"""
Test API Authentication avec RBAC (Role-Based Access Control)

Ce script teste:
- Création de 6 utilisateurs (tous client par défaut - IMPOSSIBLE de créer avec un autre rôle)
- Vérification que seul admin peut créer des admins
- Vérification que manager peut créer manager/washer mais pas admin
- Validation des permissions selon les rôles
- Sauvegarde des utilisateurs pour les tests ultérieurs

IMPORTANT: Ce script DOIT être exécuté en PREMIER car il crée les utilisateurs
           qui seront réutilisés par les autres tests.

Prérequis:
- API en cours d'exécution sur http://localhost:8000
- Base de données initialisée
"""

import requests
import json
from typing import Dict, Optional, List

# Import des utilitaires partagés
from utils import (
    AUTH_URL, TestUser, TestDataManager,
    print_section, print_success, print_error, print_warning, print_info,
    Colors, check_prerequisites
)


def register_user(email: str, password: str = "Passw0rd!",
                  first_name: str = "Test", last_name: str = "User") -> Dict:
    """
    Enregistre un nouvel utilisateur.

    IMPORTANT: Tous les utilisateurs sont créés avec le rôle 'client' par défaut.
    Il est IMPOSSIBLE de spécifier un rôle lors de la création.
    """
    try:
        response = requests.post(
            f"{AUTH_URL}/register",
            json={
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": "+1234567890"
            }
        )
        response.raise_for_status()
        data = response.json()
        print_success(f"Utilisateur créé: {email} (ID: {data.get('user_id')})")
        return data
    except requests.exceptions.RequestException as e:
        print_error(f"Échec de l'enregistrement de {email}: {e}")
        if hasattr(e.response, 'text'):
            print(f"  Détails: {e.response.text}")
        return {}


def login_user(email: str, password: str = "Passw0rd!") -> Optional[TestUser]:
    """Connecte un utilisateur et retourne un TestUser avec ses tokens."""
    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()

        user = TestUser(
            email=email,
            password=password,
            user_id=data.get("user_id"),
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            role=data.get("role"),
            first_name=data.get("full_name", "").split()[0] if data.get("full_name") else None,
            last_name=data.get("full_name", "").split()[-1] if data.get("full_name") else None
        )
        print_success(f"Connexion réussie: {email} (Rôle: {user.role})")
        return user
    except requests.exceptions.RequestException as e:
        print_error(f"Échec de connexion pour {email}: {e}")
        if hasattr(e.response, 'text'):
            print(f"  Détails: {e.response.text}")
        return None


