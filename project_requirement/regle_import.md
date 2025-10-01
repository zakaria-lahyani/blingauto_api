1) Couches et sens des dépendances

domain (entités, règles, policies) : cœur ultra-stable.

ports (contrats) : interfaces possédées par la feature qui a le besoin.

use_cases (application) : orchestre le domaine via les ports.

adapters (technique) : implémentent les ports (DB, cache, “appel local” d’une autre feature).

api (I/O) : sérialise/désérialise, RBAC, aucune règle métier.

core (infra partagée) : DB/Redis/logs/middlewares/erreurs/observabilité, pas de métier.

interfaces (composition) : crée l’app, monte les routers, health/openapi.

Flèche de dépendance autorisée (unique sens)
api → use_cases → domain
adapters → ports → (use_cases/domain)
use_cases → ports
features → jamais import direct d’une autre feature (voir §3)

2) Matrice d’imports (autorisé / interdit)

api peut importer : use_cases de sa feature, schemas de sa feature, core (middlewares/erreurs).

use_cases peut importer : domain + ports de sa feature, core (UoW/horloge abstraite).

domain peut importer : rien de framework, éventuellement typing/utils purs.

ports peut importer : types du domain de sa feature.

adapters peut importer : ports de sa feature, core (DB/Redis), et facultativement un use case public d’une autre feature via un adapter local (voir §3).

core n’importe jamais une feature.

interfaces importe tout pour assembler, mais ne contient aucune règle métier.

3) Interaction entre features (A ↔ B)

Principe d’or : pas d’import direct interne “A.domain” → “B.domain”.
Deux modes :

Synchrones (dans le même process)

A expose un use case public (ex. Pricing.Quote).

B définit un port (ex. PricingPort).

B fournit un adapter local qui appelle ce use case public de A.

Ainsi B dépend d’un contrat (son port), pas des entrailles de A.

A ne sait rien de B (dépendance unidirectionnelle).

Asynchrones (événements in-process)

Une feature publie des événements de domaine (ex. booking.confirmed).

Les autres s’abonnent via un bus interne expliqué dans core (pub/sub mémoire).

Pas d’appel croisé ; propagation des effets sans couplage dur.

Conséquence : ownership des données reste local à chaque feature. Accès lecture inter-feature via use case public (sync) ou vue matérialisée côté consommateur (async), jamais via table étrangère “piratée”.

4) Qui possède quoi (ownership)

La feature qui porte la règle possède le schéma, ses entités, ses ports.

Les contrats (ports) vivent dans la feature consommatrice (celle qui a besoin).

Les adapters vivent dans la feature consommatrice (elle choisit comment satisfaire son besoin).

Les use cases publics (appelables par d’autres) sont clairement documentés dans docs/api (même en interne).

5) Transactions, erreurs, temps

Transaction : démarre dans le use case initiateur (une feature). Les appels sync vers d’autres use cases ne doivent pas partager la même transaction DB (éviter les effets domino). On préfère séparer : calcul (pur) sync, persistance locale ; puis éventuel événement.

Erreurs : chaque feature lève ses erreurs métier ; mapping HTTP se fait en api de la feature appelante. Jamais de propagation d’exceptions techniques brutes entre features.

Temps : aucune now() directe en domain ; passe par un Clock (port) fourni par la feature appelante (testable).

6) Lecture/écriture entre packages

Lecture inter-feature : soit use case public de la feature source (sync), soit cache local/DTO injecté par événement (async).

Écriture inter-feature : interdite. Une feature ne modifie jamais les tables d’une autre. Elle émet un command/event pour que la feature propriétaire agisse si nécessaire.

7) Ports : règles de conception

Nommer côté consommateur (ex. PricingPort dans bookings), centré besoin (“obtenir un devis”), pas technologie.

Paramètres/retours stables (DTO simples, types du domaine consommateur).

Pas d’“interface fourre-tout” ; un port = une responsabilité claire.

Documenter : pré/post-conditions, erreurs fonctionnelles attendues.

8) Adapters : règles d’implémentation

Un adapter par techno : repo_sqlalchemy, cache_redis, pricing_local.

Jamais de règle métier ; seulement mapping, requêtes, orchestration technique.

Les adapters inter-feature n’accèdent qu’aux use cases publics de l’autre feature (pas de modèles internes).

9) API : frontières nettes

Ne touche qu’aux use cases et schemas de sa propre feature.

RBAC & validation I/O uniquement.

Pas de “business if/else” ici ; redirige vers un use case.

10) Core : neutre et réutilisable

Fournit : UoW/DB, clients Redis, logging, middlewares, erreurs, observabilité.

Ne connaît aucune feature.

Composition root (interfaces) branche les dépendances (quel adapter pour quel port).

11) Éviter les cycles et le couplage

Pas de from features.X import Y hors use case public via adapter.

Si A appelle B et B a besoin d’A, rompre le cycle via événements (async) ou redessiner le besoin (peut-être qu’un 3ᵉ port “catalogue” commun dans A évite l’aller-retour).

Stable Dependencies Principle : les couches stables (domain) ne dépendent pas de couches volatiles (api/adapters).

12) Tests d’architecture (automatiser les règles)

Import-linter (ou équivalent) :

Interdire features.X.domain d’importer autre chose que standard typing.

Interdire imports inter-features sauf via “couloirs” autorisés (adapters → use case public).

Forcer le sens api→use_cases→domain.

Ruff/isort : ordonner et contrôler les imports.

Mypy : figer les signatures des ports (contrats robustes).

13) Nommage & visibilité

Dossiers clairs : domain, ports, use_cases, adapters, api.

Public/privé : documenter explicitement les use cases publics accessibles inter-feature (liste courte). Le reste est interne.

14) Évolution et compatibilité

Tout changement de use case public est versionné dans la doc (breaking vs compatible).

Les ports sont côté consommateur : la feature peut changer d’implémentation (adapter) sans prévenir les autres.

Ajouter > Supprimer. On évite de renommer/retourner les paramètres sans phase de dépréciation.

15) Anti-patterns (à bannir)

“Petit import rapide” de models d’une autre feature.

Logique métier en adapter ou en api.

Appels croisés en chaîne (A→B→C) au sein d’une même transaction DB.

Requêtes SQL cross-feature sur les tables d’autrui.

Ports “universels” avec 15 méthodes.