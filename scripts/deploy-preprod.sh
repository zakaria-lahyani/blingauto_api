#!/bin/bash
# =============================================================================
# BlingAuto API - Pre-Production Deployment Script
# Automated deployment with health checks and rollback capability
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.preprod.yml"
ENV_FILE=".env.preprod"
BACKUP_DIR="./backups"

# Functions
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

# Check prerequisites
check_prerequisites() {
    print_header "Vérification des Prérequis"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé"
        exit 1
    fi
    print_success "Docker: $(docker --version)"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé"
        exit 1
    fi
    print_success "Docker Compose: $(docker-compose --version)"

    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Fichier d'environnement $ENV_FILE introuvable"
        print_info "Copiez .env.preprod et configurez-le"
        exit 1
    fi
    print_success "Fichier d'environnement: $ENV_FILE"

    # Check compose file
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Fichier Docker Compose $COMPOSE_FILE introuvable"
        exit 1
    fi
    print_success "Docker Compose file: $COMPOSE_FILE"
}

# Backup database
backup_database() {
    print_header "Sauvegarde de la Base de Données"

    mkdir -p "$BACKUP_DIR"

    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

    print_info "Création de la sauvegarde: $BACKUP_FILE"

    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_dump -U blingauto_preprod blingauto_preprod > "$BACKUP_FILE" 2>/dev/null; then
        print_success "Sauvegarde créée avec succès"

        # Compress backup
        gzip "$BACKUP_FILE"
        print_success "Sauvegarde compressée: ${BACKUP_FILE}.gz"
    else
        print_warning "Impossible de créer la sauvegarde (la base n'existe peut-être pas encore)"
    fi
}

# Pull latest images
pull_images() {
    print_header "Téléchargement des Images Docker"

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull

    print_success "Images téléchargées"
}

# Build images
build_images() {
    print_header "Construction des Images Docker"

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache

    print_success "Images construites"
}

# Stop services
stop_services() {
    print_header "Arrêt des Services"

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down

    print_success "Services arrêtés"
}

# Start services
start_services() {
    print_header "Démarrage des Services"

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    print_success "Services démarrés"
}

# Wait for services
wait_for_services() {
    print_header "Attente de la Disponibilité des Services"

    print_info "Attente de PostgreSQL..."
    sleep 10

    print_info "Attente de Redis..."
    sleep 5

    print_info "Attente de l'API..."
    sleep 15

    print_success "Services prêts"
}

# Check health
check_health() {
    print_header "Vérification de la Santé des Services"

    MAX_RETRIES=30
    RETRY_DELAY=2

    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s -f http://localhost/health > /dev/null; then
            print_success "API est en bonne santé"
            return 0
        fi
        print_info "Tentative $i/$MAX_RETRIES..."
        sleep $RETRY_DELAY
    done

    print_error "L'API ne répond pas après $MAX_RETRIES tentatives"
    return 1
}

# View logs
view_logs() {
    print_header "Logs des Services"

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs --tail=50
}

# Show status
show_status() {
    print_header "État des Services"

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

    echo ""
    print_info "Endpoints disponibles:"
    echo "  • Interface Web: https://localhost"
    echo "  • API Documentation: https://localhost/docs"
    echo "  • ReDoc: https://localhost/redoc"
    echo "  • Health Check: https://localhost/health"
}

# Rollback
rollback() {
    print_header "Rollback en Cours"

    print_warning "Restauration de la version précédente..."

    # Stop current services
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down

    # Restore from latest backup if needed
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        print_info "Dernière sauvegarde disponible: $LATEST_BACKUP"
        print_warning "Restauration manuelle requise si nécessaire"
    fi

    print_error "Rollback terminé - Veuillez vérifier les logs"
}

# Main deployment
main() {
    print_header "Déploiement BlingAuto API - Pre-Production"

    # Check prerequisites
    check_prerequisites

    # Ask for confirmation
    echo ""
    read -p "Continuer le déploiement? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Déploiement annulé"
        exit 0
    fi

    # Backup database
    backup_database

    # Pull and build images
    pull_images
    build_images

    # Stop old services
    stop_services

    # Start new services
    start_services

    # Wait for services to be ready
    wait_for_services

    # Check health
    if check_health; then
        print_header "Déploiement Réussi ✓"
        show_status
    else
        print_error "Échec du déploiement"
        read -p "Effectuer un rollback? (y/N) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback
        else
            print_warning "Vérifiez les logs:"
            view_logs
        fi
        exit 1
    fi
}

# Menu
case "${1:-}" in
    start)
        start_services
        wait_for_services
        check_health
        show_status
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        start_services
        wait_for_services
        check_health
        show_status
        ;;
    status)
        show_status
        ;;
    logs)
        view_logs
        ;;
    health)
        check_health
        ;;
    backup)
        backup_database
        ;;
    rollback)
        rollback
        ;;
    *)
        main
        ;;
esac
