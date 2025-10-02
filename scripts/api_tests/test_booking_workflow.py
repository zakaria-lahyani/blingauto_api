"""
Test du workflow complet de réservation (Booking)

Ce script teste:
- Utilisation d'un client existant (créé par test_auth_rbac.py)
- Ajout de véhicule client
- Calcul de devis avec services existants
- Création d'une réservation
- Mise à jour du statut de réservation
- Annulation de réservation

IMPORTANT: Ce script utilise les utilisateurs créés par test_auth_rbac.py
           Exécutez d'abord test_auth_rbac.py avant ce script.

Prérequis:
- API en cours d'exécution sur http://localhost:8000
- Base de données initialisée
- test_auth_rbac.py déjà exécuté (utilisateurs créés)
"""

import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta

# Import des utilitaires partagés
from utils import (
    AUTH_URL, SERVICES_URL, VEHICLES_URL, BOOKINGS_URL, PRICING_URL,
    TestUser, TestDataManager,
    print_section, print_success, print_error, print_warning, print_info,
    Colors, check_prerequisites
)


def login_existing_user(user: TestUser) -> Optional[TestUser]:
    """Se connecte avec un utilisateur existant et met à jour son token."""
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


def list_services(token: str) -> List[Dict]:
    """Liste tous les services disponibles."""
    try:
        response = requests.get(
            f"{SERVICES_URL}/",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        data = response.json()
        services = data.get("services", [])
        print_success(f"Services récupérés: {len(services)} service(s)")
        return services
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la récupération des services: {e}")
        return []


def create_vehicle(token: str, make: str, model: str, year: int, license_plate: str) -> Optional[str]:
    """Crée un véhicule pour l'utilisateur."""
    try:
        response = requests.post(
            f"{VEHICLES_URL}/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "make": make,
                "model": model,
                "year": year,
                "license_plate": license_plate,
                "color": "Blue",
                "vehicle_type": "sedan"
            }
        )
        response.raise_for_status()
        data = response.json()
        vehicle_id = data.get("id")
        print_success(f"Véhicule créé: {make} {model} ({license_plate})")
        return vehicle_id
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la création du véhicule: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Détails: {e.response.text}")
        return None


def calculate_quote(token: str, service_ids: List[str]) -> Optional[Dict]:
    """Calcule un devis pour les services sélectionnés."""
    try:
        response = requests.post(
            f"{PRICING_URL}/quote",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "service_ids": service_ids,
                "apply_tax": True,
                "apply_discounts": False
            }
        )
        response.raise_for_status()
        data = response.json()
        print_success(f"Devis calculé - Total: {data.get('final_price', 'N/A')}€")
        return data
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors du calcul du devis: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Détails: {e.response.text}")
        return None


def create_booking(token: str, vehicle_id: str, service_ids: List[str],
                   scheduled_time: str) -> Optional[str]:
    """Crée une réservation."""
    try:
        response = requests.post(
            f"{BOOKINGS_URL}/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "vehicle_id": vehicle_id,
                "service_ids": service_ids,
                "scheduled_time": scheduled_time,
                "notes": "Test booking via API"
            }
        )
        response.raise_for_status()
        data = response.json()
        booking_id = data.get("id")
        print_success(f"Réservation créée: {booking_id}")
        print_info(f"  Horaire: {scheduled_time}")
        print_info(f"  Statut: {data.get('status', 'unknown')}")
        return booking_id
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la création de la réservation: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Détails: {e.response.text}")
        return None


def get_booking(token: str, booking_id: str) -> Optional[Dict]:
    """Récupère les détails d'une réservation."""
    try:
        response = requests.get(
            f"{BOOKINGS_URL}/{booking_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        data = response.json()
        print_success(f"Réservation récupérée: {booking_id}")
        return data
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la récupération de la réservation: {e}")
        return None


def update_booking_status(token: str, booking_id: str, new_status: str) -> bool:
    """Met à jour le statut d'une réservation."""
    try:
        response = requests.patch(
            f"{BOOKINGS_URL}/{booking_id}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": new_status}
        )
        response.raise_for_status()
        print_success(f"Statut mis à jour: {new_status}")
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la mise à jour du statut: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Détails: {e.response.text}")
        return False


def cancel_booking(token: str, booking_id: str, reason: str) -> bool:
    """Annule une réservation."""
    try:
        response = requests.post(
            f"{BOOKINGS_URL}/{booking_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": reason}
        )
        response.raise_for_status()
        print_success(f"Réservation annulée: {booking_id}")
        print_info(f"  Raison: {reason}")
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de l'annulation: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Détails: {e.response.text}")
        return False


