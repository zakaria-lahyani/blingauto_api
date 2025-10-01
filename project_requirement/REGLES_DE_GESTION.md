# Système de Gestion de Lavage Auto - Règles de Gestion

## 1. Introduction

Ce document décrit l'ensemble des règles de gestion métier implémentées dans le système de gestion de lavage automobile BlingAuto API. Ces règles garantissent la cohérence des données, l'intégrité métier et la sécurité du système.

---

## 2. Gestion des Utilisateurs et Authentification

### 2.1 Inscription et Validation des Utilisateurs

#### RG-AUTH-001 : Validation de l'email
- **Règle** : L'adresse email doit être unique dans le système
- **Format** : Doit contenir le caractère "@" et respecter le format email standard
- **Longueur** : Maximum 255 caractères
- **Implémentation** : `src/features/auth/domain/entities.py:88-93`

#### RG-AUTH-002 : Validation du mot de passe
- **Longueur minimale** : 8 caractères minimum
- **Longueur maximale** : 128 caractères maximum
- **Exigences de sécurité** : Validation selon les critères de sécurité configurés
- **Implémentation** : `src/shared/utils/validation.py`

#### RG-AUTH-003 : Validation des noms
- **Prénom** : Obligatoire, 1-100 caractères, ne peut pas être vide
- **Nom** : Obligatoire, 1-100 caractères, ne peut pas être vide
- **Normalisation** : Suppression des espaces en début/fin, application de la casse titre
- **Implémentation** : `src/features/auth/domain/entities.py:95-103`

#### RG-AUTH-004 : Validation du téléphone
- **Format** : Validation selon les standards internationaux
- **Longueur** : Maximum 20 caractères
- **Caractère optionnel** : Le numéro de téléphone n'est pas obligatoire
- **Implémentation** : `src/features/auth/presentation/api/schemas.py:52-58`

### 2.2 Gestion des Sessions et Sécurité

#### RG-AUTH-005 : Gestion des tokens JWT
- **Token d'accès** : Durée de vie de 15 minutes
- **Token de rafraîchissement** : Durée de vie de 7 jours avec rotation automatique
- **Révocation** : Possibilité de révoquer tous les tokens d'un utilisateur

#### RG-AUTH-006 : Verrouillage de compte
- **Tentatives échouées** : Maximum 5 tentatives de connexion échouées
- **Durée de verrouillage** : Augmente progressivement avec les violations répétées
- **Période de grâce** : 30 minutes après la dernière tentative échouée
- **Implémentation** : `src/features/auth/domain/entities.py:174-198`

#### RG-AUTH-007 : Vérification email
- **Obligatoire** : Compte inactif jusqu'à vérification email
- **Token de vérification** : Expire après 24 heures
- **Renouvelable** : Possibilité de renvoyer l'email de vérification

#### RG-AUTH-008 : Réinitialisation mot de passe
- **Token de réinitialisation** : Expire après 1 heure
- **Usage unique** : Le token ne peut être utilisé qu'une seule fois
- **Sécurité** : Token cryptographiquement sécurisé

### 2.3 Rôles et Permissions

#### RG-AUTH-009 : Hiérarchie des rôles
- **Admin** : Accès complet au système
- **Manager** : Gestion des opérations et du personnel
- **Washer** : Accès aux réservations assignées
- **Client** : Accès aux fonctions client uniquement

#### RG-AUTH-010 : Contrôle d'accès basé sur les rôles (RBAC)
- **Principe** : Chaque endpoint vérifie les permissions requises
- **Héritage** : Les rôles supérieurs héritent des permissions inférieures
- **Séparation** : Les clients ne peuvent accéder qu'à leurs propres données

---

## 3. Gestion des Véhicules

### 3.1 Enregistrement des Véhicules

#### RG-VEH-001 : Validation de la marque
- **Longueur** : Minimum 2 caractères, maximum 50 caractères
- **Format** : Normalisation en casse titre
- **Implémentation** : `src/features/vehicles/domain/entities.py:56-61`

#### RG-VEH-002 : Validation du modèle
- **Longueur** : Minimum 1 caractère, maximum 50 caractères
- **Obligatoire** : Le modèle ne peut pas être vide
- **Format** : Normalisation en casse titre
- **Implémentation** : `src/features/vehicles/domain/entities.py:63-68`

