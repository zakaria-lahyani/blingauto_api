Vue d’ensemble (principes)

Séparation stricte par feature : chaque feature a domain (règles), ports (contrats), use_cases (application), adapters (implémentations techniques), api (I/O HTTP).

Dépendances dirigées : api → use_cases → domain ; adapters implémentent ports. Jamais l’inverse.

Infra commune légère dans core/ (DB/Redis/logs/middlewares/config) — pas de logique métier ici.

Aucune import “traversant” entre features : si une feature A a besoin de B, elle passe par un port exposé par A et un adapter local côté A qui appelle le use case de B (appel direct en mémoire, mais via contrat).

Tests à tous les niveaux : unit (domain), intégration (adapters), API (e2e).

NGINX en frontal (reverse proxy + headers + rate-limit), FastAPI en unique app.

Arborescence du dépôt (proposée)
repo/
  app/
    core/                          # Transversal (pas de business)
      config/                      # lecture env, profils (dev/stage/prod)
      db/                          # SQLAlchemy: engine, session, UoW
      cache/                       # Redis client, wrappers (rate-limit, locks)
      security/                    # JWT, password hashing, RBAC helpers
      middleware/                  # request_id, logging, cors, timeout, rate_limit
      observability/               # tracing, metrics, health/readiness
      errors/                      # exceptions communes + mapping HTTP
    features/
      auth/
        domain/                    # entités, value objects, policies RIGOUREUSES
        ports/                     # IUserRepo, ITokenService, etc. (interfaces)
        use_cases/                 # RegisterUser, Login, Refresh, etc.
        adapters/                  # repo SQLA, token JWT, cache Redis...
        api/                       # router FastAPI, schémas Pydantic, deps RBAC
        tests/                     # unit (domain), intégration (repo), api (e2e)
      bookings/
        domain/                    # agrégat Booking + machine d'états + policies
        ports/                     # IBookingRepo, PricingPort, SchedulingPort, Clock
        use_cases/                 # Create, Confirm, Start, Complete, Cancel, Rate...
        adapters/                  # repo SQLA, pricing_local, scheduling_local, locks
        api/                       # endpoints /api/bookings/*
        tests/
      pricing/
        domain/                    # catalogue, règles de tarification
        ports/                     # ICatalogueRepo
        use_cases/                 # Quote
        adapters/                  # repo SQLA
        api/                       # /api/pricing/*
        tests/
      vehicles/
        domain/                    # véhicule, invariants (plaque, année, défaut)
        ports/                     # IVehicleRepo
        use_cases/                 # CRUD, set_default
        adapters/                  # repo SQLA
        api/
        tests/
      scheduling/
        domain/                    # ressources, horaires, buffers, compatibilités
        ports/                     # CapacityRepo, CalendarSvc, DistanceSvc
        use_cases/                 # CheckAvailability, SuggestSlots
        adapters/
        api/
        tests/
    interfaces/
      http_api.py                  # création de l’app FastAPI + montage des routers
      health.py                    # /health & /ready
      openapi.py                   # titre, tags, docs publiques (exemples)
    migrations/                    # Alembic (schéma unique ou sous-dossiers par feature)
    main.py                        # point d’entrée (charge core + interfaces)
  deploy/
    docker/
      nginx/
        Dockerfile
        nginx.conf
        conf.d/
          app.conf                 # reverse proxy vers app:8000 + headers + RL
      postgres/
        init/                      # scripts init optionnels (dev)
      docker-compose.yml
    .env.example                   # variables d’environnement (sans secrets)
  tests/
    conftest.py                    # fixtures partagées (client HTTP, DB test, etc.)
    e2e/                           # scénarios bout-en-bout cross-features
  docs/
    ADRs/                          # décisions d’architecture (courtes)
    api/                           # spec OpenAPI exportée, exemples
    rules/                         # synthèse règles de gestion par feature
  Makefile                         # raccourcis DX (run, test, lint, fmt, migrate)
  pyproject.toml                   # dépendances & outils qualité
  README.md                        # guide dev court (5 min)

Rôle de chaque dossier (en une phrase)

core/ : outils techniques communs (DB, Redis, logging, middlewares, config, observabilité). Jamais de règle métier.

features/*/domain/ : la vérité métier (entités, invariants, policies, transitions d’état). Zéro dépendance framework.

features/*/ports/ : contrats (interfaces) pour dépendances externes à la feature (repos, services voisins, horloge…).

