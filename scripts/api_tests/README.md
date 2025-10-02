# Scripts de Tests API - BlingAuto

Ce dossier contient des scripts Python pour tester les endpoints réels de l'API BlingAuto. Ces scripts permettent de simuler différents scénarios et valider le comportement de vos endpoints en conditions réelles.

## 🎯 Philosophie des Tests

**IMPORTANT**: Les scripts sont conçus pour **réutiliser les utilisateurs** créés lors du premier test. Cela reflète le comportement réel de votre application:

- ✅ **Tous les utilisateurs sont créés avec le rôle `client` par défaut** - Il est IMPOSSIBLE de créer directement un utilisateur avec un autre rôle
- ✅ **Seuls les admins/managers peuvent promouvoir des utilisateurs** - Les clients ne peuvent pas modifier les rôles
- ✅ **Les données sont partagées entre les tests** - Un utilisateur créé dans test_auth_rbac.py sera réutilisé par test_booking_workflow.py

## 📋 Prérequis

### 1. API en cours d'exécution

Assurez-vous que votre API est démarrée et accessible :

```bash
# Depuis le répertoire racine du projet
python main.py
```

L'API devrait être accessible sur `http://localhost:8000`

### 2. Base de données initialisée

Assurez-vous que votre base de données est configurée et les migrations appliquées.

### 3. Bibliothèque requests

Installez la bibliothèque `requests` si ce n'est pas déjà fait :

```bash
pip install requests
```

## 🚀 Démarrage Rapide

### Option 1: Exécuter tous les tests (recommandé)

```bash
python scripts/api_tests/run_all_tests.py
```

Ce script exécutera automatiquement tous les tests dans le bon ordre.

### Option 2: Exécuter les tests individuellement

**IMPORTANT**: Les tests doivent être exécutés dans cet ordre:

```bash
# 1️⃣ PREMIER: Créer les utilisateurs (OBLIGATOIRE)
python scripts/api_tests/test_auth_rbac.py

# 2️⃣ DEUXIÈME: Créer les services (utilise manager/admin)
python scripts/api_tests/test_services_management.py

# 3️⃣ TROISIÈME: Tester les réservations (utilise client et services)
python scripts/api_tests/test_booking_workflow.py
```

## 📁 Fichiers du Projet

### Scripts de Test

- **`test_auth_rbac.py`** - Tests d'authentification et RBAC (À exécuter EN PREMIER)
- **`test_services_management.py`** - Tests de gestion des services (utilise manager/admin existant)
- **`test_booking_workflow.py`** - Tests du workflow de réservation (utilise client existant)
- **`run_all_tests.py`** - Script pour exécuter tous les tests automatiquement

### Utilitaires

- **`utils.py`** - Fonctions partagées et gestion des données de test
- **`test_data.json`** - Fichier de persistance des utilisateurs de test (généré automatiquement)

## 🧪 Description Détaillée des Tests

### 1. `test_auth_rbac.py` - Authentification et RBAC ⭐ PREMIER

**Objectif**: Créer les utilisateurs de test et valider le système de contrôle d'accès

**Ce que le script teste**:
- ✅ Création de 6 utilisateurs (tous clients par défaut - RÈGLE STRICTE)
- ✅ Vérification que TOUS sont créés avec le rôle `client`
- ✅ Test: Un client NE PEUT PAS modifier les rôles (403)
- ✅ Promotion manuelle d'user1 en `admin` (via DB)
- ✅ Test: Admin peut promouvoir vers n'importe quel rôle
- ✅ Test: Manager peut promouvoir vers manager/washer (PAS admin)
- ✅ Test: Washer NE PEUT PAS modifier les rôles (403)
- ✅ Liste de tous les utilisateurs (vue admin)
- ✅ **Sauvegarde des utilisateurs** pour les tests suivants

**Règles validées**:
- 🔒 Impossible de créer un utilisateur avec un rôle spécifique lors de l'inscription
- 🔒 Seuls admin et manager peuvent modifier les rôles
- 🔒 Seul admin peut créer d'autres admins
- 🔒 Manager peut promouvoir vers manager, washer, client (PAS admin)

**Exécution**:
```bash
python scripts/api_tests/test_auth_rbac.py
```

**Note importante**: Nécessite une intervention manuelle pour promouvoir user1 en admin:

```sql
UPDATE users SET role = 'admin' WHERE id = '<user_id_affiché>';
```

