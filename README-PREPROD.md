# BlingAuto API - Pre-Production Setup

🚀 **Configuration complète prête à déployer avec Nginx, PostgreSQL, Redis et SSL automatique**

---

## ⚡ Démarrage Rapide

### 1. Cloner et Configurer

```bash
git clone https://github.com/yourusername/blingauto-api.git
cd blingauto-api

# Copier et configurer l'environnement
cp .env.preprod .env.preprod.local
nano .env.preprod.local

# Générer les secrets
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 2. Déployer

```bash
# Déploiement automatique
chmod +x scripts/deploy-preprod.sh
./scripts/deploy-preprod.sh
```

### 3. Tester

```bash
# Health check
curl http://localhost/health

# Documentation
open http://localhost/docs
```

### 4. Configurer SSL (Optionnel)

```bash
# Avec Let's Encrypt
chmod +x scripts/setup-letsencrypt.sh
./scripts/setup-letsencrypt.sh preprod.blingauto.com admin@blingauto.com
```

---

## 📦 Ce qui est Inclus

### Infrastructure

- ✅ **Nginx** - Reverse proxy avec SSL, rate limiting, compression
- ✅ **PostgreSQL 16** - Base de données avec volumes persistants
- ✅ **Redis 7** - Cache et sessions avec AOF persistence
- ✅ **Certbot** - SSL automatique avec Let's Encrypt
- ✅ **Health Checks** - Surveillance automatique de tous les services

### Fonctionnalités

- ✅ **Admin par Défaut** - Création automatique au premier démarrage
- ✅ **Migrations Auto** - Base de données initialisée automatiquement
- ✅ **Backups** - Scripts de sauvegarde intégrés
- ✅ **Rollback** - Restauration facile en cas de problème
- ✅ **Logs Centralisés** - Tous les logs accessibles via Docker

### Sécurité

- ✅ **HTTPS** - SSL/TLS avec certificats Let's Encrypt
- ✅ **Rate Limiting** - Protection contre les abus
- ✅ **CORS** - Configuré pour votre domaine
- ✅ **Headers de Sécurité** - HSTS, CSP, X-Frame-Options
- ✅ **Mots de Passe Hashés** - bcrypt pour tous les mots de passe

---

## 📁 Structure des Fichiers

```
blingauto-api/
├── docker-compose.preprod.yml          # Compose sans SSL
├── docker-compose.preprod-letsencrypt.yml  # Compose avec Let's Encrypt
├── .env.preprod                         # Template environnement
├── nginx/
│   ├── Dockerfile                       # Image Nginx personnalisée
│   ├── nginx.conf                       # Config Nginx (SSL self-signed)
│   ├── nginx-letsencrypt.conf          # Config Nginx (Let's Encrypt)
│   └── html/
│       ├── index.html                   # Page d'accueil
│       └── 50x.html                     # Page d'erreur
├── scripts/
│   ├── deploy-preprod.sh               # Script de déploiement
│   ├── setup-letsencrypt.sh            # Configuration SSL
│   ├── create_admin.py                 # Création admin auto
│   └── docker-entrypoint.sh            # Entrypoint container
├── PREPROD_DEPLOYMENT_GUIDE.md         # Guide complet
└── README-PREPROD.md                   # Ce fichier
```

---

## 🔧 Commandes Utiles

### Gestion des Services

```bash
# Démarrer
./scripts/deploy-preprod.sh start

# Arrêter
./scripts/deploy-preprod.sh stop

# Redémarrer
./scripts/deploy-preprod.sh restart

# État
./scripts/deploy-preprod.sh status

# Logs
./scripts/deploy-preprod.sh logs

# Health check
./scripts/deploy-preprod.sh health
```

### Base de Données

```bash
# Backup manuel
./scripts/deploy-preprod.sh backup

# Accéder à PostgreSQL
docker-compose -f docker-compose.preprod.yml exec postgres psql -U blingauto_preprod

# Voir les tables
docker-compose -f docker-compose.preprod.yml exec postgres psql -U blingauto_preprod -d blingauto_preprod -c "\dt"
```

### Logs et Debug

```bash
# Tous les logs
docker-compose -f docker-compose.preprod.yml logs -f

# API seulement
docker-compose -f docker-compose.preprod.yml logs -f api

# Nginx seulement
docker-compose -f docker-compose.preprod.yml logs -f nginx

# 100 dernières lignes
docker-compose -f docker-compose.preprod.yml logs --tail=100
```

---

## 🌐 Endpoints Disponibles

Après déploiement, ces endpoints sont accessibles:

| Endpoint | Description |
|----------|-------------|
| `https://preprod.blingauto.com/` | Page d'accueil |
| `https://preprod.blingauto.com/docs` | Documentation Swagger UI |
| `https://preprod.blingauto.com/redoc` | Documentation ReDoc |
| `https://preprod.blingauto.com/health` | Health check |
| `https://preprod.blingauto.com/api/v1/*` | Endpoints API |

---

## 🔐 Configuration SSL

### Option 1: Self-Signed (Test Local)

Utilisé par défaut avec `docker-compose.preprod.yml`:

```bash
./scripts/deploy-preprod.sh
# SSL self-signed automatiquement généré
```

⚠️ Le navigateur affichera un avertissement (normal pour certificat self-signed)

### Option 2: Let's Encrypt (Production)

Pour un certificat SSL valide gratuit:

```bash
# 1. Configurer le DNS (domaine → IP serveur)
nslookup preprod.blingauto.com

# 2. Obtenir le certificat
./scripts/setup-letsencrypt.sh preprod.blingauto.com admin@blingauto.com

# 3. Déployer avec Let's Encrypt
docker-compose -f docker-compose.preprod-letsencrypt.yml --env-file .env.preprod.local up -d
```