#### RG-VEH-003 : Validation de l'année
- **Année minimale** : 1900
- **Année maximale** : Année courante + 2 ans
- **Logique** : Permet les véhicules futurs avec une limite raisonnable
- **Implémentation** : `src/features/vehicles/domain/entities.py:70-76`

#### RG-VEH-004 : Validation de la couleur
- **Longueur** : Minimum 2 caractères, maximum 30 caractères
- **Format** : Normalisation en casse titre
- **Implémentation** : `src/features/vehicles/domain/entities.py:78-83`

#### RG-VEH-005 : Validation de la plaque d'immatriculation
- **Longueur** : Minimum 2 caractères, maximum 20 caractères
- **Format** : Conversion en majuscules
- **Unicité** : Doit être unique par utilisateur (recommandé)
- **Implémentation** : `src/features/vehicles/domain/entities.py:85-90`

### 3.2 Gestion des Véhicules

#### RG-VEH-006 : Véhicule par défaut
- **Unicité** : Un seul véhicule par défaut par utilisateur
- **Obligation** : Définition automatique si premier véhicule
- **Transfert** : Changement de véhicule par défaut possible

#### RG-VEH-007 : Suppression des véhicules
- **Suppression douce** : Les véhicules sont marqués comme supprimés, pas physiquement effacés
- **Contrainte** : Le véhicule par défaut ne peut pas être supprimé s'il y a des réservations actives
- **Historique** : Conservation de l'historique des réservations

---

## 4. Gestion des Services et Catégories

### 4.1 Catégories de Services

#### RG-SVC-001 : Validation du nom de catégorie
- **Longueur** : Maximum 100 caractères
- **Unicité** : Les noms de catégories doivent être uniques
- **Obligatoire** : Le nom ne peut pas être vide
- **Implémentation** : `src/features/services/domain/entities.py:37-42`

#### RG-SVC-002 : Statut des catégories
- **États possibles** : ACTIVE, INACTIVE
- **Suppression** : Les catégories ne peuvent pas être supprimées si elles contiennent des services
- **Désactivation** : Alternative à la suppression pour préserver l'intégrité

### 4.2 Services

#### RG-SVC-003 : Validation du nom de service
- **Longueur** : Maximum 100 caractères
- **Unicité** : Les noms doivent être uniques dans une catégorie
- **Obligatoire** : Le nom ne peut pas être vide
- **Implémentation** : `src/features/services/domain/entities.py:119-124`

#### RG-SVC-004 : Validation du prix
- **Valeur minimale** : Doit être positif (> 0)
- **Type** : Utilisation de Decimal pour la précision financière
- **Implémentation** : `src/features/services/domain/entities.py:126-129`

#### RG-SVC-005 : Validation de la durée
- **Valeur minimale** : Doit être positive (> 0)
- **Unité** : Exprimée en minutes
- **Implémentation** : `src/features/services/domain/entities.py:131-134`

#### RG-SVC-006 : Gestion des services populaires
- **Marquage** : Les services peuvent être marqués comme populaires
- **Affichage** : Utilisé pour la mise en avant dans l'interface
- **Gestion** : Contrôlé par les administrateurs/managers

---

## 5. Gestion des Réservations

### 5.1 Création et Validation des Réservations

#### RG-BOK-001 : Contraintes sur les services
- **Minimum** : 1 service obligatoire par réservation
- **Maximum** : 10 services maximum par réservation
- **Unicité** : Pas de services dupliqués dans une même réservation
- **Implémentation** : `src/features/bookings/domain/entities.py:67-68, 167-176`

#### RG-BOK-002 : Contraintes de durée
- **Durée minimale** : 30 minutes par réservation
- **Durée maximale** : 240 minutes (4 heures) par réservation
- **Calcul** : Somme des durées de tous les services sélectionnés
- **Implémentation** : `src/features/bookings/domain/entities.py:69-70, 196-204`

#### RG-BOK-003 : Contraintes de prix
- **Prix minimum** : 0.00€
- **Prix maximum** : 10 000.00€
- **Calcul** : Somme des prix de tous les services sélectionnés
- **Type** : Utilisation de Decimal pour la précision
- **Implémentation** : `src/features/bookings/domain/entities.py:71-72, 206-210`