**Résultats**: Les utilisateurs créés sont sauvegardés dans `test_data.json` et seront réutilisés par les autres tests.

---

### 2. `test_services_management.py` - Gestion des Services

**Objectif**: Créer les services qui seront utilisés pour les réservations

**Ce que le script teste**:
- ✅ **Utilise un manager/admin existant** (créé par test_auth_rbac.py)
- ✅ Création de catégories multiples
- ✅ Listing des catégories
- ✅ Création de services dans différentes catégories
- ✅ Listing de tous les services
- ✅ Récupération d'un service spécifique
- ✅ Mise à jour d'un service (prix, description)
- ✅ Récupération des services populaires
- ✅ Désactivation/Réactivation de services
- ✅ Listing avec services inactifs
- ✅ Suppression d'un service

**Prérequis**:
- ✅ `test_auth_rbac.py` exécuté
- ✅ Au moins un utilisateur manager ou admin disponible

**Exécution**:
```bash
python scripts/api_tests/test_services_management.py
```

---

### 3. `test_booking_workflow.py` - Workflow de Réservation

**Objectif**: Tester le cycle complet d'une réservation de lavage

**Ce que le script teste**:
- ✅ **Utilise un client existant** (créé par test_auth_rbac.py)
- ✅ Vérification des services disponibles (créés par test_services_management.py)
- ✅ Ajout d'un véhicule client
- ✅ Calcul d'un devis pour des services sélectionnés
- ✅ Création d'une réservation
- ✅ Récupération des détails de réservation
- ✅ Mise à jour du statut (avec vérification des permissions)
- ✅ Liste des réservations du client
- ✅ Annulation de réservation

**Règles validées**:
- 🔒 Un client peut créer une réservation pour lui-même
- 🔒 Un client peut annuler sa propre réservation
- 🔒 Seul admin/manager peut confirmer une réservation

**Prérequis**:
- ✅ `test_auth_rbac.py` exécuté (pour avoir un client)
- ✅ `test_services_management.py` exécuté (pour avoir des services)

**Exécution**:
```bash
python scripts/api_tests/test_booking_workflow.py
```

---

### 4. `run_all_tests.py` - Exécution Automatique

**Objectif**: Exécuter tous les tests dans le bon ordre automatiquement

**Options disponibles**:
```bash
# Exécuter tous les tests
python scripts/api_tests/run_all_tests.py

# Sauter les tests d'authentification (si déjà exécutés)
python scripts/api_tests/run_all_tests.py --skip-auth

# Nettoyer les données avant de commencer
python scripts/api_tests/run_all_tests.py --clean

# Sauter certains tests
python scripts/api_tests/run_all_tests.py --skip-services --skip-booking
```

---

## 🛠️ Utilitaires (`utils.py`)

Le module `utils.py` fournit des fonctions partagées:

### Gestion des Données de Test

```bash
# Afficher les statistiques
python scripts/api_tests/utils.py stats

# Lister tous les utilisateurs
python scripts/api_tests/utils.py list

# Effacer toutes les données de test
python scripts/api_tests/utils.py clear
```

### Classes et Fonctions Principales

- **`TestDataManager`**: Gère la persistance des données de test
- **`TestUser`**: Représente un utilisateur de test
- **`Colors`**: Codes couleur pour l'affichage
- **Fonctions d'affichage**: `print_success()`, `print_error()`, `print_warning()`, `print_info()`
- **`check_prerequisites()`**: Vérifie que l'API est accessible

## 🎨 Codes Couleur dans les Résultats

Les scripts utilisent des codes couleur pour faciliter la lecture:

- 🟢 **Vert** : Succès / Opération réussie
- 🔴 **Rouge** : Erreur / Échec
- 🟡 **Jaune** : Avertissement / Information importante
- 🔵 **Bleu** : Information générale
- 🟣 **Magenta/Cyan** : Titres de sections

## 📊 Exemple de Sortie

