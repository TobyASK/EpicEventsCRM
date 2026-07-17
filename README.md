# Epic Events CRM

Application CRM (Customer Relationship Management) développée pour Epic Events, entreprise spécialisée dans l'organisation d'événements pour start-ups.

## Description

Epic Events CRM est une application en ligne de commande sécurisée permettant de gérer :
- Les **clients** et leurs informations
- Les **contrats** signés avec les clients
- Les **événements** organisés
- Les **employés** de l'entreprise (Commercial, Support, Gestion)

## Architecture

L'application suit une architecture MVC (Model-View-Controller) :

```
projet12/
├── config/              # Configuration (base de données, settings)
├── models/              # Modèles de données (SQLAlchemy)
├── controllers/         # Logique métier et opérations CRUD
├── cli/                 # Interface en ligne de commande (Click + Rich)
├── utils/               # Utilitaires (auth, permissions, Sentry)
├── tests/               # Tests unitaires et d'intégration (pytest)
├── epicevents.py        # Point d'entrée de l'application
├── init_database.py     # Script d'initialisation de la base
└── requirements.txt     # Dépendances Python
```

## Sécurité

**Protection contre les injections SQL**
- Utilisation de **SQLAlchemy ORM** — toutes les requêtes sont paramétrées

**Gestion des mots de passe**
- Hachage avec **Argon2** (algorithme recommandé par l'OWASP)
- Salage automatique, aucun stockage en clair

**Authentification**
- JWT (JSON Web Token) avec expiration à 8 heures
- Token stocké localement dans `.auth_token`

**Permissions**
- Principe du moindre privilège
- Permissions basées sur les départements
- Vérification systématique avant chaque opération

**Données sensibles**
- Variables d'environnement via `.env`
- `.gitignore` configuré pour exclure `.env` et la base SQLite

## Installation

### Prérequis
- Python 3.9 ou supérieur
- Aucune base de données externe requise (SQLite intégré à Python)

### Étapes

1. **Cloner le repository**
```bash
git clone <votre-repo>
cd projet12
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer les variables d'environnement**
```bash
# Windows
copy .env.example .env
# Linux/Mac
cp .env.example .env
```

Éditer `.env` et renseigner au minimum la clé JWT :
```env
DATABASE_URL=sqlite:///./epicevents.db
JWT_SECRET_KEY=votre-clé-secrète-très-longue-et-aléatoire
```

5. **Initialiser la base de données**
```bash
python init_database.py
```

Cela crée les tables et un utilisateur administrateur :
- Email : `admin@epicevents.com`
- Mot de passe : `admin123`

> **Changez ce mot de passe avant toute utilisation.**

## Utilisation

### Connexion / déconnexion
```bash
python epicevents.py login
python epicevents.py logout
```

### Gestion des employés

```bash
python epicevents.py employee create
python epicevents.py employee list
python epicevents.py employee update <id>
python epicevents.py employee delete <id>
```

### Gestion des clients

```bash
python epicevents.py client create
python epicevents.py client list
python epicevents.py client list --mine      # Mes clients uniquement
python epicevents.py client update <id>
```

### Gestion des contrats

```bash
python epicevents.py contract create
python epicevents.py contract list
python epicevents.py contract list --unsigned   # Non signés
python epicevents.py contract list --unpaid     # Non payés
python epicevents.py contract update <id>
python epicevents.py contract sign <id>
```

### Gestion des événements

```bash
python epicevents.py event create
python epicevents.py event list
python epicevents.py event list --mine          # Mes événements (Support)
python epicevents.py event list --no-support    # Sans support assigné
python epicevents.py event update <id>
python epicevents.py event assign-support <event_id> <support_id>
```

## Permissions par département

### Tous les collaborateurs (lecture seule)
- Accès en lecture à tous les clients, contrats et événements

### Commercial
- Créer et modifier ses propres clients (auto-assigné à la création)
- Modifier les contrats de ses clients
- Filtrer les contrats (non signés, non payés)
- Créer des événements pour ses clients ayant un contrat signé

### Support
- Voir et modifier ses propres événements (ceux qui lui sont assignés)

### Gestion
- Créer, modifier et **supprimer** des employés
- Créer, modifier et **signer** des contrats
- **Assigner** un membre du support à un événement

## Modèle de données

### Employee
`id` · `employee_number` · `full_name` · `email` · `password_hash` · `department`

### Client
`id` · `full_name` · `email` · `phone` · `company_name` · `created_date` · `last_contact_date` · `commercial_contact_id`

### Contract
`id` · `contract_number` · `total_amount` · `amount_remaining` · `is_signed` · `created_date` · `client_id` · `commercial_contact_id`

### Event
`id` · `event_name` · `event_date_start` · `event_date_end` · `location` · `attendees` · `notes` · `created_date` · `contract_id` · `support_contact_id`

## Journalisation avec Sentry

Configurez `SENTRY_DSN` dans `.env` pour activer :
- Toutes les exceptions
- Création et modification d'employés
- Signature de contrats

## Tests et qualité de code

```bash
# Lancer la suite de tests
python -m pytest tests/ -v

# Avec couverture de code
python -m pytest tests/ --cov=controllers --cov=models --cov=utils --cov-report=term-missing

# Vérifier la conformité PEP8
python -m flake8 --max-line-length=100 cli/ config/ controllers/ models/ utils/ tests/ epicevents.py init_database.py
```

91 tests unitaires et d'intégration couvrent l'authentification, le système de permissions et les opérations CRUD des 4 entités métier. Le code respecte PEP8 (0 violation flake8).

## Diagramme de base de données

Le diagramme de classes UML (`diagramme_bdd.png`) décrit les 4 entités et leurs relations (associations, compositions avec cascade, multiplicités). Voir [BDD_EXPLANATION.md](BDD_EXPLANATION.md) pour le détail des règles d'intégrité.

## Documentation complémentaire

- [INSTALLATION.md](INSTALLATION.md) — guide d'installation pas à pas
- [GUIDE_COMMANDES.md](GUIDE_COMMANDES.md) — référence complète des commandes CLI
- [DOCUMENTATION.md](DOCUMENTATION.md) — documentation technique détaillée (architecture, sécurité, permissions)
- [BDD_EXPLANATION.md](BDD_EXPLANATION.md) — modèle de données et conventions du diagramme

## Technologies

- **Python 3.9+**
- **SQLAlchemy 2.0** — ORM, protection anti-injection SQL
- **SQLite** — base de données embarquée (aucune installation requise)
- **Click** — framework CLI
- **Rich** — interface CLI enrichie
- **Argon2** — hachage de mots de passe
- **PyJWT** — tokens JWT
- **Sentry** — journalisation des erreurs
- **python-dotenv** — variables d'environnement
- **pytest / pytest-cov** — tests unitaires et d'intégration, couverture de code
- **flake8** — conformité PEP8

## Licence

Ce projet est développé pour Epic Events dans le cadre d'un projet pédagogique OpenClassrooms.

---

> Ne jamais commiter le fichier `.env` ni le fichier `epicevents.db`.
> Changer le mot de passe administrateur par défaut avant toute utilisation réelle.