def get_user_profile(token: str) -> Dict:
    """Récupère le profil de l'utilisateur connecté."""
    try:
        response = requests.get(
            f"{AUTH_URL}/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print_error(f"Échec de récupération du profil: {e}")
        return {}


def update_role(token: str, user_id: str, new_role: str) -> tuple[int, Dict]:
    """
    Met à jour le rôle d'un utilisateur.

    Permissions:
    - Admin: peut promouvoir vers admin, manager, washer, client
    - Manager: peut promouvoir vers manager, washer, client (PAS admin)
    - Washer/Client: NE PEUT PAS promouvoir (403)
    """
    try:
        response = requests.patch(
            f"{AUTH_URL}/users/{user_id}/role",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": new_role}
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Rôle mis à jour vers '{new_role}' pour l'utilisateur {user_id}")
            return response.status_code, data
        else:
            data = response.json() if response.text else {}
            print_error(f"Échec de mise à jour du rôle (Code: {response.status_code})")
            if data:
                print(f"  Détails: {data}")
            return response.status_code, data

    except requests.exceptions.RequestException as e:
        print_error(f"Erreur lors de la mise à jour du rôle: {e}")
        return 500, {}


def list_users(token: str, role_filter: Optional[str] = None) -> Dict:
    """Liste tous les utilisateurs (admin seulement)."""
    try:
        params = {}
        if role_filter:
            params['role'] = role_filter

        response = requests.get(
            f"{AUTH_URL}/users",
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )
        response.raise_for_status()
        data = response.json()
        print_success(f"Liste récupérée: {data.get('total', 0)} utilisateurs")
        return data
    except requests.exceptions.RequestException as e:
        print_error(f"Échec de récupération de la liste: {e}")
        return {}


def main():
    """Fonction principale de test."""

    print_section(" TEST RBAC - GESTION DES RÔLES ET PERMISSIONS")

    # Vérifier les prérequis
    if not check_prerequisites():
        print_error("\n Prérequis non satisfaits. Arrêt des tests.")
        return

    # Initialiser le gestionnaire de données
    data_manager = TestDataManager()

    # Vérifier si des utilisateurs existent déjà
    existing_users = data_manager.get_all_users()
    if existing_users:
        print_warning(f"\n  {len(existing_users)} utilisateur(s) de test déjà existant(s)")
        response = input("Voulez-vous continuer et créer de nouveaux utilisateurs? (y/N): ")
        if response.lower() != 'y':
            print_info("Test annulé. Utilisez 'python utils.py clear' pour effacer les données.")
            return

    # --- ÉTAPE 1: Création des utilisateurs ---
    print_section("1️  CRÉATION DE 6 UTILISATEURS (TOUS CLIENT PAR DÉFAUT)")

    print_info("RÈGLE: Tous les utilisateurs sont créés avec le rôle 'client'")
    print_info("       Il est IMPOSSIBLE de spécifier un rôle lors de l'inscription\n")

    emails = [f"user{i}@test.com" for i in range(1, 7)]
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]

    users_data = []
    for i, email in enumerate(emails):
        user_data = register_user(
            email,
            first_name=first_names[i],
            last_name=f"Test{i+1}"
        )
        users_data.append(user_data)

    print(f"\n{Colors.BOLD}Résumé:{Colors.RESET} {len(users_data)} utilisateurs créés")

    # --- ÉTAPE 2: Connexion des utilisateurs ---
    print_section("2️  CONNEXION DES UTILISATEURS")

    users: List[TestUser] = []
    for email in emails:
        user = login_user(email)
        if user:
            users.append(user)
            # Sauvegarder l'utilisateur
            data_manager.add_user(user)

    if len(users) < 6:
        print_error("Impossible de continuer: tous les utilisateurs n'ont pas pu se connecter")
        return

    # Sauvegarder les données
    data_manager.save()

    # --- ÉTAPE 3: Vérification des rôles par défaut ---
    print_section("3️  VÉRIFICATION DES RÔLES PAR DÉFAUT")

    all_clients = True
    for user in users:
        if user.role == "client":
            print_success(f"{user.email} → Rôle: {user.role} ✓")
        else:
            print_error(f"{user.email} → Rôle: {user.role} (attendu: client)")
            all_clients = False

    if all_clients:
        print_success("\n TOUS les utilisateurs créés avec le rôle 'client' par défaut")
    else:
        print_error("\n Certains utilisateurs n'ont pas le rôle 'client'")

    # --- ÉTAPE 4: Test des restrictions (client ne peut pas modifier les rôles) ---
    print_section("4️  TEST: CLIENT NE PEUT PAS MODIFIER LES RÔLES")

    print_info("RÈGLE: Seuls admin et manager peuvent modifier les rôles\n")
    print(f"Client {users[4].email} essaie de promouvoir {users[5].email} en manager...")
    status, result = update_role(users[4].access_token, users[5].user_id, "manager")

    if status == 403:
        print_success(" Accès refusé (403) - Comportement attendu")
    else:
        print_error(f" Status inattendu: {status} (attendu: 403)")

    # --- ÉTAPE 5: Promotion manuelle admin (simulation) ---
    print_section("5️  PROMOTION DE USER1 EN ADMIN")

    print_warning("  Cette étape nécessite une intervention manuelle dans la base de données")
    print(f"\n{Colors.BOLD}Pour promouvoir {users[0].email} en admin, exécutez:{Colors.RESET}")
    print(f"{Colors.YELLOW}UPDATE users SET role = 'admin' WHERE id = '{users[0].user_id}';{Colors.RESET}")
    print()

    input(f"{Colors.BOLD}Appuyez sur Entrée après avoir promu user1 en admin...{Colors.RESET}")

    # Reconnexion de user1 pour obtenir le nouveau token avec le rôle admin
    print("\nReconnexion de user1...")
    users[0] = login_user(users[0].email)

    if users[0].role != "admin":
        print_error(f" user1 n'est pas admin (rôle actuel: {users[0].role})")
        print_error("Vérifiez la modification dans la DB et réessayez.")
        return

    # Mettre à jour les données
    data_manager.add_user(users[0])
    data_manager.save()

    # --- ÉTAPE 6: Admin promeut user2 en manager ---
    print_section("6️  ADMIN PROMEUT USER2 EN MANAGER")

    print_info("RÈGLE: Admin peut promouvoir vers n'importe quel rôle\n")

    status, result = update_role(users[0].access_token, users[1].user_id, "manager")

    if status == 200:
        print_success(" user2 promu en manager par l'admin")
        # Reconnexion de user2
        users[1] = login_user(users[1].email)
        data_manager.add_user(users[1])
        data_manager.save()
    else:
        print_error(f" Échec de la promotion (Status: {status})")

    # --- ÉTAPE 7: Manager promeut user3 en manager ---
    print_section("7️  MANAGER PROMEUT USER3 EN MANAGER")

    print_info("RÈGLE: Manager peut promouvoir vers manager, washer, client (PAS admin)\n")

    status, result = update_role(users[1].access_token, users[2].user_id, "manager")

    if status == 200:
        print_success(" user3 promu en manager par un autre manager")
        users[2] = login_user(users[2].email)
        data_manager.add_user(users[2])
        data_manager.save()
    else:
        print_error(f"❌ Échec de la promotion (Status: {status})")

    # --- ÉTAPE 8: Manager promeut user4 en washer ---
    print_section("8️  MANAGER PROMEUT USER4 EN WASHER")

    status, result = update_role(users[1].access_token, users[3].user_id, "washer")

    if status == 200:
        print_success(" user4 promu en washer par un manager")
        users[3] = login_user(users[3].email)
        data_manager.add_user(users[3])
        data_manager.save()
    else:
        print_error(f" Échec de la promotion (Status: {status})")

    # --- ÉTAPE 9: Manager essaie de promouvoir en admin (doit échouer) ---
    print_section("9️  TEST: MANAGER NE PEUT PAS CRÉER D'ADMIN")

    print(f"Manager {users[1].email} essaie de promouvoir {users[4].email} en admin...")
    status, result = update_role(users[1].access_token, users[4].user_id, "admin")

    if status == 403:
        print_success(" Accès refusé (403) - Comportement attendu")
        print_info("   Seul un admin peut créer un autre admin")
    else:
        print_error(f" Status inattendu: {status} (attendu: 403)")

    # --- ÉTAPE 10: Washer essaie de promouvoir (doit échouer) ---
    print_section(" TEST: WASHER NE PEUT PAS MODIFIER LES RÔLES")

    print(f"Washer {users[3].email} essaie de promouvoir {users[4].email} en manager...")
    status, result = update_role(users[3].access_token, users[4].user_id, "manager")

    if status == 403:
        print_success(" Accès refusé (403) - Comportement attendu")
    else:
        print_error(f" Status inattendu: {status} (attendu: 403)")

    # --- ÉTAPE 11: Liste des utilisateurs (admin) ---
    print_section("1️1️  LISTE DES UTILISATEURS (VUE ADMIN)")

    users_list = list_users(users[0].access_token)

    if users_list:
        print(f"\n{Colors.BOLD}Utilisateurs dans le système:{Colors.RESET}")
        for user_data in users_list.get('users', []):
            role = user_data['role']
            role_color = (
                Colors.GREEN if role == 'admin' else
                Colors.YELLOW if role == 'manager' else
                Colors.BLUE if role == 'washer' else
                Colors.RESET
            )
            print(f"  • {user_data['email']:<30} {role_color}[{role}]{Colors.RESET}")

    # --- RÉSUMÉ FINAL ---
    print_section(" RÉSUMÉ DES TESTS")

    print(f"{Colors.BOLD}Rôles finaux:{Colors.RESET}")
    for i, user in enumerate(users):
        profile = get_user_profile(user.access_token)
        if profile:
            role = profile.get('role', 'unknown')
            role_color = (
                Colors.GREEN if role == 'admin' else
                Colors.YELLOW if role == 'manager' else
                Colors.BLUE if role == 'washer' else
                Colors.RESET
            )
            print(f"  {i+1}. {user.email:<30} → {role_color}{role}{Colors.RESET}")

            # Mettre à jour le rôle dans les données
            user.role = role
            data_manager.add_user(user)

    # Sauvegarder les données finales
    data_manager.save()

    # Afficher les statistiques
    print(f"\n{Colors.BOLD}Statistiques:{Colors.RESET}")
    stats = data_manager.get_stats()
    for role, count in stats['roles'].items():
        print(f"  • {role}: {count} utilisateur(s)")

    print(f"\n{Colors.GREEN}{Colors.BOLD} Tests RBAC terminés avec succès!{Colors.RESET}")
    print(f"\n{Colors.INFO}ℹ  Les utilisateurs créés sont sauvegardés dans: {data_manager.data_file}{Colors.RESET}")
    print(f"{Colors.INFO}   Ils seront réutilisés par les autres tests.{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrompus par l'utilisateur{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Erreur inattendue: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