```
======================================================================
🔐 TEST RBAC - GESTION DES RÔLES ET PERMISSIONS
======================================================================

======================================================================
1️⃣  CRÉATION DE 6 UTILISATEURS (TOUS CLIENT PAR DÉFAUT)
======================================================================

ℹ RÈGLE: Tous les utilisateurs sont créés avec le rôle 'client'
ℹ        Il est IMPOSSIBLE de spécifier un rôle lors de l'inscription

✓ Utilisateur créé: user1@test.com (ID: abc123...)
✓ Utilisateur créé: user2@test.com (ID: def456...)
...

======================================================================
3️⃣  VÉRIFICATION DES RÔLES PAR DÉFAUT
======================================================================

✓ user1@test.com → Rôle: client ✓
✓ user2@test.com → Rôle: client ✓
...

✅ TOUS les utilisateurs créés avec le rôle 'client' par défaut
```

## 🔧 Personnalisation

### Modifier l'URL de base

Si votre API tourne sur un port différent, modifiez dans `utils.py`:

```python
BASE_URL = "http://localhost:8000/api/v1"  # Modifiez ici
```

### Ajouter vos propres tests

1. Créez un fichier `test_<feature>.py`
2. Importez les utilitaires: `from utils import ...`
3. Utilisez `TestDataManager` pour récupérer les utilisateurs existants
4. Suivez la structure des scripts existants

Exemple:

```python
from utils import (
    TestDataManager, login_existing_user,
    print_section, print_success, print_error
)

def main():
    # Récupérer un utilisateur existant
    data_manager = TestDataManager()
    client = data_manager.get_user_by_role("client")

    # Se connecter
    client = login_existing_user(client)

    # Vos tests ici...
```

## 🐛 Débogage

### 1. Vérifier que l'API est démarrée

```bash
curl http://localhost:8000/health
```

### 2. Consulter les logs de l'API

Les messages d'erreur détaillés apparaissent dans les logs de votre API.

### 3. Vérifier les données de test

```bash
python scripts/api_tests/utils.py list
```

### 4. Nettoyer et recommencer

```bash
python scripts/api_tests/utils.py clear
python scripts/api_tests/run_all_tests.py
```

### 5. Tester un endpoint manuellement

```bash
# Exemple: inscription
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Passw0rd!","first_name":"Test","last_name":"User","phone_number":"+1234567890"}'
```

## 📝 Workflow Recommandé

### Première Exécution

```bash
# 1. Démarrer l'API
python main.py

# 2. Dans un autre terminal, exécuter les tests
cd scripts/api_tests

# 3. Exécuter tous les tests
python run_all_tests.py

# 4. Suivre les instructions (promotion admin dans la DB)

# 5. Vérifier les statistiques
python utils.py stats
```

### Exécutions Suivantes

```bash
# Si les utilisateurs existent déjà
python run_all_tests.py --skip-auth

# Ou exécuter un test spécifique
python test_booking_workflow.py
```

### Nettoyage

```bash
# Effacer toutes les données de test
python utils.py clear

# Recommencer from scratch
python run_all_tests.py
```

## ⚠️ Règles Importantes

### À FAIRE ✅

- ✅ Exécuter `test_auth_rbac.py` EN PREMIER
- ✅ Utiliser les utilisateurs existants dans les tests suivants
- ✅ Respecter les permissions (admin > manager > washer > client)
- ✅ Vérifier les prérequis avant chaque test
- ✅ Consulter les logs en cas d'erreur

### À NE PAS FAIRE ❌

- ❌ Créer de nouveaux utilisateurs dans chaque test
- ❌ Essayer de créer un utilisateur avec un rôle spécifique lors de l'inscription
- ❌ Exécuter les tests sur une base de données de production
- ❌ Modifier manuellement le fichier `test_data.json`
- ❌ Sauter `test_auth_rbac.py` si aucun utilisateur n'existe

## 📚 Documentation API

Pour plus d'informations sur les endpoints:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contribuer

Pour ajouter un nouveau script:

1. Créez `test_<feature>.py` dans ce dossier
2. Importez et utilisez les utilitaires de `utils.py`
3. Réutilisez les utilisateurs existants via `TestDataManager`
4. Ajoutez la documentation dans ce README
5. Mettez à jour `run_all_tests.py` si nécessaire

## 📞 Support

En cas de problème:

1. Vérifiez les prérequis
2. Consultez les logs de l'API
3. Utilisez `python utils.py stats` pour diagnostiquer
4. Consultez la documentation Swagger
5. Ouvrez une issue avec:
   - La commande exécutée
   - Les logs d'erreur
   - Les statistiques (`utils.py stats`)

---

**Dernière mise à jour**: 2025-01-02
**Version**: 2.0 - Avec partage d'utilisateurs entre tests