#### RG-BOK-004 : Contraintes temporelles
- **Réservation passée** : Interdite de programmer dans le passé
- **Réservation future** : Maximum 90 jours à l'avance
- **Validation** : Utilisation de la comparaison timezone-aware
- **Implémentation** : `src/features/bookings/domain/entities.py:73, 178-192`

### 5.2 Types de Réservations

#### RG-BOK-005 : Réservations mobiles
- **Localisation obligatoire** : Coordonnées GPS requises (lat, lng)
- **Format** : Dictionnaire avec clés 'lat' et 'lng'
- **Validation** : Vérification du format et des types de données
- **Implémentation** : `src/features/bookings/domain/entities.py:140-150`

#### RG-BOK-006 : Réservations stationnaires (sur site)
- **Localisation** : Pas de coordonnées client requises
- **Ressource** : Utilise les baies de lavage du centre
- **Accès** : Client se rend au centre de lavage

#### RG-BOK-007 : Tailles de véhicules
- **Types supportés** : compact, standard, large, oversized
- **Validation** : Vérification contre la liste des tailles valides
- **Contrainte** : Doit correspondre aux capacités des ressources
- **Implémentation** : `src/features/bookings/domain/entities.py:157-160`

### 5.3 Cycle de Vie des Réservations

#### RG-BOK-008 : États des réservations
- **PENDING** : Création initiale, modifications autorisées
- **CONFIRMED** : Réservation confirmée, modifications limitées
- **IN_PROGRESS** : Service en cours, suivi des temps réels
- **COMPLETED** : Service terminé, évaluation possible
- **CANCELLED** : Réservation annulée avec frais éventuels
- **NO_SHOW** : Client absent, frais complets appliqués

#### RG-BOK-009 : Transitions d'états
- **Progression uniquement** : Les états ne peuvent que progresser
- **Exceptions** : Annulation possible depuis PENDING et CONFIRMED
- **Validation** : Vérification de l'état actuel avant transition

### 5.4 Politique d'Annulation

#### RG-BOK-010 : Frais d'annulation basés sur le préavis
- **Plus de 24h** : Annulation gratuite (0%)
- **6-24h** : 25% du prix total
- **2-6h** : 50% du prix total
- **Moins de 2h** : 100% du prix total
- **Implémentation** : `src/features/bookings/domain/entities.py:343-354`

#### RG-BOK-011 : Gestion des non-présentations
- **Période de grâce** : 30 minutes après l'heure prévue
- **Frais** : 100% du prix total pour non-présentation
- **Statut** : Changement automatique vers NO_SHOW
- **Implémentation** : `src/features/bookings/domain/entities.py:372-379`

### 5.5 Reprogrammation

#### RG-BOK-012 : Contraintes de reprogrammation
- **Préavis minimum** : 2 heures avant la nouvelle heure
- **États autorisés** : PENDING et CONFIRMED uniquement
- **Validation** : Vérification de disponibilité pour le nouveau créneau
- **Implémentation** : `src/features/bookings/domain/entities.py:277-296`

### 5.6 Modifications des Services

#### RG-BOK-013 : Ajout de services
- **État requis** : PENDING uniquement
- **Limite** : Respect de la limite de 10 services maximum
- **Validation** : Recalcul automatique du prix et de la durée
- **Implémentation** : `src/features/bookings/domain/entities.py:309-324`

#### RG-BOK-014 : Suppression de services
- **État requis** : PENDING uniquement
- **Minimum** : Au moins 1 service doit rester
- **Validation** : Recalcul automatique du prix et de la durée
- **Implémentation** : `src/features/bookings/domain/entities.py:326-341`

### 5.7 Suivi des Heures et Frais Supplémentaires

#### RG-BOK-015 : Heures supplémentaires
- **Taux** : 1.00€ par minute de dépassement
- **Calcul** : Basé sur la différence entre temps réel et temps prévu
- **Application** : Uniquement si le service dépasse la durée prévue
- **Implémentation** : `src/features/bookings/domain/entities.py:385-397`

### 5.8 Évaluation de la Qualité

#### RG-BOK-016 : Système d'évaluation
- **Échelle** : 1 à 5 étoiles
- **Disponibilité** : Uniquement après achèvement du service
- **Unicité** : Une seule évaluation par réservation
- **Commentaire** : Optionnel, maximum 1000 caractères
- **Implémentation** : `src/features/bookings/domain/entities.py:298-307`

