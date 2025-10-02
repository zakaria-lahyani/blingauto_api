"""
Test de gestion des services et catégories

Ce script teste:
- Utilisation d'un utilisateur manager/admin existant (créé par test_auth_rbac.py)
- Création de catégories
- Création de services dans les catégories
- Listing des services
- Mise à jour de services
- Activation/désactivation de services
- Suppression de services

IMPORTANT: Ce script utilise les utilisateurs créés par test_auth_rbac.py
           Un utilisateur manager ou admin est requis pour gérer les services.

Prérequis:
- API en cours d'exécution sur http://localhost:8000
- Base de données initialisée
- test_auth_rbac.py déjà exécuté (utilisateurs créés avec au moins un manager/admin)
"""

import requests
from typing import Dict, Optional, List
from datetime import datetime

# Import des utilitaires partagés
from utils import (
    SERVICES_URL, TestUser, TestDataManager,
    print_section, print_success, print_error, print_warning, print_info,
    Colors, check_prerequisites
)


def login_existing_user(user: TestUser) -> Optional[TestUser]:
    """Se connecte avec un utilisateur existant et met à jour son token."""
    from utils import AUTH_URL

    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            json={"email": user.email, "password": user.password}
        )
        response.raise_for_status()
        data = response.json()

        # Mettre à jour les tokens
        user.access_token = data.get("access_token")
        user.refresh_token = data.get("refresh_token")
        user.role = data.get("role")

        print_success(f"Connexion réussie: {user.email} (Rôle: {user.role})")
        return user
    except requests.exceptions.RequestException as e:
        print_error(f"Échec de connexion pour {user.email}: {e}")
        return None


