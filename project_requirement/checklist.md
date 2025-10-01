## Core (infrastructure commune)
- Définir variables d’env (DB_URL, REDIS_URL, JWT_SECRET, RATE_LIMITS).
- Écrire règles de dépendances (api→use_cases→domain ; adapters implémentent ports).
- Middlewares à activer : request-id, logging JSON, CORS, timeout, rate-limit.
- Observabilité : endpoints /health & /ready, métriques (latence, erreurs), tracing.
- Format d’erreur standard (code interne, message, request_id).

## Auth
- Rôles & scopes : Admin, Manager, Washer, Client (+ héritage clair).
- Invariants utilisateur : email unique/valide, mot de passe (longueur/complexité), statut actif.
- Tokens : durée access (15 min), refresh (7 j), rotation + révocation.
- Sécurité : lockout progressif (ex. 5 échecs), reset password (1h), verify email (24h).
- Ports : IUserRepo, ITokenService.
- Endpoints : register, login, refresh, logout(all), verify, reset(request/confirm), GET /me.
- RBAC : dépendances par scope côté API (moindre privilège).

## Vehicles
- Invariants : marque/modèle/couleur (tailles max), année 1900..(année+2), plaque unique par user (soft delete friendly), “par défaut” unique.
- Règle : interdiction de supprimer si réservation active.
- Ports : IVehicleRepo.
- Endpoints : list/create/update/delete(soft)/set-default.
- Index/contraintes : unique (user_id, plate) où deleted_at NULL ; check année.

## Services & Catégories
- Catégories : nom unique, statut ACTIVE/INACTIVE, non supprimable si services rattachés.
- Services : nom unique par catégorie, durée>0, prix>0, flag “popular”.
- Ports : ICategoryRepo, IServiceRepo.
- Endpoints : CRUD + toggle-status ; interdiction suppression catégorie si enfants.
- Indices : categories(name UNIQUE), composite (category_id, name).

## Pricing
- Règles : somme des services (Decimal), arrondi, remises futures (prévu mais pas activé).
- Port : ICatalogueRepo (lecture prix/durée).
- Use case : Quote (entrée items, sortie total/durée).
- Endpoint : POST /api/pricing/quote (si tu veux exposer publiquement, sinon interne).
- Index : services consultés souvent (cache lecture optionnel via Redis).

## Bookings
- États autorisés : PENDING → CONFIRMED → IN_PROGRESS → COMPLETED; sorties : CANCELLED, NO_SHOW.
- Création : 1..10 services, pas de doublon, durée totale 30–240 min, ≤90 jours, pas dans le passé, véhicule taille ∈ {compact, standard, large, oversized}, si mobile ⇒ GPS requis.
- Annulation (barème) : >24h=0%, 6–24h=25%, 2–6h=50%, <2h=100%. No-show après 30 min.
- Replanification : préavis ≥2h ; seulement PENDING/CONFIRMED.
- Modifs services : add/remove uniquement en PENDING.
- Overtime : facturation au-delà du temps planifié (p.ex. 1€/min).
- Évaluation : 1–5, texte ≤1000 chars, disponible seulement en COMPLETED, unique par booking.
- Ports : IBookingRepo, PricingPort, SchedulingPort, Clock, LockPort (anti-collision).
- Endpoints : create, confirm, start, complete, cancel, reschedule, add-service, remove-service, rate, list/detail.
- Index : (scheduled_at, status), table booking_items, table d’events (audit).

## Scheduling
- Ressources “facility” : baies (capacité 1), compatibilité tailles, statut actif.- 
- Ressources “mobile” : rayon (km), base GPS, capacité/jour.- 
- Horaires : par jour/semaine, fermetures/blackouts, tampon 15 min entre prestations.- 
- Règles : anticipation min 2h ; max 90 jours ; auto-libération du slot à l’annulation.- 
- Ports : CapacityRepo, CalendarService, DistanceService, SuggestionService.- 
- Endpoints : check-availability, suggest-slots (retourne alternatives si créneau indisponible).- 
- Données : éventuelle table slots matérialisée (optionnel) + index sur périodes.

## API (assemblage)

- Carte des routes par feature (/api/auth, /api/vehicles, /api/services, /api/pricing, /api/bookings, /api/scheduling).- 
- Schémas d’entrée/sortie (Pydantic) stricts ; toutes les dates en UTC, TZ-aware.- 
- Guards : RBAC par scope ; validations d’accès “propriétaire” (client ne voit que ses bookings/vehicles).- 
- Erreurs : mappage unique (400/401/403/404/422/429/500) + request_id.

## NGINX (front minimal robuste)

- Reverse proxy → app:8000.
- Headers sécurité de base (nosniff, frame-deny, xss protection, referrer policy).
- Rate-limit L7 IP (ex. 100 req/min, burst 20).
- Routes directes /health, /ready.
- Option TLS (prod) + compression gzip statique (si tu sers un front).

## Base de données & migrations

- Un schéma unique, tables alignées aux features.
- Contraintes : uniques et checks correspondant aux invariants clés.
- Migrations par lot logique (regroupées par feature).
- Fichier “seed” minimal (catégories/services de base) pour dev.

## Redis (facultatif mais utile)

- Rate-limit backend partagé (cohérence multi-workers).
- Locks métier (ex. verrouiller un créneau à la création avant confirmation).
- Caches lecture à TTL court (catalogue pricing, listes services).

# Tests (pyramide)
## Unit (domain)

- Auth : règles MDP, lockout, tokens (durées théoriques).
- Vehicles : invariants (année, plaque unique, véhicule par défaut).
- Services/Catégories : unicités, (dé)activation, interdiction suppression si enfants.
- Bookings : transitions autorisées, barème annulation, no-show, add/remove en PENDING, overtime, rating.
- Scheduling : buffer 15 min, heures d’ouverture, capacité, alternatives.

## Intégration (adapters)

- Repos SQLAlchemy (CRUD, index, contraintes levées).
- Redis locks/rate-limit (chemins heureux + timeouts).

## API (e2e)

- Parcours complet booking (create→confirm→start→complete).
- Annulation aux différents préavis (vérifier frais).
- Replanification avec contrôle de capacité & tampon.
- RBAC : accès client vs manager vs admin (refus / autorisation).

## Rituels d’équipe (pour rester clean)

- Une PR = une intention (use case, règle) ; pas de “réécritures globales”.
- Respect strict des dépendances (aucun import cross-feature hors ports).
- “Definition of Done” inclut : règles écrites (docs/rules), tests passants, endpoints documentés.

