"""
Utilitaires partagés pour les tests API

Ce module fournit:
- Gestion centralisée des utilisateurs de test
- Fonctions communes pour l'authentification
- Utilitaires d'affichage
- Gestion de la persistence des données de test
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = f"{BASE_URL}/auth"
SERVICES_URL = f"{BASE_URL}/services"
VEHICLES_URL = f"{BASE_URL}/vehicles"
BOOKINGS_URL = f"{BASE_URL}/bookings"
PRICING_URL = f"{BASE_URL}/pricing"

# Fichier de persistence des données de test
TEST_DATA_FILE = Path(__file__).parent / "test_data.json"


@dataclass
class TestUser:
    """Représente un utilisateur de test avec ses credentials."""
    email: str
    password: str
    user_id: Optional[str] = None
    role: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire (sans les tokens)."""
        data = asdict(self)
        # Ne pas sauvegarder les tokens (ils expirent)
        data.pop('access_token', None)
        data.pop('refresh_token', None)
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'TestUser':
        """Crée une instance depuis un dictionnaire."""
        return cls(**data)


class Colors:
    """Codes ANSI pour la couleur dans le terminal."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Affiche un titre de section."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")


def print_success(message: str):
    """Affiche un message de succès."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Affiche un message d'erreur."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    """Affiche une information."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_warning(message: str):
    """Affiche un avertissement."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


class TestDataManager:
    """Gestionnaire des données de test persistées."""

    def __init__(self, data_file: Path = TEST_DATA_FILE):
        self.data_file = data_file
        self._data = self._load()

    def _load(self) -> Dict:
        """Charge les données depuis le fichier."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print_warning(f"Erreur lors du chargement des données: {e}")
                return self._default_data()
        return self._default_data()

    def _default_data(self) -> Dict:
        """Retourne la structure de données par défaut."""
        return {
            "users": [],
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }

    def save(self):
        """Sauvegarde les données dans le fichier."""
        self._data["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            print_success(f"Données sauvegardées: {self.data_file}")
        except Exception as e:
            print_error(f"Erreur lors de la sauvegarde: {e}")

    def add_user(self, user: TestUser):
        """Ajoute ou met à jour un utilisateur."""
        # Vérifier si l'utilisateur existe déjà
        for i, existing_user in enumerate(self._data["users"]):
            if existing_user.get("email") == user.email:
                self._data["users"][i] = user.to_dict()
                print_info(f"Utilisateur mis à jour: {user.email}")
                return

        # Ajouter le nouvel utilisateur
        self._data["users"].append(user.to_dict())
        print_info(f"Utilisateur ajouté: {user.email}")

    def get_user_by_email(self, email: str) -> Optional[TestUser]:
        """Récupère un utilisateur par email."""
        for user_data in self._data["users"]:
            if user_data.get("email") == email:
                return TestUser.from_dict(user_data)
        return None

    def get_user_by_role(self, role: str) -> Optional[TestUser]:
        """Récupère le premier utilisateur avec ce rôle."""
        for user_data in self._data["users"]:
            if user_data.get("role") == role:
                return TestUser.from_dict(user_data)
        return None

    def get_all_users(self) -> List[TestUser]:
        """Récupère tous les utilisateurs."""
        return [TestUser.from_dict(u) for u in self._data["users"]]

    def get_users_by_role(self, role: str) -> List[TestUser]:
        """Récupère tous les utilisateurs avec ce rôle."""
        return [
            TestUser.from_dict(u)
            for u in self._data["users"]
            if u.get("role") == role
        ]

    def user_exists(self, email: str) -> bool:
        """Vérifie si un utilisateur existe."""
        return any(u.get("email") == email for u in self._data["users"])

    def clear_all(self):
        """Efface toutes les données de test."""
        self._data = self._default_data()
        self.save()
        print_warning("Toutes les données de test ont été effacées")

    def get_stats(self) -> Dict:
        """Retourne des statistiques sur les données de test."""
        users = self._data.get("users", [])
        role_counts = {}
        for user in users:
            role = user.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        return {
            "total_users": len(users),
            "roles": role_counts,
            "created_at": self._data.get("created_at"),
            "last_updated": self._data.get("last_updated")
        }


def print_test_data_stats():
    """Affiche les statistiques des données de test."""
    manager = TestDataManager()
    stats = manager.get_stats()

    print_section(" STATISTIQUES DES DONNÉES DE TEST")
    print(f"{Colors.BOLD}Total utilisateurs:{Colors.RESET} {stats['total_users']}")

    if stats['roles']:
        print(f"\n{Colors.BOLD}Répartition par rôle:{Colors.RESET}")
        for role, count in stats['roles'].items():
            print(f"  • {role}: {count}")

    print(f"\n{Colors.BOLD}Créé le:{Colors.RESET} {stats.get('created_at', 'N/A')}")
    print(f"{Colors.BOLD}Dernière mise à jour:{Colors.RESET} {stats.get('last_updated', 'N/A')}")
    print()


def check_prerequisites() -> bool:
    """Vérifie que les prérequis sont remplis."""
    import requests

    print_section(" VÉRIFICATION DES PRÉREQUIS")

    # Vérifier que l'API est accessible
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code == 200:
            print_success("API accessible")
        else:
            print_error(f"API répond avec le code {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Impossible de contacter l'API: {e}")
        print_info("Assurez-vous que l'API est démarrée sur http://localhost:8000")
        return False

    # Vérifier que les données de test existent (sauf pour le premier test)
    manager = TestDataManager()
    users = manager.get_all_users()

    if users:
        print_success(f"{len(users)} utilisateur(s) de test trouvé(s)")
    else:
        print_warning("Aucun utilisateur de test trouvé")
        print_info("Exécutez d'abord: python scripts/api_tests/test_auth_rbac.py")

    return True


if __name__ == "__main__":
    """Script utilitaire pour gérer les données de test."""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "stats":
            print_test_data_stats()

        elif command == "clear":
            response = input("  Voulez-vous vraiment effacer toutes les données de test? (y/N): ")
            if response.lower() == 'y':
                TestDataManager().clear_all()
            else:
                print_info("Annulé")

        elif command == "list":
            manager = TestDataManager()
            users = manager.get_all_users()

            print_section("👥 UTILISATEURS DE TEST")
            if users:
                for user in users:
                    role_color = (
                        Colors.GREEN if user.role == 'admin' else
                        Colors.YELLOW if user.role == 'manager' else
                        Colors.BLUE if user.role == 'washer' else
                        Colors.RESET
                    )
                    print(f"  • {user.email:<30} {role_color}[{user.role or 'N/A'}]{Colors.RESET} (ID: {user.user_id or 'N/A'})")
            else:
                print_info("Aucun utilisateur de test trouvé")

        else:
            print(f"Commande inconnue: {command}")
            print("\nCommandes disponibles:")
            print("  stats  - Afficher les statistiques")
            print("  list   - Lister tous les utilisateurs")
            print("  clear  - Effacer toutes les données de test")

    else:
        print("Utilitaire de gestion des données de test")
        print("\nUsage: python utils.py [command]")
        print("\nCommandes:")
        print("  stats  - Afficher les statistiques")
        print("  list   - Lister tous les utilisateurs")
        print("  clear  - Effacer toutes les données de test")