def create_category(token: str, name: str, description: str, display_order: int = 1) -> Optional[str]:
    """Crée une catégorie de service."""
    try:
        response = requests.post(
            f"{SERVICES_URL}/categories",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": name,
                "description": description,
                "display_order": display_order
            }
        )
        response.raise_for_status()
        data = response.json()
        category_id = data.get("id")
        print_success(f"Catégorie créée: '{name}' (ID: {category_id})")
        return category_id
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur création catégorie '{name}': {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Détails: {e.response.text}")
        return None


def list_categories(token: str) -> List[Dict]:
    """Liste toutes les catégories."""
    try:
        response = requests.get(
            f"{SERVICES_URL}/categories",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        data = response.json()
        categories = data.get("categories", [])
        print_success(f"Catégories récupérées: {len(categories)} catégorie(s)")
        return categories
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la récupération des catégories: {e}")
        return []


def get_category(token: str, category_id: str) -> Optional[Dict]:
    """Récupère les détails d'une catégorie."""
    try:
        response = requests.get(
            f"{SERVICES_URL}/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        data = response.json()
        print_success(f"Catégorie récupérée: {data.get('name')}")
        return data
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la récupération de la catégorie: {e}")
        return None


def create_service(token: str, category_id: str, name: str, description: str,
                   price: float, duration: int, is_popular: bool = False) -> Optional[str]:
    """Crée un service dans une catégorie."""
    try:
        response = requests.post(
            f"{SERVICES_URL}/categories/{category_id}/services",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": name,
                "description": description,
                "price": str(price),
                "duration_minutes": duration,
                "is_popular": is_popular
            }
        )
        response.raise_for_status()
        data = response.json()
        service_id = data.get("id")
        print_success(f"Service créé: '{name}' - {price}€ ({duration}min)")
        return service_id
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur création service '{name}': {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Détails: {e.response.text}")
        return None


def list_services(token: str, category_id: Optional[str] = None,
                  include_inactive: bool = False) -> List[Dict]:
    """Liste tous les services ou les services d'une catégorie."""
    try:
        if category_id:
            url = f"{SERVICES_URL}/categories/{category_id}/services"
        else:
            url = f"{SERVICES_URL}/"

        params = {"include_inactive": include_inactive}

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )
        response.raise_for_status()
        data = response.json()
        services = data.get("services", [])
        print_success(f"Services récupérés: {len(services)} service(s)")
        return services
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la récupération des services: {e}")
        return []


def get_service(token: str, service_id: str) -> Optional[Dict]:
    """Récupère les détails d'un service."""
    try:
        response = requests.get(
            f"{SERVICES_URL}/{service_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        data = response.json()
        print_success(f"Service récupéré: {data.get('name')}")
        return data
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la récupération du service: {e}")
        return None


def update_service(token: str, service_id: str, **updates) -> bool:
    """Met à jour un service."""
    try:
        response = requests.patch(
            f"{SERVICES_URL}/{service_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=updates
        )
        response.raise_for_status()
        print_success(f"Service mis à jour: {service_id}")
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la mise à jour: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Détails: {e.response.text}")
        return False


def toggle_service_status(token: str, service_id: str, activate: bool) -> bool:
    """Active ou désactive un service."""
    try:
        action = "activate" if activate else "deactivate"
        response = requests.post(
            f"{SERVICES_URL}/{service_id}/{action}",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        status = "activé" if activate else "désactivé"
        print_success(f"Service {status}: {service_id}")
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors du changement de statut: {e}")
        return False


def delete_service(token: str, service_id: str) -> bool:
    """Supprime un service."""
    try:
        response = requests.delete(
            f"{SERVICES_URL}/{service_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        print_success(f"Service supprimé: {service_id}")
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la suppression: {e}")
        return False


def get_popular_services(token: str, limit: int = 5) -> List[Dict]:
    """Récupère les services populaires."""
    try:
        response = requests.get(
            f"{SERVICES_URL}/popular",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": limit}
        )
        response.raise_for_status()
        data = response.json()
        services = data.get("services", [])
        print_success(f"Services populaires récupérés: {len(services)}")
        return services
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la récupération des services populaires: {e}")
        return []


def main():
    """Fonction principale de test de gestion des services."""

    print_section("  TEST GESTION DES SERVICES ET CATÉGORIES")

    # Vérifier les prérequis
    if not check_prerequisites():
        print_error("\n Prérequis non satisfaits. Arrêt des tests.")
        return

    # Initialiser le gestionnaire de données
    data_manager = TestDataManager()

    # --- ÉTAPE 1: Récupération d'un manager ou admin existant ---
    print_section("1️  UTILISATION D'UN UTILISATEUR MANAGER/ADMIN")

    print_info("RÈGLE: Seuls les managers et admins peuvent gérer les services\n")

    # Essayer de récupérer un manager d'abord
    manager = data_manager.get_user_by_role("manager")

    if not manager:
        # Sinon essayer un admin
        manager = data_manager.get_user_by_role("admin")

    if not manager:
        print_error("Aucun manager ou admin trouvé dans les données de test")
        print_warning("Exécutez d'abord: python scripts/api_tests/test_auth_rbac.py")
        print_info("Assurez-vous qu'au moins un utilisateur a le rôle 'manager' ou 'admin'")
        return

    print_info(f"Utilisateur sélectionné: {manager.email} (Rôle: {manager.role})")

    # Se connecter pour obtenir un token valide
    manager = login_existing_user(manager)
    if not manager or not manager.access_token:
        print_error("Impossible de se connecter avec l'utilisateur")
        return

    # --- ÉTAPE 2: Création de catégories ---
    print_section("2️  CRÉATION DE CATÉGORIES")

    categories_data = [
        ("Lavage Extérieur", "Services de lavage extérieur du véhicule", 1),
        ("Lavage Intérieur", "Services de nettoyage intérieur", 2),
        ("Detailing Premium", "Services de detailing haut de gamme", 3),
    ]

    category_ids = {}
    for name, desc, order in categories_data:
        cat_id = create_category(manager.access_token, name, desc, order)
        if cat_id:
            category_ids[name] = cat_id

    # --- ÉTAPE 3: Listing des catégories ---
    print_section("3️  LISTING DES CATÉGORIES")

    categories = list_categories(manager.access_token)
    if categories:
        print(f"\n{Colors.BOLD}Catégories disponibles:{Colors.RESET}")
        for cat in categories:
            print(f"  • {cat.get('name'):<25} - {cat.get('service_count', 0)} service(s)")

    # --- ÉTAPE 4: Création de services ---
    print_section("4️  CRÉATION DE SERVICES")

    services_data = []
    if "Lavage Extérieur" in category_ids:
        ext_cat_id = category_ids["Lavage Extérieur"]
        services_data.extend([
            (ext_cat_id, "Lavage Express", "Lavage rapide extérieur", 20.00, 20, False),
            (ext_cat_id, "Lavage Standard", "Lavage complet extérieur", 30.00, 30, True),
            (ext_cat_id, "Lavage Premium", "Lavage premium avec cire", 50.00, 45, True),
        ])

    if "Lavage Intérieur" in category_ids:
        int_cat_id = category_ids["Lavage Intérieur"]
        services_data.extend([
            (int_cat_id, "Aspirateur Basique", "Aspiration intérieure basique", 15.00, 15, False),
            (int_cat_id, "Nettoyage Complet", "Nettoyage intérieur complet", 40.00, 40, True),
        ])

    if "Detailing Premium" in category_ids:
        det_cat_id = category_ids["Detailing Premium"]
        services_data.extend([
            (det_cat_id, "Polish & Wax", "Polissage et cirage professionnel", 80.00, 90, False),
            (det_cat_id, "Detailing Complet", "Service de detailing complet", 150.00, 180, True),
        ])

    service_ids = []
    for cat_id, name, desc, price, duration, popular in services_data:
        srv_id = create_service(manager.access_token, cat_id, name, desc, price, duration, popular)
        if srv_id:
            service_ids.append(srv_id)

    # --- ÉTAPE 5: Listing des services ---
    print_section("5️  LISTING DE TOUS LES SERVICES")

    all_services = list_services(manager.access_token)
    if all_services:
        print(f"\n{Colors.BOLD}Services disponibles:{Colors.RESET}")
        for srv in all_services:
            popular_badge = f"{Colors.YELLOW} {Colors.RESET}" if srv.get('is_popular') else "  "
            status_color = Colors.GREEN if srv.get('status') == 'active' else Colors.RED
            print(f"  {popular_badge} {srv.get('name'):<25} {srv.get('price', 0):>6}€ ({srv.get('duration_minutes', 0):>3}min) [{status_color}{srv.get('status')}{Colors.RESET}]")

    # --- ÉTAPE 6: Récupération d'un service spécifique ---
    if service_ids:
        print_section("6️  RÉCUPÉRATION D'UN SERVICE SPÉCIFIQUE")

        service_details = get_service(manager.access_token, service_ids[0])
        if service_details:
            print(f"\n{Colors.BOLD}Détails du service:{Colors.RESET}")
            print_info(f"  ID: {service_details.get('id')}")
            print_info(f"  Nom: {service_details.get('name')}")
            print_info(f"  Prix: {service_details.get('price')}€")
            print_info(f"  Durée: {service_details.get('duration_minutes')} minutes")
            print_info(f"  Statut: {service_details.get('status')}")
            print_info(f"  Populaire: {'Oui' if service_details.get('is_popular') else 'Non'}")

    # --- ÉTAPE 7: Mise à jour d'un service ---
    if service_ids:
        print_section("7️  MISE À JOUR D'UN SERVICE")

        new_price = 35.00
        update_success = update_service(
            manager.access_token,
            service_ids[0],
            price=str(new_price),
            description="Description mise à jour via API"
        )

        if update_success:
            # Vérifier la mise à jour
            updated_service = get_service(manager.access_token, service_ids[0])
            if updated_service:
                print_info(f"  Nouveau prix: {updated_service.get('price')}€")
                print_info(f"  Description: {updated_service.get('description')}")

    # --- ÉTAPE 8: Services populaires ---
    print_section("8️  SERVICES POPULAIRES")

    popular_services = get_popular_services(manager.access_token, limit=5)
    if popular_services:
        print(f"\n{Colors.BOLD}Top services populaires:{Colors.RESET}")
        for i, srv in enumerate(popular_services, 1):
            print(f"  {i}. {srv.get('name'):<25} {srv.get('price', 0):>6}€")

    # --- ÉTAPE 9: Désactivation d'un service ---
    if service_ids and len(service_ids) > 1:
        print_section("9️  DÉSACTIVATION D'UN SERVICE")

        deactivate_success = toggle_service_status(manager.access_token, service_ids[1], False)

        if deactivate_success:
            # Vérifier le statut
            service_details = get_service(manager.access_token, service_ids[1])
            if service_details:
                status = service_details.get('status')
                status_color = Colors.GREEN if status == 'active' else Colors.RED
                print_info(f"  Statut actuel: {status_color}{status}{Colors.RESET}")

    # --- ÉTAPE 10: Réactivation du service ---
    if service_ids and len(service_ids) > 1:
        print_section(" RÉACTIVATION DU SERVICE")

        activate_success = toggle_service_status(manager.access_token, service_ids[1], True)

        if activate_success:
            service_details = get_service(manager.access_token, service_ids[1])
            if service_details:
                status = service_details.get('status')
                status_color = Colors.GREEN if status == 'active' else Colors.RED
                print_info(f"  Statut actuel: {status_color}{status}{Colors.RESET}")

    # --- ÉTAPE 11: Listing avec services inactifs ---
    print_section("1️1️  LISTING AVEC SERVICES INACTIFS")

    all_including_inactive = list_services(manager.access_token, include_inactive=True)
    active_count = sum(1 for s in all_including_inactive if s.get('status') == 'active')
    inactive_count = sum(1 for s in all_including_inactive if s.get('status') == 'inactive')

    print_info(f"  Services actifs: {active_count}")
    print_info(f"  Services inactifs: {inactive_count}")
    print_info(f"  Total: {len(all_including_inactive)}")

    # --- ÉTAPE 12: Suppression d'un service (optionnel) ---
    if service_ids and len(service_ids) > 2:
        print_section("1️2️  SUPPRESSION D'UN SERVICE (TEST)")

        print_warning("Suppression du dernier service créé...")
        delete_success = delete_service(manager.access_token, service_ids[-1])

        if delete_success:
            # Vérifier que le service n'existe plus
            deleted_service = get_service(manager.access_token, service_ids[-1])
            if not deleted_service:
                print_success("Service définitivement supprimé de la base")

    # --- RÉSUMÉ ---
    print_section(" RÉSUMÉ DES TESTS")

    final_categories = list_categories(manager.access_token)
    final_services = list_services(manager.access_token)

    print(f"{Colors.BOLD}Utilisateur:{Colors.RESET}")
    print(f"  • Email: {manager.email}")
    print(f"  • Rôle: {manager.role}")

    print(f"\n{Colors.BOLD}État final:{Colors.RESET}")
    print(f"  • Catégories: {len(final_categories)}")
    print(f"  • Services actifs: {len(final_services)}")

    print(f"\n{Colors.BOLD}Opérations testées:{Colors.RESET}")
    print(f"  ✓ Connexion avec manager/admin existant")
    print(f"  ✓ Création de catégories")
    print(f"  ✓ Création de services")
    print(f"  ✓ Listing et filtrage")
    print(f"  ✓ Mise à jour de services")
    print(f"  ✓ Activation/désactivation")
    print(f"  ✓ Récupération de services populaires")
    print(f"  ✓ Suppression de services")

    print(f"\n{Colors.GREEN}{Colors.BOLD} Tests de gestion des services terminés!{Colors.RESET}")
    print(f"\n{Colors.INFO}ℹ  Les services créés seront disponibles pour:{Colors.RESET}")
    print(f"{Colors.INFO}   - Les tests de réservation (test_booking_workflow.py){Colors.RESET}")
    print(f"{Colors.INFO}   - Les clients pour créer des réservations{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrompus par l'utilisateur{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Erreur inattendue: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