---

## 6. Gestion des Ressources et Planification

### 6.1 Baies de Lavage

#### RG-FAC-001 : Configuration des baies
- **Numérotation** : Chaque baie a un numéro unique
- **Taille de véhicule** : Capacité maximale définie (compact à oversized)
- **Équipements** : Liste des types d'équipements disponibles
- **État** : Actif/Inactif pour maintenance

#### RG-FAC-002 : Compatibilité des véhicules
- **Hiérarchie des tailles** : compact < standard < large < oversized
- **Règle** : Une baie peut accueillir sa taille maximale et toutes les tailles inférieures
- **Implémentation** : `src/features/scheduling/domain/wash_facility_entities.py:53-58`

### 6.2 Équipes Mobiles

#### RG-FAC-003 : Configuration des équipes mobiles
- **Rayon de service** : Périmètre géographique défini (défaut: 50km)
- **Capacité journalière** : Maximum 8 véhicules par jour par équipe
- **Équipements** : Liste des équipements transportés
- **Localisation de base** : Point de départ pour les calculs de distance

#### RG-FAC-004 : Calcul de distance de service
- **Méthode** : Calcul approximatif basé sur les coordonnées GPS
- **Limitation** : Service uniquement dans le rayon défini
- **Optimisation** : Priorité aux équipes les plus proches
- **Implémentation** : `src/features/scheduling/domain/wash_facility_entities.py:106-122`

### 6.3 Horaires d'Ouverture

#### RG-SCH-001 : Configuration des horaires
- **Par jour** : Horaires spécifiques pour chaque jour de la semaine
- **Périodes de pause** : Définition des créneaux indisponibles
- **Fermetures** : Jours de fermeture complète
- **Créneaux** : Durée par défaut de 30 minutes

#### RG-SCH-002 : Contraintes de planification
- **Tampon** : 15 minutes entre les réservations
- **Réservation anticipée** : Minimum 2 heures à l'avance
- **Réservation le jour même** : Autorisée selon configuration
- **Maximum à l'avance** : 90 jours maximum

### 6.4 Gestion de la Capacité

#### RG-CAP-001 : Allocation des créneaux
- **Principe** : Un créneau par ressource et par période
- **Conflits** : Détection automatique des conflits de planification
- **Libération** : Libération automatique en cas d'annulation

#### RG-CAP-002 : Suggestions d'alternatives
- **Stratégies** : Plus tôt disponible, préférences utilisateur
- **Facteurs** : Jour préféré, créneaux horaires préférés
- **Contraintes** : Évitement des périodes non souhaitées

---

## 7. Sécurité et Validation des Données

### 7.1 Validation des Entrées

#### RG-SEC-001 : Sanitisation des données
- **Texte** : Suppression des espaces en début/fin
- **HTML** : Protection contre XSS
- **SQL** : Protection contre injection SQL via ORM
- **Longueurs** : Respect des limites de champs

#### RG-SEC-002 : Format des données
- **Email** : Validation du format standard
- **Téléphone** : Validation selon standards internationaux
- **UUID** : Validation du format UUID pour les identifiants
- **Dates** : Gestion timezone-aware obligatoire

### 7.2 Contrôle d'Accès

#### RG-SEC-003 : Principe de moindre privilège
- **Accès minimum** : Chaque rôle a le minimum de permissions nécessaires
- **Séparation** : Isolation des données entre clients
- **Audit** : Traçabilité des actions effectuées

#### RG-SEC-004 : Protection des données sensibles
- **Mots de passe** : Hachage avec bcrypt
- **Tokens** : Stockage sécurisé et chiffré
- **Données personnelles** : Limitation de l'accès et de l'exposition

### 7.3 Limitation du Taux de Requêtes

#### RG-SEC-005 : Rate limiting
- **Par IP** : Limitation des requêtes par adresse IP
- **Par utilisateur** : Limitation des requêtes par compte utilisateur
- **Par endpoint** : Limites spécifiques selon la sensibilité
- **Escalade** : Verrouillage temporaire en cas d'abus

---

## 8. Règles de Cohérence et d'Intégrité

### 8.1 Intégrité Référentielle

