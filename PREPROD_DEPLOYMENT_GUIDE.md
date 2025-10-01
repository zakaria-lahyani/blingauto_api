# BlingAuto API - Guide de Déploiement Pre-Production

**Configuration Complète avec Nginx, PostgreSQL, Redis et SSL**

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Prérequis](#prérequis)
4. [Installation Rapide](#installation-rapide)
5. [Configuration](#configuration)
6. [Déploiement](#déploiement)
7. [SSL avec Let's Encrypt](#ssl-avec-lets-encrypt)
8. [Gestion](#gestion)
9. [Surveillance](#surveillance)
10. [Dépannage](#dépannage)

---

## Vue d'ensemble

Ce guide couvre le déploiement complet de BlingAuto API en environnement de pre-production avec:

✅ **Nginx** - Reverse proxy avec rate limiting et HTTPS
✅ **PostgreSQL 16** - Base de données production-ready
✅ **Redis 7** - Cache et sessions
✅ **Let's Encrypt** - Certificats SSL gratuits et automatiques
✅ **Docker Compose** - Orchestration complète
✅ **Scripts de déploiement** - Automatisation et rollback

---

## Architecture

```
                    Internet
                       │
                       ▼
              ┌────────────────┐
              │  Nginx :80/443 │  ← SSL/TLS, Rate Limiting
              │  (Reverse Proxy)│
              └────────┬───────┘
                       │
              Docker Network
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │PostgreSQL│  │   API    │  │  Redis   │
   │  :5432   │  │  :8000   │  │  :6379   │
   └──────────┘  └──────────┘  └──────────┘
         │             │             │
         ▼             ▼             ▼
    [Volume]      [Logs]       [Volume]
   postgres_data              redis_data
```

### Composants

| Service | Description | Port | Volume |
|---------|-------------|------|--------|
| **nginx** | Reverse proxy + SSL | 80, 443 | nginx_logs |
| **api** | FastAPI application | 8000 | logs/ |
| **postgres** | Base de données | 5432 | postgres_preprod_data |
| **redis** | Cache et sessions | 6379 | redis_preprod_data |
| **certbot** | Gestion SSL | - | certbot/conf |

---

## Prérequis

### Logiciels Requis

- **Serveur Linux**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Nom de domaine**: Pointant vers votre serveur (pour SSL)

### Configuration Serveur

**Minimum**:
- 2 vCPU
- 4 GB RAM
- 40 GB SSD
- Ports 80, 443 ouverts

**Recommandé**:
- 4 vCPU
- 8 GB RAM
- 80 GB SSD
- Backup automatique

### Vérification

```bash
# Docker
docker --version
# Docker version 24.0.0+

# Docker Compose
docker-compose --version
# Docker Compose version v2.20.0+

# Ports disponibles
sudo netstat -tulpn | grep -E ':(80|443) '
# Devrait être vide si disponible
```

---

## Installation Rapide

### 1. Cloner le Projet

```bash
# SSH dans votre serveur
ssh user@votre-serveur.com

# Cloner le repository
git clone https://github.com/yourusername/blingauto-api.git
cd blingauto-api
```

### 2. Configurer l'Environnement

```bash
# Copier le fichier d'environnement pre-production
cp .env.preprod .env.preprod.local

# Éditer avec vos valeurs
nano .env.preprod.local
```

**⚠️ IMPORTANT**: Modifier ces valeurs obligatoirement:

```bash
# Génrer la clé secrète
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Dans .env.preprod.local:
SECRET_KEY=<votre-clé-générée>
POSTGRES_PASSWORD=<mot-de-passe-sécurisé-20-chars>
REDIS_PASSWORD=<mot-de-passe-sécurisé-20-chars>
INITIAL_ADMIN_EMAIL=admin@votre-domaine.com
INITIAL_ADMIN_PASSWORD=<mot-de-passe-admin-12-chars>
```

### 3. Déployer (Sans SSL d'abord)

```bash
# Utiliser le script de déploiement
chmod +x scripts/deploy-preprod.sh
./scripts/deploy-preprod.sh
```

Le script va:
1. ✅ Vérifier les prérequis
2. ✅ Sauvegarder la base de données
3. ✅ Construire les images Docker
4. ✅ Démarrer tous les services
5. ✅ Vérifier la santé de l'API
6. ✅ Afficher les endpoints disponibles

### 4. Vérifier le Déploiement

```bash
# Tester l'API (HTTP seulement pour l'instant)
curl http://localhost/health

# Accéder à la documentation
# Ouvrir dans un navigateur:
http://votre-serveur/docs
```

---

## Configuration

### Fichiers de Configuration

#### .env.preprod.local

```bash
# =============================================================================
# Configuration Pre-Production
# =============================================================================

# Application
ENVIRONMENT=staging
APP_NAME=BlingAuto API - Pre-Production

# Base de données
POSTGRES_DB=blingauto_preprod
POSTGRES_USER=blingauto_preprod
POSTGRES_PASSWORD=VotreMotDePasseSecurise2024!

# Redis
REDIS_PASSWORD=VotreRedisPasswordSecurise2024!

# Security
SECRET_KEY=<généré-avec-python-secrets>

# Admin initial
INITIAL_ADMIN_EMAIL=admin@preprod.blingauto.com
INITIAL_ADMIN_PASSWORD=AdminSecurePass2024!

# Frontend URL (à adapter)
FRONTEND_URL=https://preprod.blingauto.com
CORS_ORIGINS=https://preprod.blingauto.com
```

#### docker-compose.preprod.yml

Le fichier `docker-compose.preprod.yml` est préconfigur avec:
- Nginx reverse proxy
- PostgreSQL 16
- Redis 7
- API avec 4 workers
- Volumes persistants
- Health checks
- Networks isolés

**Pas besoin de modification** sauf cas particuliers.

---

## Déploiement

### Déploiement Initial

```bash
# Option 1: Script automatique (recommandé)
./scripts/deploy-preprod.sh

# Option 2: Manuel
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local up -d
```

### Mise à Jour

```bash
# Avec le script (inclut backup automatique)
./scripts/deploy-preprod.sh

# Ou manuel
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local down
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local pull
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local build
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local up -d
```

### Commandes Utiles

```bash
# Démarrer
./scripts/deploy-preprod.sh start

# Arrêter
./scripts/deploy-preprod.sh stop

# Redémarrer
./scripts/deploy-preprod.sh restart

# Voir l'état
./scripts/deploy-preprod.sh status

# Voir les logs
./scripts/deploy-preprod.sh logs

# Health check
./scripts/deploy-preprod.sh health

# Backup manuel
./scripts/deploy-preprod.sh backup

# Rollback
./scripts/deploy-preprod.sh rollback
```

---

## SSL avec Let's Encrypt

### Prérequis SSL

1. **Nom de domaine** configuré et pointant vers votre serveur
2. **Ports 80 et 443** ouverts dans le firewall
3. **DNS propagé** (vérifier avec `nslookup votre-domaine.com`)

### Installation SSL

#### Étape 1: Préparer le Domaine

```bash
# Vérifier que le domaine pointe vers votre serveur
nslookup preprod.blingauto.com

# Devrait retourner l'IP de votre serveur
```

#### Étape 2: Obtenir le Certificat

```bash
# Utiliser le script automatique
chmod +x scripts/setup-letsencrypt.sh

# Pour production (certificat réel)
./scripts/setup-letsencrypt.sh preprod.blingauto.com admin@blingauto.com

# Pour test (certificat staging - recommandé d'abord)
./scripts/setup-letsencrypt.sh preprod.blingauto.com admin@blingauto.com 1
```

#### Étape 3: Déployer avec Let's Encrypt

```bash
# Utiliser le docker-compose avec Let's Encrypt
docker-compose -f docker-compose.preprod-letsencrypt.yml --env-file .env.preprod.local up -d
```

### Renouvellement Automatique

Les certificats Let's Encrypt expirent après 90 jours. Le renouvellement est **automatique** via le service Certbot.

**Vérification manuelle**:
```bash
# Tester le renouvellement (dry-run)
docker-compose -f docker-compose.preprod-letsencrypt.yml run --rm certbot renew --dry-run

# Forcer le renouvellement
docker-compose -f docker-compose.preprod-letsencrypt.yml run --rm certbot renew --force-renewal
```

---

## Gestion

### Logs

```bash
# Tous les services
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local logs -f

# API uniquement
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local logs -f api

# Nginx
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local logs -f nginx

# PostgreSQL
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local logs -f postgres

# Les 100 dernières lignes
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local logs --tail=100
```

### Base de Données

```bash
# Accéder à PostgreSQL
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec postgres psql -U blingauto_preprod -d blingauto_preprod

# Créer un backup
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec -T postgres pg_dump -U blingauto_preprod blingauto_preprod > backup_$(date +%Y%m%d).sql

# Restaurer un backup
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec -T postgres psql -U blingauto_preprod blingauto_preprod < backup_20250101.sql

# Voir les tables
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec postgres psql -U blingauto_preprod -d blingauto_preprod -c "\dt"
```

### Redis

```bash
# Accéder à Redis CLI
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec redis redis-cli -a <REDIS_PASSWORD>

# Vérifier les clés
redis-cli> KEYS *

# Voir info
redis-cli> INFO

# Vider le cache
redis-cli> FLUSHALL
```

### Migrations

```bash
# Voir l'état des migrations
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec api alembic current

# Historique
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec api alembic history

# Appliquer les migrations
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec api alembic upgrade head

# Rollback d'une migration
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec api alembic downgrade -1
```

---

## Surveillance

### Health Check

```bash
# Via curl
curl https://preprod.blingauto.com/health

# Réponse attendue
{
  "status": "healthy",
  "timestamp": "2025-10-01T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "system": {"status": "healthy", "cpu_percent": 15.2}
  }
}
```

### Métriques Docker

```bash
# Utilisation des ressources en temps réel
docker stats

# État des conteneurs
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local ps

# Inspect un service
docker inspect blingauto-api-preprod
```

### Logs Nginx

```bash
# Access logs
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec nginx tail -f /var/log/nginx/access.log

# Error logs
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec nginx tail -f /var/log/nginx/error.log
```

---

## Dépannage

### Problème: Services ne démarrent pas

```bash
# Vérifier les logs
./scripts/deploy-preprod.sh logs

# Vérifier l'état
./scripts/deploy-preprod.sh status

# Problème courant: ports déjà utilisés
sudo netstat -tulpn | grep -E ':(80|443|5432|6379) '

# Solution: arrêter les services conflictuels
sudo systemctl stop apache2  # Si Apache est installé
sudo systemctl stop nginx    # Si Nginx système est installé
```

### Problème: Base de données ne se connecte pas

```bash
# Vérifier PostgreSQL
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec postgres pg_isready

# Vérifier les logs PostgreSQL
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local logs postgres

# Recréer le volume (⚠️ PERTE DE DONNÉES)
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local down -v
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local up -d
```

### Problème: SSL ne fonctionne pas

```bash
# Vérifier que le domaine pointe vers le serveur
nslookup preprod.blingauto.com

# Vérifier les ports ouverts
sudo ufw status
# Ou
sudo iptables -L -n

# Ouvrir les ports si nécessaire
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Vérifier les certificats
docker-compose -f docker-compose.preprod-letsencrypt.yml run --rm certbot certificates

# Re-générer les certificats
./scripts/setup-letsencrypt.sh preprod.blingauto.com admin@blingauto.com
```

### Problème: API retourne 502 Bad Gateway

```bash
# L'API ne répond pas, vérifier ses logs
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local logs api

# Redémarrer l'API
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local restart api

# Vérifier la connexion Nginx → API
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec nginx wget -O- http://api:8000/health
```

### Problème: Erreur de migration

```bash
# Voir l'état actuel
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec api alembic current

# Rollback
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec api alembic downgrade -1

# Réappliquer
docker-compose -f docker-compose.preprod.yml --env-file .env.preprod.local exec api alembic upgrade head
```

---

## Tests de Validation

### Checklist de Déploiement

- [ ] Services démarrés: `docker-compose ps`
- [ ] Health check OK: `curl https://preprod.blingauto.com/health`
- [ ] Documentation accessible: `https://preprod.blingauto.com/docs`
- [ ] SSL valide: Cadenas vert dans le navigateur
- [ ] Admin créé: Se connecter via `/docs`
- [ ] Base de données persistante: Redémarrer et vérifier les données
- [ ] Logs accessibles: `docker-compose logs`
- [ ] Backup fonctionne: `./scripts/deploy-preprod.sh backup`

### Tests API

```bash
# Health check
curl https://preprod.blingauto.com/health

# Documentation
curl https://preprod.blingauto.com/openapi.json

# Login admin
curl -X POST https://preprod.blingauto.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@preprod.blingauto.com","password":"votre-password"}'

# Créer un wash bay (avec token)
curl -X POST https://preprod.blingauto.com/api/v1/facilities/wash-bays \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"bay_number":"BAY-001","max_vehicle_size":"LARGE"}'
```

---

## Sécurité

### Checklist Sécurité

- [x] Mot de passe PostgreSQL fort (20+ caractères)
- [x] Mot de passe Redis fort (20+ caractères)
- [x] SECRET_KEY généré aléatoirement (64 caractères)
- [x] Mot de passe admin fort (12+ caractères)
- [x] SSL activé avec certificats valides
- [x] Rate limiting configuré (Nginx)
- [x] CORS limité aux domaines autorisés
- [x] Firewall configuré (ports 80, 443 uniquement)
- [x] Backups automatiques
- [ ] Monitoring externe configuré
- [ ] Alertes configurées

### Hardening Supplémentaire

```bash
# Désactiver les ports de debug
# Dans docker-compose.preprod.yml, commenter:
# ports:
#   - "5432:5432"  # PostgreSQL
#   - "6379:6379"  # Redis

# Configurer le firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Maintenance

### Backups Automatiques

Créer un cron job pour backups quotidiens:

```bash
# Éditer crontab
crontab -e

# Ajouter (backup chaque jour à 2h du matin)
0 2 * * * /path/to/blingauto-api/scripts/deploy-preprod.sh backup

# Nettoyer les vieux backups (garder 7 derniers jours)
0 3 * * * find /path/to/blingauto-api/backups -name "*.sql.gz" -mtime +7 -delete
```

### Mises à Jour

```bash
# 1. Backup
./scripts/deploy-preprod.sh backup

# 2. Pull derniers changements
git pull origin main

# 3. Redéployer
./scripts/deploy-preprod.sh

# 4. Vérifier
./scripts/deploy-preprod.sh health
```

---

## Support

**Documentation**:
- API: https://preprod.blingauto.com/docs
- GitHub: https://github.com/yourusername/blingauto-api
- Issues: https://github.com/yourusername/blingauto-api/issues

**Contact**:
- Email: support@blingauto.com
- Slack: #blingauto-support

---

**Version**: 1.0.0
**Date**: 2025-10-01
**Environnement**: Pre-Production