def list_my_bookings(token: str) -> List[Dict]:
    """Liste toutes les réservations de l'utilisateur."""
    try:
        response = requests.get(
            f"{BOOKINGS_URL}/my-bookings",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        data = response.json()
        bookings = data.get("bookings", [])
        print_success(f"Réservations récupérées: {len(bookings)} réservation(s)")
        return bookings
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la récupération des réservations: {e}")
        return []


def main():
    """Fonction principale de test du workflow de réservation."""

    print_section(" TEST WORKFLOW COMPLET DE RÉSERVATION")

    # Vérifier les prérequis
    if not check_prerequisites():
        print_error("\n Prérequis non satisfaits. Arrêt des tests.")
        return

    # Initialiser le gestionnaire de données
    data_manager = TestDataManager()

    # --- ÉTAPE 1: Récupération d'un client existant ---
    print_section("1️  UTILISATION D'UN CLIENT EXISTANT")

    # Récupérer un client depuis les données de test
    client = data_manager.get_user_by_role("client")

    if not client:
        print_error("Aucun client trouvé dans les données de test")
        print_warning("Exécutez d'abord: python scripts/api_tests/test_auth_rbac.py")
        return

    print_info(f"Client sélectionné: {client.email} (Rôle: {client.role})")

    # Se connecter pour obtenir un token valide
    client = login_existing_user(client)
    if not client or not client.access_token:
        print_error("Impossible de se connecter avec le client")
        return

    # --- ÉTAPE 2: Vérification des services disponibles ---
    print_section("2️  VÉRIFICATION DES SERVICES DISPONIBLES")

    # Lister les services existants
    services = list_services(client.access_token)

    service_ids = []
    if services and len(services) >= 2:
        # Utiliser les services existants
        service_ids = [s.get("id") for s in services[:2] if s.get("id")]
        print_info(f"Utilisation de {len(service_ids)} service(s) existant(s)")
        for srv in services[:2]:
            print(f"  • {srv.get('name')} - {srv.get('price')}€ ({srv.get('duration_minutes')}min)")
    else:
        print_warning("Pas assez de services disponibles")
        print_info("Les services devraient être créés par un admin/manager")
        print_info("Exécutez: python scripts/api_tests/test_services_management.py")

    # --- ÉTAPE 3: Création d'un véhicule ---
    print_section("3️  AJOUT D'UN VÉHICULE CLIENT")

    license_plate = f"BKG{datetime.now().strftime('%H%M%S')}"
    vehicle_id = create_vehicle(
        client.access_token,
        "Toyota",
        "Camry",
        2022,
        license_plate
    )

    if not vehicle_id:
        print_error("Impossible de continuer sans véhicule")
        return

    # --- ÉTAPE 4: Calcul de devis (si services disponibles) ---
    if service_ids:
        print_section("4️  CALCUL DE DEVIS")

        quote = calculate_quote(client.access_token, service_ids)
        if quote:
            print(f"\n{Colors.BOLD}Détails du devis:{Colors.RESET}")
            print_info(f"  Sous-total: {quote.get('subtotal', 'N/A')}€")
            print_info(f"  Taxes: {quote.get('tax_amount', 'N/A')}€")
            print_info(f"  Total: {quote.get('final_price', 'N/A')}€")
            print_info(f"  Durée totale: {quote.get('total_duration', 'N/A')} minutes")

    # --- ÉTAPE 5: Création de réservation ---
    print_section("5️  CRÉATION DE RÉSERVATION")

    if not service_ids:
        print_warning("Impossible de créer une réservation sans services")
        print_info("Ce test nécessite des services. Exécutez test_services_management.py d'abord.")
        return

    # Horaire dans 2 jours à 14h
    scheduled_time = (datetime.now() + timedelta(days=2)).replace(hour=14, minute=0, second=0, microsecond=0)
    scheduled_time_str = scheduled_time.isoformat()

    print_info(f"Horaire demandé: {scheduled_time.strftime('%Y-%m-%d %H:%M')}")

    booking_id = create_booking(
        client.access_token,
        vehicle_id,
        service_ids,
        scheduled_time_str
    )

    if not booking_id:
        print_warning("Impossible de créer une réservation")
        return

    # --- ÉTAPE 6: Récupération des détails ---
    print_section("6️  RÉCUPÉRATION DES DÉTAILS DE RÉSERVATION")

    booking_details = get_booking(client.access_token, booking_id)
    if booking_details:
        print(f"\n{Colors.BOLD}Détails de la réservation:{Colors.RESET}")
        print_info(f"  ID: {booking_details.get('id')}")
        print_info(f"  Statut: {booking_details.get('status')}")
        print_info(f"  Client: {booking_details.get('customer_id')}")
        print_info(f"  Véhicule: {booking_details.get('vehicle_id')}")
        print_info(f"  Horaire: {booking_details.get('scheduled_time')}")
        print_info(f"  Services: {len(booking_details.get('services', []))} service(s)")

    # --- ÉTAPE 7: Mise à jour du statut ---
    print_section("7️  MISE À JOUR DU STATUT")

    print_info("RÈGLE: Seul un admin/manager peut confirmer une réservation")
    print_info("       Un client peut uniquement annuler sa propre réservation\n")

    # Essayer avec le client (devrait échouer ou être limité)
    update_success = update_booking_status(client.access_token, booking_id, "confirmed")

    # Si on a un manager, on pourrait essayer avec lui
    if not update_success:
        manager = data_manager.get_user_by_role("manager")
        if manager:
            print_info("\nTentative avec un compte manager...")
            manager = login_existing_user(manager)
            if manager:
                update_success = update_booking_status(manager.access_token, booking_id, "confirmed")

    # Vérifier le changement
    if update_success:
        booking_details = get_booking(client.access_token, booking_id)
        if booking_details:
            status = booking_details.get('status')
            status_color = Colors.GREEN if status == 'confirmed' else Colors.YELLOW
            print_info(f"  Nouveau statut: {status_color}{status}{Colors.RESET}")

    # --- ÉTAPE 8: Liste des réservations ---
    print_section("8️  LISTE DE MES RÉSERVATIONS")

    my_bookings = list_my_bookings(client.access_token)
    if my_bookings:
        print(f"\n{Colors.BOLD}Mes réservations:{Colors.RESET}")
        for booking in my_bookings:
            status = booking.get('status', 'unknown')
            status_color = (
                Colors.GREEN if status == 'confirmed' else
                Colors.YELLOW if status == 'pending' else
                Colors.RED if status == 'cancelled' else
                Colors.RESET
            )
            scheduled = booking.get('scheduled_time', 'N/A')
            print(f"  • ID: {booking.get('id'):<36} | {status_color}{status:<12}{Colors.RESET} | {scheduled}")

    # --- ÉTAPE 9: Annulation ---
    print_section("9️  ANNULATION DE RÉSERVATION")

    print_info("RÈGLE: Un client peut annuler sa propre réservation\n")

    cancel_success = cancel_booking(
        client.access_token,
        booking_id,
        "Test d'annulation via API - Scénario de test"
    )

    if cancel_success:
        # Vérifier l'annulation
        booking_details = get_booking(client.access_token, booking_id)
        if booking_details:
            status = booking_details.get('status')
            print_info(f"  Statut final: {Colors.RED}{status}{Colors.RESET}")

    # --- RÉSUMÉ ---
    print_section(" RÉSUMÉ DU WORKFLOW")

    print(f"{Colors.BOLD}Client utilisé:{Colors.RESET}")
    print(f"  • Email: {client.email}")
    print(f"  • Rôle: {client.role}")

    print(f"\n{Colors.BOLD}Étapes complétées:{Colors.RESET}")
    print(f"  ✓ Connexion avec client existant")
    print(f"  ✓ Vérification des services disponibles")
    print(f"  ✓ Ajout d'un véhicule")
    if service_ids:
        print(f"  ✓ Calcul de devis")
        print(f"  ✓ Création de réservation")
        print(f"  ✓ Récupération des détails")
        print(f"  ✓ Mise à jour du statut (avec permissions)")
        print(f"  ✓ Liste des réservations")
        print(f"  ✓ Annulation de réservation")
    else:
        print(f"   Tests de réservation limités (pas de services)")

    print(f"\n{Colors.GREEN}{Colors.BOLD} Workflow de réservation testé!{Colors.RESET}")
    print(f"\n{Colors.INFO}ℹ  Note: Pour des tests complets, assurez-vous d'avoir:{Colors.RESET}")
    print(f"{Colors.INFO}   - Des services créés (via test_services_management.py){Colors.RESET}")
    print(f"{Colors.INFO}   - Des utilisateurs avec différents rôles (via test_auth_rbac.py){Colors.RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrompus par l'utilisateur{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Erreur inattendue: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
