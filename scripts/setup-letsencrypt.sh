#!/bin/bash
# =============================================================================
# BlingAuto API - Let's Encrypt SSL Setup Script
# Automatic SSL certificate generation for pre-production
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Configuration
DOMAIN="${1:-}"
EMAIL="${2:-}"
STAGING="${3:-0}"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    print_error "Usage: $0 <domain> <email> [staging]"
    echo ""
    echo "Exemples:"
    echo "  $0 preprod.blingauto.com admin@blingauto.com"
    echo "  $0 preprod.blingauto.com admin@blingauto.com 1  # Mode staging (test)"
    exit 1
fi

print_header "Configuration Let's Encrypt SSL pour $DOMAIN"

# Create directories
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Staging flag
STAGING_ARG=""
if [ "$STAGING" != "0" ]; then
    STAGING_ARG="--staging"
    print_warning "Mode STAGING activé (certificats de test)"
fi

# Request certificate
print_info "Demande de certificat SSL pour: $DOMAIN"
print_info "Email: $EMAIL"

docker-compose -f docker-compose.preprod-letsencrypt.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    $STAGING_ARG \
    -d "$DOMAIN"

if [ $? -eq 0 ]; then
    print_success "Certificat SSL obtenu avec succès!"

    # Update nginx config with domain
    print_info "Mise à jour de la configuration Nginx..."

    sed -i "s/yourdomain.com/$DOMAIN/g" ./nginx/nginx-letsencrypt.conf

    print_success "Configuration Nginx mise à jour"

    # Reload nginx
    print_info "Rechargement de Nginx..."
    docker-compose -f docker-compose.preprod-letsencrypt.yml exec nginx nginx -s reload

    print_header "Configuration SSL Terminée ✓"
    print_success "Votre site est maintenant accessible via HTTPS"
    print_info "URL: https://$DOMAIN"
else
    print_error "Échec de l'obtention du certificat SSL"
    print_warning "Vérifiez que:"
    echo "  • Le domaine $DOMAIN pointe vers ce serveur"
    echo "  • Le port 80 est accessible depuis Internet"
    echo "  • Nginx est démarré"
    exit 1
fi
