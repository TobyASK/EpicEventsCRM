# Epic Events CRM

Application CRM en ligne de commande pour la gestion des employés, clients, contrats et événements.

## Objectif

Le projet fournit un workflow complet pour :
- authentifier les utilisateurs par JWT ;
- appliquer des permissions par département ;
- gérer le cycle commercial client → contrat → événement ;
- administrer les comptes employés.

## Prérequis

- Python 3.11+
- pip

## Structure

```
projet12/
├── cli/                 # Commandes Click
├── config/              # Configuration DB et settings
├── controllers/         # Logique métier + contrôles d'accès
├── models/              # Modèles SQLAlchemy
├── tests/               # Tests unitaires/intégration
├── utils/               # Auth, permissions, logs Sentry
├── main.py              # Entrée CLI principale
├── init_database.py     # Initialisation DB + admin
└── requirements.txt
```

## Installation rapide

1. Créer et activer l'environnement virtuel.
```bash
python -m venv venv
venv\Scripts\activate
```

2. Installer les dépendances.
```bash
pip install -r requirements.txt
```

3. Créer le fichier `.env`.
```bash
copy .env.example .env
```

Variables recommandées dans `.env` :

```env
DATABASE_URL=sqlite:///./epicevents.db
JWT_SECRET_KEY=change-me-in-production
AUTH_TOKEN_FILE=.auth_token
SENTRY_DSN=

DEFAULT_ADMIN_EMPLOYEE_NUMBER=ADMIN001
DEFAULT_ADMIN_FULL_NAME=Administrateur
DEFAULT_ADMIN_EMAIL=admin@epicevents.com
DEFAULT_ADMIN_PASSWORD=admin123
```

4. Initialiser la base.
```bash
python init_database.py
```

Le compte administrateur initial est lu depuis les variables `DEFAULT_ADMIN_*`.

Important : changez `JWT_SECRET_KEY` et `DEFAULT_ADMIN_PASSWORD` avant un usage en production.

## Utilisation

Deux modes d'utilisation sont disponibles :

1. Mode commandes directes
2. Mode menu interactif

Mode menu interactif :

```bash
python main.py
```

Connexion / déconnexion :
```bash
python main.py login
python main.py logout
```

Commandes principales :
```bash
python main.py employee create
python main.py employee list
python main.py client create
python main.py client list --mine
python main.py contract create
python main.py contract list --unsigned
python main.py contract sign <id>
python main.py event list --no-support
python main.py event assign-support <event_id> <support_id>
```

Lors de `contract create`, la CLI :
- affiche les clients disponibles ;
- propose les commerciaux disponibles ;
- permet de sélectionner explicitement le contact commercial (avec valeur par défaut issue du client).

## Fonctionnement interne (concret)

### 1. Point d'entrée

- `main.py` initialise la base via `init_db()` puis :
	- lance les commandes CLI si des arguments sont fournis ;
	- lance un menu interactif sinon.
- Les commandes sont définies dans `cli/cli.py`.

### 2. Exécution d'une action

Chaque commande passe par `run_with_db()` dans `cli/cli.py` :

1. ouverture d'une session SQLAlchemy (`SessionLocal`) ;
2. vérification d'authentification si l'action est protégée (`require_auth`) ;
3. exécution de la logique métier dans un contrôleur ;
4. affichage du résultat ;
5. fermeture garantie de la session DB.

### 3. Authentification et session

- `login` (`AuthController.login` dans `controllers/auth_controller.py`) :
	- charge l'employé par email ;
	- vérifie le mot de passe haché Argon2 (`utils/auth.py`) ;
	- crée un JWT ;
	- sauvegarde le token localement (`AUTH_TOKEN_FILE`).
- `get_current_user` : lit le token, valide sa signature, puis recharge l'employé en base.
- `logout` : supprime le fichier token local.

### 4. Permissions et autorisation

- La matrice des permissions est définie dans `utils/permissions.py`.
- Les contrôleurs vérifient les droits avant toute lecture/écriture.
- Exemple de logique par rôle :
	- commercial : clients propres, événements de ses contrats signés ;
	- support : événements assignés ;
	- gestion : employés, contrats, signatures, assignation support.

### 5. Logique métier par domaine

- Employés : `controllers/employee_controller.py`
- Clients : `controllers/client_controller.py`
- Contrats : `controllers/contract_controller.py`
- Événements : `controllers/event_controller.py`

Règles clés implémentées :

1. un contrat doit être signé avant création d'événement ;
2. un support ne modifie que ses événements ;
3. un commercial ne modifie que ses clients ;
4. création de contrat avec sélection explicite du contact commercial.

### 6. Modèle de données

Les entités SQLAlchemy sont dans `models/` :

- `Employee`
- `Client`
- `Contract`
- `Event`

Le schéma relationnel est fourni dans `diagramme_bdd.pdf`.

### 7. Journalisation et erreurs

- Sentry est initialisé au démarrage CLI (`init_sentry` dans `utils/sentry_logger.py`).
- Les contrôleurs journalisent les exceptions (`log_exception`).
- Certains événements métier sont loggés (ex. signature de contrat).

### 8. Tests

- Les tests sont dans `tests/`.
- Ils couvrent permissions, authentification et règles métier principales.
- Exécution :

```bash
pytest -q
```

## Permissions

- Commercial: crée/modifie ses clients, crée des événements sur contrats signés de ses clients.
- Support: lit et modifie uniquement ses événements assignés.
- Gestion: admin employés, contrats (création, modification, signature) et assignation support.

## Sécurité

- ORM SQLAlchemy (requêtes paramétrées).
- Hachage mots de passe avec Argon2.
- Session persistante via token stocké dans un fichier (`AUTH_TOKEN_FILE`).
- Contrôle d'accès systématique en contrôleurs.
- Variables sensibles via `.env`.

## Qualité

Validation locale :
```bash
python -m compileall -q .
pytest -q
```

Rapport de couverture (optionnel) :

```bash
pytest --cov=. --cov-report=term-missing
```

État actuel validé : `92 passed`.

## Présentation technique

Le diagramme de base est disponible dans `diagramme_bdd.pdf`.

## Note

Ne pas versionner `.env`, `.auth_token`, ni `epicevents.db`.