✅ Certificat valide reconnu par tous les navigateurs
✅ Renouvellement automatique tous les 90 jours

---

## 👤 Utilisateur Admin

Un utilisateur admin est créé automatiquement au premier démarrage.

### Credentials par Défaut

Configurés dans `.env.preprod.local`:

```bash
INITIAL_ADMIN_EMAIL=admin@preprod.blingauto.com
INITIAL_ADMIN_PASSWORD=VotreMotDePasse
```

### Se Connecter

```bash
# Via curl
curl -X POST https://preprod.blingauto.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@preprod.blingauto.com",
    "password": "VotreMotDePasse"
  }'

# Via Swagger UI
# 1. Aller sur https://preprod.blingauto.com/docs
# 2. Cliquer sur "Authorize"
# 3. Se connecter avec email/password
```

⚠️ **IMPORTANT**: Changer le mot de passe admin après la première connexion!

---

## 📊 Surveillance

### Health Check Automatique

Tous les services ont des health checks configurés:

```bash
# Voir l'état de santé
docker-compose -f docker-compose.preprod.yml ps

NAME                  STATUS                    PORTS
blingauto-api        Up (healthy)              8000/tcp
blingauto-nginx      Up (healthy)              0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
blingauto-postgres   Up (healthy)              5432/tcp
blingauto-redis      Up (healthy)              6379/tcp
```

### Métriques en Temps Réel

```bash
# Utilisation des ressources
docker stats

# Exemple de sortie:
CONTAINER          CPU %     MEM USAGE / LIMIT     MEM %     NET I/O
blingauto-api      15%       256MB / 4GB           6.4%      1.2MB / 890KB
blingauto-nginx    2%        32MB / 4GB            0.8%      5.6MB / 3.2MB
blingauto-postgres 8%        128MB / 4GB           3.2%      450KB / 380KB
blingauto-redis    3%        48MB / 512MB          9.4%      120KB / 95KB
```

---

## 🛠️ Dépannage

### Services ne démarrent pas

```bash
# Vérifier les logs
./scripts/deploy-preprod.sh logs

# Ports déjà utilisés?
sudo netstat -tulpn | grep -E ':(80|443) '

# Redémarrer Docker
sudo systemctl restart docker
```

### API retourne 502

```bash
# L'API ne répond pas
docker-compose -f docker-compose.preprod.yml logs api

# Redémarrer l'API
docker-compose -f docker-compose.preprod.yml restart api
```

### Base de données corrompue

```bash
# Restaurer depuis backup
./scripts/deploy-preprod.sh rollback

# Ou recréer (⚠️ PERTE DE DONNÉES)
docker-compose -f docker-compose.preprod.yml down -v
./scripts/deploy-preprod.sh
```

### SSL ne fonctionne pas

```bash
# Vérifier DNS
nslookup preprod.blingauto.com

# Vérifier ports ouverts
sudo ufw status

# Ouvrir ports si nécessaire
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Re-générer certificat
./scripts/setup-letsencrypt.sh preprod.blingauto.com admin@blingauto.com
```

---

## 📋 Checklist de Déploiement

Avant de mettre en production, vérifier:

- [ ] ✅ `.env.preprod.local` configuré avec secrets forts
- [ ] ✅ DNS configuré (domaine → IP serveur)
- [ ] ✅ Ports 80 et 443 ouverts dans le firewall
- [ ] ✅ Docker et Docker Compose installés
- [ ] ✅ Services démarrés: `./scripts/deploy-preprod.sh status`
- [ ] ✅ Health check OK: `curl https://preprod.blingauto.com/health`
- [ ] ✅ SSL valide (Let's Encrypt)
- [ ] ✅ Admin créé et mot de passe changé
- [ ] ✅ Documentation accessible: `/docs`
- [ ] ✅ Tests API passent
- [ ] ✅ Backups configurés (cron)
- [ ] ✅ Monitoring externe configuré

---

## 🚀 Déploiement Complet

### Scénario: Nouveau Serveur

```bash
# 1. SSH dans le serveur
ssh user@preprod.blingauto.com

# 2. Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Installer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Cloner le projet
git clone https://github.com/yourusername/blingauto-api.git
cd blingauto-api

# 5. Configurer l'environnement
cp .env.preprod .env.preprod.local
nano .env.preprod.local
# Modifier: SECRET_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD, INITIAL_ADMIN_*

# 6. Déployer (sans SSL d'abord)
chmod +x scripts/deploy-preprod.sh
./scripts/deploy-preprod.sh

# 7. Tester
curl http://localhost/health

# 8. Configurer SSL
chmod +x scripts/setup-letsencrypt.sh
./scripts/setup-letsencrypt.sh preprod.blingauto.com admin@blingauto.com

# 9. Redéployer avec SSL
docker-compose -f docker-compose.preprod-letsencrypt.yml --env-file .env.preprod.local up -d

# 10. Vérifier
curl https://preprod.blingauto.com/health
open https://preprod.blingauto.com/docs
```

---

## 📞 Support

**Documentation Complète**: [PREPROD_DEPLOYMENT_GUIDE.md](./PREPROD_DEPLOYMENT_GUIDE.md)

**Problèmes**:
- GitHub Issues: https://github.com/yourusername/blingauto-api/issues
- Email: support@blingauto.com

**Contribution**:
- Fork le projet
- Créer une branche feature
- Soumettre une Pull Request

---

**Version**: 1.0.0
**Dernière Mise à Jour**: 2025-10-01
**Environnement**: Pre-Production
**Statut**: ✅ Production Ready