#### RG-INT-001 : Clés étrangères
- **Contraintes** : Toutes les relations sont protégées par des contraintes
- **Suppression en cascade** : Définition claire des comportements
- **Suppression douce** : Préférence pour le marquage vs suppression physique

#### RG-INT-002 : Unicité des données
- **Emails** : Uniques dans tout le système
- **Plaques d'immatriculation** : Uniques par utilisateur
- **Tokens** : Génération cryptographiquement sécurisée

### 8.2 Cohérence Temporelle

#### RG-TMP-001 : Gestion des fuseaux horaires
- **Standard** : Utilisation d'UTC en interne
- **Conversion** : Conversion locale pour l'affichage
- **Validation** : Comparaisons timezone-aware obligatoires

#### RG-TMP-002 : Timestamps automatiques
- **Création** : created_at automatique à la création
- **Modification** : updated_at automatique à chaque modification
- **Traçabilité** : Conservation de l'historique des modifications

### 8.3 Validation Métier

#### RG-BIZ-001 : Règles métier transversales
- **Disponibilité** : Vérification en temps réel avant confirmation
- **Capacité** : Respect des limites de ressources
- **Conflits** : Détection et résolution des conflits de planification

#### RG-BIZ-002 : États cohérents
- **Progression** : Les transitions d'état suivent la logique métier
- **Validation** : Vérification des prérequis avant chaque transition
- **Rollback** : Possibilité d'annuler les opérations en cas d'erreur

---

## 9. Gestion des Erreurs et Exceptions

### 9.1 Classification des Erreurs

#### RG-ERR-001 : Types d'erreurs standardisés
- **400 - Validation** : Erreurs de validation des données d'entrée
- **401 - Authentification** : Problèmes d'authentification
- **403 - Autorisation** : Permissions insuffisantes
- **404 - Ressource** : Ressource non trouvée
- **422 - Logique métier** : Violation des règles métier
- **429 - Rate limiting** : Trop de requêtes
- **500 - Serveur** : Erreurs internes du système

### 9.2 Format des Réponses d'Erreur

#### RG-ERR-002 : Standardisation des erreurs
- **Format** : Structure JSON cohérente
- **Détails** : Informations sur le champ et le type d'erreur
- **Traçabilité** : ID de requête pour le debugging
- **Sécurité** : Pas d'exposition d'informations sensibles

---

## 10. Performance et Scalabilité

### 10.1 Contraintes de Performance

#### RG-PERF-001 : Temps de réponse
- **API** : 95e percentile < 200ms
- **Timeout** : 120 secondes par défaut pour les opérations longues
- **Pagination** : Limitation des résultats (défaut: 20, max: 100)

#### RG-PERF-002 : Gestion des ressources
- **Connexions DB** : Pool de connexions configuré
- **Mémoire** : Limitation de la taille des payloads
- **Cache** : Mise en cache des données fréquemment accédées

### 10.2 Scalabilité

#### RG-SCALE-001 : Architecture stateless
- **Sessions** : Aucun état stocké côté serveur
- **Tokens** : Autoporteurs pour l'authentification
- **Load balancing** : Support du répartiteur de charge

---

## 11. Conformité et Audit

### 11.1 Traçabilité

#### RG-AUDIT-001 : Logs d'activité
- **Actions sensibles** : Connexions, modifications de rôles, suppressions
- **Données personnelles** : Conformité RGPD
- **Rétention** : Politique de conservation des logs

#### RG-AUDIT-002 : Historique des modifications
- **Timestamps** : Traçabilité de toutes les modifications
- **Utilisateur** : Identification de l'auteur des modifications
- **Données** : Conservation des états précédents pour l'audit

---

## 12. Conclusion

Ces règles de gestion constituent le socle fonctionnel du système BlingAuto API. Elles garantissent :

- **Intégrité des données** : Validation rigoureuse et contraintes métier
- **Sécurité** : Protection contre les vulnérabilités courantes
- **Cohérence** : Logique métier uniforme et prévisible
- **Traçabilité** : Audit complet des opérations
- **Performance** : Optimisation et scalabilité

Toute modification de ces règles doit être documentée et validée par l'équipe de développement et les parties prenantes métier.

---

**Version** : 1.0  
**Date** : 2025-09-30  
**Auteur** : Documentation Système BlingAuto API  
**Statut** : Version de production