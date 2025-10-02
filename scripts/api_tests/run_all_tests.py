"""
Script d'exécution de tous les tests API dans le bon ordre

Ce script exécute automatiquement tous les tests dans l'ordre correct:
1. test_auth_rbac.py - Création et gestion des utilisateurs (DOIT être exécuté en premier)
2. test_services_management.py - Création et gestion des services (utilise manager/admin)
3. test_booking_workflow.py - Workflow de réservation (utilise client et services)

Usage:
    python scripts/api_tests/run_all_tests.py [options]

Options:
    --skip-auth        : Sauter les tests d'authentification (si déjà exécutés)
    --skip-services    : Sauter les tests de gestion des services
    --skip-booking     : Sauter les tests de réservation
    --clean           : Nettoyer les données de test avant de commencer
"""

import subprocess
import sys
import os
from pathlib import Path

# Import des utilitaires
from utils import (
    TestDataManager,
    print_section, print_success, print_error, print_warning, print_info,
    Colors, check_prerequisites, print_test_data_stats
)


def run_test_script(script_name: str, description: str) -> bool:
    """Exécute un script de test et retourne True si succès."""
    print_section(f" EXÉCUTION: {description}")

    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        print_error(f"Script introuvable: {script_path}")
        return False

    print_info(f"Lancement de {script_name}...\n")

    try:
        # Exécuter le script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent,
            check=False,
            capture_output=False  # Afficher la sortie en temps réel
        )

        if result.returncode == 0:
            print_success(f"\n {description} terminé avec succès!\n")
            return True
        else:
            print_error(f"\n {description} a échoué (code: {result.returncode})\n")
            return False

    except KeyboardInterrupt:
        print_warning(f"\n  Test interrompu par l'utilisateur\n")
        return False
    except Exception as e:
        print_error(f"\n Erreur lors de l'exécution: {e}\n")
        return False


def parse_arguments():
    """Parse les arguments de la ligne de commande."""
    args = {
        'skip_auth': '--skip-auth' in sys.argv,
        'skip_services': '--skip-services' in sys.argv,
        'skip_booking': '--skip-booking' in sys.argv,
        'clean': '--clean' in sys.argv,
    }
    return args


def main():
    """Fonction principale."""

    print_section(" EXÉCUTION COMPLÈTE DES TESTS API")

    # Parser les arguments
    args = parse_arguments()

    # Vérifier les prérequis
    print_section(" VÉRIFICATION DES PRÉREQUIS")

    if not check_prerequisites():
        print_error("\n Prérequis non satisfaits. Impossible de continuer.")
        print_info("\nAssurez-vous que:")
        print_info("  1. L'API est démarrée (python main.py)")
        print_info("  2. La base de données est accessible")
        return 1

    # Gérer le nettoyage si demandé
    if args['clean']:
        print_section("🧹 NETTOYAGE DES DONNÉES DE TEST")

        data_manager = TestDataManager()
        response = input(f"{Colors.YELLOW}  Voulez-vous vraiment effacer toutes les données de test? (y/N): {Colors.RESET}")

        if response.lower() == 'y':
            data_manager.clear_all()
            print_success("Données de test effacées")
        else:
            print_info("Nettoyage annulé")

    # Afficher les statistiques initiales
    print_test_data_stats()

    # Liste des tests à exécuter
    tests = []

    if not args['skip_auth']:
        tests.append(('test_auth_rbac.py', 'Tests RBAC et gestion des rôles'))

    if not args['skip_services']:
        tests.append(('test_services_management.py', 'Tests de gestion des services'))

    if not args['skip_booking']:
        tests.append(('test_booking_workflow.py', 'Tests du workflow de réservation'))

    if not tests:
        print_warning("Tous les tests ont été sautés!")
        print_info("Utilisez --help pour voir les options disponibles")
        return 0

    # Exécuter les tests
    print_section(f" PLAN D'EXÉCUTION ({len(tests)} test(s))")

    for i, (script, desc) in enumerate(tests, 1):
        print(f"  {i}. {desc} ({script})")

    print()
    input(f"{Colors.BOLD}Appuyez sur Entrée pour démarrer les tests...{Colors.RESET}")

    results = []
    for script, description in tests:
        success = run_test_script(script, description)
        results.append((description, success))

        if not success:
            print_error(f"Le test '{description}' a échoué.")
            response = input(f"{Colors.YELLOW}Voulez-vous continuer avec les tests suivants? (y/N): {Colors.RESET}")

            if response.lower() != 'y':
                print_warning("Arrêt de l'exécution des tests")
                break

    # Résumé final
    print_section(" RÉSUMÉ FINAL")

    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed

    print(f"{Colors.BOLD}Résultats:{Colors.RESET}")
    for description, success in results:
        status = f"{Colors.GREEN}✓ RÉUSSI{Colors.RESET}" if success else f"{Colors.RED}✗ ÉCHEC{Colors.RESET}"
        print(f"  • {description:<50} {status}")

    print(f"\n{Colors.BOLD}Statistiques:{Colors.RESET}")
    print(f"  Total: {total}")
    print(f"  {Colors.GREEN}Réussis: {passed}{Colors.RESET}")
    if failed > 0:
        print(f"  {Colors.RED}Échoués: {failed}{Colors.RESET}")

    # Afficher les statistiques finales
    print_test_data_stats()

    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD} TOUS LES TESTS ONT RÉUSSI!{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}  Certains tests ont échoué{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}  Exécution interrompue par l'utilisateur{Colors.RESET}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED} Erreur inattendue: {e}{Colors.RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