features/*/use_cases/ : application des règles métier à une intention utilisateur (une fonction, un effet).

features/*/adapters/ : implémentations concrètes des ports (SQLAlchemy, Redis, “appel local” d’un use case d’une autre feature).

features/*/api/ : endpoints FastAPI + schémas Pydantic + guards RBAC. Ne contenant aucune règle métier.

interfaces/ : composition de l’app (montage des routers, health, openapi).

migrations/ : migrations DB (Alembic).

deploy/ : NGINX, Postgres dev, docker compose.

docs/ : règles, décisions, API docs.

tests/ : niveaux globaux (e2e) + tests spécifiques dans chaque feature.

Règles de dépendances (à respecter strictement)

domain ne dépend que de Python standard.

use_cases dépend de domain et ports (jamais d’adapter).

adapters dépend de ports et core (DB/Redis), jamais l’inverse.

api dépend de use_cases et schemas; ne touche pas domain directement.

features ne s’importent jamais entre elles directement : elles communiquent via ports.

interfaces assemble le tout, c’est le seul endroit qui “voit” toutes les features.

Astuce : un outil (ruff/mypy) peut interdire certaines import-cycles pour faire respecter ces règles.

Flux type (pour vérifier l’isolation)

Requête → api valide I/O + RBAC → appelle un use case.

Le use case applique règles de domain + utilise des ports (repos, services) injectés.

Les adapters branchés (SQLA, “local call” d’une autre feature, Redis lock) exécutent le concret.

Retour formaté via schémas api.

Aucune règle dans api/adapters; toutes les règles dans domain/use_cases.

DB & migrations (simples et propres)

Un seul schéma au départ, organisé par tables alignées aux features.

Index/contraintes au plus près des règles (unicités, checks).

Migrations par lot logique (par feature) avec messages explicites.

Unit of Work (dans core/db) : chaque use case ouvre/commit une transaction.

Conventions (pour rester lisible)

Nommer les use cases comme des intentions: CreateBooking, ConfirmBooking, QuotePricing.

Policies explicites dans domain/policies.py (annulation, barèmes, états).

Ports en ports/*.py avec signatures claires et docstring (entrées/sorties).

Adapters suffixés par technologie: repo_sqlalchemy.py, cache_redis.py, pricing_local.py.

Endpoints REST stables : /api/<feature> + actions explicites (/{id}:confirm).

Erreurs standardisées via core/errors (code, message, request_id).

NGINX (où, comment)

deploy/docker/nginx/ : config générique (“app.conf”)

Reverse proxy → app:8000

Headers sécurité (X-Frame-Options, X-Content-Type-Options, Referrer-Policy)

Rate-limit L7 simple (par IP)

/health & /ready routés vers l’app

Tests (où les écrire)

features/*/tests/unit/ : policies, transitions, règles de domaine (sans DB).

features/*/tests/integration/ : adapters (SQLA/Redis) avec DB éphémère.

features/*/tests/api/ : routes de la feature (TestClient).

tests/e2e/ : scénarios transverses (ex. créer un booking → confirmer → compléter).

Couverture minimale : transitions d’état, barèmes, contraintes d’entrée.

Qualité & CI (à poser dès le début)

Ruff/Black/Mypy configurés au repo.

Pre-commit pour formatter/linter avant chaque commit.

CI : lint + tests unit + tests intégration + tests API.

Artifacts : export OpenAPI (docs/) à chaque build.

Organisation du travail

Feature-first : une PR = une feature ou une règle de gestion cohérente.

ADRs (1 page) pour décisions structurantes (ex. format des états Booking).

Changelog simple (Keep a Changelog), versions internes sémantiques.

Checklist d’initialisation (sans code)

Créer le squelette de dossiers ci-dessus.

Écrire un README de 10 lignes expliquant le flux et les règles de dépendances.

Lister dans docs/rules/ vos règles de gestion par feature (copie condensée).

Définir dans docs/api/ la carte des endpoints (même sommaire).

Poser la config NGINX de base dans deploy/.

Installer les outils qualité (ruff/black/mypy, pre-commit) et le pipeline CI minimal.

Si tu veux, je te fais une checklist personnalisée par feature à partir de tes règles de gestion (ex. états Booking, barèmes d’annulation, validations véhicule) pour que chaque dossier domain/policies.py soit cadré dès J0.