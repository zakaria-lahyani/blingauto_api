# BlingAuto API - Guide de Démarrage Rapide

🚀 **Lancez l'application en 3 minutes**

---

## Option 1: Démarrage Simple (Recommandé)

### 1. Vérifier les prérequis

```powershell
# Vérifier Docker
docker --version
docker-compose --version
```

### 2. Démarrer l'application

```powershell
# Dans le dossier du projet
cd C:\Users\zak\Desktop\workspace\project\lavage\api\blingauto_api

# Démarrer tous les services
docker-compose up -d --build

# Attendre 30 secondes que les services démarrent
timeout /t 30

# Voir l'état
docker-compose ps
```

### 3. Tester l'API

```powershell
# Health check
curl http://localhost:8000/health

# Ouvrir la documentation
start http://localhost:8000/docs
```

### 4. Se connecter en tant qu'Admin

**Credentials** (depuis `.env`):
- Email: `admin@blingauto.local`
- Password: `AdminDev123!`

**Via Swagger**:
1. Aller sur http://localhost:8000/docs
2. Cliquer sur "Authorize" (cadenas en haut à droite)
3. Entrer les credentials
4. Tester les endpoints

---

## Option 2: Démarrage avec Pre-Production (Nginx + SSL)

### 1. Configurer l'environnement

```powershell
# Copier le fichier de configuration
copy .env.preprod .env.preprod.local

# Éditer avec vos valeurs
notepad .env.preprod.local
```

### 2. Démarrer avec Nginx

```powershell
# Démarrage automatique avec le script
bash scripts/deploy-preprod.sh

# Ou manuel
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local up -d --build
```

### 3. Accéder

- **HTTP**: http://localhost
- **HTTPS**: https://localhost (certificat self-signed)
- **Docs**: https://localhost/docs

---

## Commandes Utiles

### Gestion des Services

```powershell
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Voir les logs
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f api

# Redémarrer
docker-compose restart

# État des services
docker-compose ps
```

### Base de Données

```powershell
# Accéder à PostgreSQL
docker-compose exec postgres psql -U blingauto_user -d blingauto

# Voir les tables
docker-compose exec postgres psql -U blingauto_user -d blingauto -c "\dt"

# Backup
docker-compose exec postgres pg_dump -U blingauto_user blingauto > backup.sql

# Migrations
docker-compose exec api alembic upgrade head
```

### Redis

```powershell
# Accéder à Redis
docker-compose exec redis redis-cli -a DevRedisPassword123!

# Voir les clés
redis-cli> KEYS *

# Vider le cache
redis-cli> FLUSHALL
```

---

## Dépannage

### Problème: Port déjà utilisé

```powershell
# Vérifier quel processus utilise le port 8000
netstat -ano | findstr :8000

# Arrêter le processus (remplacer PID)
taskkill /PID 12345 /F

# Ou changer le port
# Dans .env: API_PORT=8001
docker-compose up -d
```

### Problème: Erreur de build

```powershell
# Nettoyer et reconstruire
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Problème: Base de données ne démarre pas

```powershell
# Voir les logs
docker-compose logs postgres

# Recréer le volume (⚠️ PERTE DE DONNÉES)
docker-compose down -v
docker volume rm blingauto-postgres-data
docker-compose up -d
```

### Problème: API ne démarre pas

```powershell
# Voir les logs
docker-compose logs api

# Vérifier les variables d'environnement
docker-compose exec api env | findstr DATABASE_URL

# Redémarrer l'API
docker-compose restart api
```

---

## Endpoints Disponibles

Après démarrage, ces endpoints sont accessibles:

| Endpoint | Description |
|----------|-------------|
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/docs` | Documentation Swagger UI |
| `http://localhost:8000/redoc` | Documentation ReDoc |
| `http://localhost:8000/openapi.json` | Spécification OpenAPI |
| `http://localhost:8000/api/v1/auth/login` | Login |
| `http://localhost:8000/api/v1/facilities/wash-bays` | Wash bays CRUD |
| `http://localhost:8000/api/v1/facilities/mobile-teams` | Mobile teams CRUD |

---

## Test Complet

### 1. Health Check

```powershell
curl http://localhost:8000/health
```

**Réponse attendue**:
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"}
  }
}
```

### 2. Login Admin

```powershell
curl -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"admin@blingauto.local\",\"password\":\"AdminDev123!\"}"
```

**Réponse**: Token JWT

### 3. Créer un Wash Bay

```powershell
# Remplacer <TOKEN> par le token obtenu
curl -X POST http://localhost:8000/api/v1/facilities/wash-bays `
  -H "Authorization: Bearer <TOKEN>" `
  -H "Content-Type: application/json" `
  -d "{\"bay_number\":\"BAY-001\",\"max_vehicle_size\":\"LARGE\"}"
```

---

## Arrêt de l'Application

```powershell
# Arrêter les services (garde les données)
docker-compose down

# Arrêter et supprimer les volumes (⚠️ PERTE DE DONNÉES)
docker-compose down -v
```

---

## Next Steps

1. ✅ **Tester l'API** via Swagger UI
2. ✅ **Créer des wash bays** et mobile teams
3. ✅ **Tester les endpoints** d'authentification
4. 📖 Lire [DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md) pour plus de détails
5. 🚀 Déployer en pre-production avec [PREPROD_DEPLOYMENT_GUIDE.md](./PREPROD_DEPLOYMENT_GUIDE.md)

---

**Questions?** Consultez les guides complets:
- [DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md) - Docker setup complet
- [PREPROD_DEPLOYMENT_GUIDE.md](./PREPROD_DEPLOYMENT_GUIDE.md) - Pre-production avec Nginx
- [ADMIN_USER_GUIDE.md](./ADMIN_USER_GUIDE.md) - Gestion utilisateur admin

**Version**: 1.0.0
**Last Updated**: 2025-10-01
