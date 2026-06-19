# DOCUMENTATION TECHNIQUE - EPIC EVENTS CRM

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture](#2-architecture)
3. [Modèles de données](#3-modèles-de-données)
4. [Sécurité](#4-sécurité)
5. [Authentification JWT](#5-authentification-jwt)
6. [Système de permissions](#6-système-de-permissions)
7. [Opérations CRUD](#7-opérations-crud)
8. [Interface CLI](#8-interface-cli)
9. [Journalisation Sentry](#9-journalisation-sentry)
10. [Choix techniques](#10-choix-techniques)

---

## 1. Vue d'ensemble

### Contexte

Epic Events est une entreprise de gestion d'événements. Le CRM gère :
- Les clients et leurs contacts commerciaux
- Les contrats signés avec les clients
- Les événements organisés dans le cadre de ces contrats
- Les employés répartis en 3 départements

### Objectifs

- Application CLI en Python
- Protection contre les injections SQL (ORM)
- Authentification avec JWT et hachage Argon2
- Principe du moindre privilège (permissions par département)
- Journalisation des événements critiques avec Sentry

### Stack technique

| Composant | Technologie |
|---|---|
| Langage | Python 3.9+ |
| Base de données | SQLite (via SQLAlchemy) |
| ORM | SQLAlchemy 2.0 |
| CLI | Click + Rich |
| Auth | Argon2 + PyJWT |
| Monitoring | Sentry |

---

## 2. Architecture

### MVC adapté pour CLI

```
cli/main.py              ← View (Click commands + Rich output)
      │
      ↓
controllers/             ← Controller (logique métier + permissions)
      │
      ↓
models/                  ← Model (SQLAlchemy ORM)
      │
      ↓
epicevents.db            ← SQLite
```

### Structure des fichiers

```
projet12/
├── config/
│   ├── database.py      # Engine SQLite, session, init_db()
│   └── settings.py      # JWT config, Sentry DSN
├── models/
│   ├── employee.py      # Employee + Department enum
│   ├── client.py
│   ├── contract.py
│   └── event.py
├── controllers/
│   ├── auth_controller.py
│   ├── employee_controller.py
│   ├── client_controller.py
│   ├── contract_controller.py
│   └── event_controller.py
├── cli/
│   └── main.py          # Toutes les commandes Click
├── utils/
│   ├── auth.py          # hash_password, JWT, token file
│   ├── permissions.py   # Permission + DEPARTMENT_PERMISSIONS
│   └── sentry_logger.py
├── epicevents.py        # Point d'entrée
└── init_database.py     # Script d'initialisation
```

---

## 3. Modèles de données

### Schéma des relations

```
Employee (commercial) ──── 1:N ──── Client ──── 1:N ──── Contract ──── 1:1 ──── Event
                                                              │                    │
Employee (gestion)  ─── signe ───────────────────────────────┘                    │
Employee (support)  ─── assigné ────────────────────────────────────────────────── ┘
```

### Employee

| Colonne | Type | Contraintes |
|---|---|---|
| id | INTEGER | PK |
| employee_number | VARCHAR(50) | UNIQUE, NOT NULL |
| full_name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(100) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| department | ENUM (VARCHAR) | NOT NULL : commercial / support / gestion |

### Client

| Colonne | Type | Contraintes |
|---|---|---|
| id | INTEGER | PK |
| full_name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(100) | UNIQUE, NOT NULL |
| phone | VARCHAR(20) | NOT NULL |
| company_name | VARCHAR(100) | NOT NULL |
| created_date | DATETIME | NOT NULL, DEFAULT NOW |
| last_contact_date | DATETIME | NOT NULL, auto-mis à jour |
| commercial_contact_id | INTEGER | FK → employees.id, NOT NULL |

### Contract

| Colonne | Type | Contraintes |
|---|---|---|
| id | INTEGER | PK |
| contract_number | VARCHAR(50) | UNIQUE, NOT NULL |
| total_amount | FLOAT | NOT NULL |
| amount_remaining | FLOAT | NOT NULL |
| is_signed | BOOLEAN | NOT NULL, DEFAULT FALSE |
| created_date | DATETIME | NOT NULL, DEFAULT NOW |
| client_id | INTEGER | FK → clients.id, NOT NULL |
| commercial_contact_id | INTEGER | FK → employees.id, NOT NULL |

### Event

| Colonne | Type | Contraintes |
|---|---|---|
| id | INTEGER | PK |
| event_name | VARCHAR(200) | NOT NULL |
| event_date_start | DATETIME | NOT NULL |
| event_date_end | DATETIME | NOT NULL |
| location | VARCHAR(200) | NOT NULL |
| attendees | INTEGER | NOT NULL |
| notes | TEXT | NULLABLE |
| created_date | DATETIME | NOT NULL, DEFAULT NOW |
| contract_id | INTEGER | FK → contracts.id, UNIQUE, NOT NULL |
| support_contact_id | INTEGER | FK → employees.id, NULLABLE |

---

## 4. Sécurité

### 4.1 Protection contre les injections SQL

SQLAlchemy ORM génère des requêtes paramétrées. Aucune requête SQL n'est construite par concaténation de chaînes :

```python
# Ce que nous faisons (sécurisé)
client = db.query(Client).filter(Client.email == email).first()

# Ce que nous n'utilisons jamais
query = f"SELECT * FROM clients WHERE email = '{email}'"  # dangereux
```

### 4.2 Hachage des mots de passe — Argon2

Argon2 est le gagnant du Password Hashing Competition (2015) et recommandé par l'OWASP :

```python
from argon2 import PasswordHasher

ph = PasswordHasher()
hash = ph.hash("mot_de_passe")     # salage automatique
ph.verify(hash, "mot_de_passe")    # True ou exception
```

**Avantages :**
- Salage automatique (chaque hash est unique)
- Résistance aux attaques GPU
- Paramètres ajustables (mémoire, itérations, parallélisme)

### 4.3 Variables d'environnement

Les secrets sont chargés depuis `.env` via `python-dotenv` :

```env
JWT_SECRET_KEY=...    # jamais en dur dans le code
SENTRY_DSN=...
```

`.env` et `epicevents.db` sont exclus du versioning via `.gitignore`.

### 4.4 Clés étrangères SQLite

SQLite désactive les clés étrangères par défaut. Le fichier `config/database.py` active le pragma au démarrage de chaque connexion :

```python
@sa_event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```

---

## 5. Authentification JWT

### Flux de connexion

```
1. login(email, password)
2. Vérification Argon2 du mot de passe
3. Génération du token JWT :
   payload = { employee_id, email, department, iat, exp }
   token = jwt.encode(payload, JWT_SECRET_KEY, HS256)
4. Sauvegarde dans .auth_token
5. Commandes suivantes : lecture + décodage du token
```

### Structure du token

```json
{
  "employee_id": 1,
  "email": "john@epicevents.com",
  "department": "commercial",
  "iat": 1709827200,
  "exp": 1709856000
}
```

- Durée de vie : 8 heures (une journée de travail)
- Algorithme : HS256
- Token expiré → suppression automatique, redirection vers login

---

## 6. Système de permissions

### Matrice complète

| Permission | Commercial | Support | Gestion |
|---|:---:|:---:|:---:|
| READ_ALL_CLIENTS | ✅ | ✅ | ✅ |
| CREATE_CLIENT | ✅ | ❌ | ❌ |
| UPDATE_OWN_CLIENTS | ✅ | ❌ | ❌ |
| READ_ALL_CONTRACTS | ✅ | ✅ | ✅ |
| CREATE_CONTRACT | ❌ | ❌ | ✅ |
| UPDATE_OWN_CONTRACTS | ✅ | ❌ | ❌ |
| UPDATE_CONTRACT (tous) | ❌ | ❌ | ✅ |
| SIGN_CONTRACT | ❌ | ❌ | ✅ |
| READ_ALL_EVENTS | ✅ | ✅ | ✅ |
| CREATE_EVENT | ✅ | ❌ | ❌ |
| READ_OWN_EVENTS | ❌ | ✅ | ❌ |
| UPDATE_OWN_EVENTS | ❌ | ✅ | ❌ |
| ASSIGN_SUPPORT | ❌ | ❌ | ✅ |
| CREATE_EMPLOYEE | ❌ | ❌ | ✅ |
| READ_EMPLOYEES | ❌ | ❌ | ✅ |
| UPDATE_EMPLOYEE | ❌ | ❌ | ✅ |
| DELETE_EMPLOYEE | ❌ | ❌ | ✅ |

### Règles métier supplémentaires (au-delà des permissions)

- **Commercial** : peut créer un client → auto-assigné comme contact commercial
- **Commercial** : peut modifier uniquement ses propres clients (`commercial_contact_id == current_user.employee_id`)
- **Commercial** : peut modifier uniquement les contrats de ses clients
- **Commercial** : peut créer un événement uniquement sur un contrat signé **et** appartenant à l'un de ses clients
- **Support** : peut modifier uniquement les événements qui lui sont assignés (`support_contact_id == current_user.employee_id`)
- **Gestion** : `assign_support` vérifie que l'employé cible est bien du département support

### Implémentation

```python
# utils/permissions.py

DEPARTMENT_PERMISSIONS = {
    Department.COMMERCIAL: _READ_ALL + [
        Permission.CREATE_CLIENT,
        Permission.UPDATE_OWN_CLIENTS,
        Permission.UPDATE_OWN_CONTRACTS,
        Permission.CREATE_EVENT,
    ],
    Department.SUPPORT: _READ_ALL + [
        Permission.READ_OWN_EVENTS,
        Permission.UPDATE_OWN_EVENTS,
    ],
    Department.GESTION: _READ_ALL + [
        Permission.CREATE_EMPLOYEE,
        Permission.READ_EMPLOYEES,
        Permission.UPDATE_EMPLOYEE,
        Permission.DELETE_EMPLOYEE,
        Permission.CREATE_CONTRACT,
        Permission.UPDATE_CONTRACT,
        Permission.SIGN_CONTRACT,
        Permission.ASSIGN_SUPPORT,
    ]
}
```

Vérification dans chaque controller :

```python
def create_client(self, current_user, ...):
    if not check_permission(current_user.get('department'), Permission.CREATE_CLIENT):
        raise PermissionError("Permission refusée")
    # ...
```

---

## 7. Opérations CRUD

### Pattern commun à tous les controllers

```python
def action(self, current_user, ...):
    try:
        # 1. Vérifier les permissions
        if not check_permission(...):
            raise PermissionError(...)

        # 2. Valider les données (unicité, existence)
        # 3. Effectuer l'opération
        # 4. Commit + refresh
        # 5. Journaliser si nécessaire (Sentry)
        return result

    except Exception as e:
        self.db.rollback()          # atomicité
        log_exception(e, context)   # traçabilité
        raise
```

### Opérations disponibles par entité

| Entité | Create | Read All | Read Own | Update All | Update Own | Delete |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Employee | Gestion | Gestion | — | Gestion | — | Gestion |
| Client | Commercial | Tous | Commercial | — | Commercial | — |
| Contract | Gestion | Tous | — | Gestion | Commercial | — |
| Event | Commercial | Tous | Support | — | Support | — |

---

## 8. Interface CLI

### Arborescence des commandes

```
epicevents.py
├── login
├── logout
├── init
├── employee
│   ├── create      (Gestion)
│   ├── list        (Gestion)
│   ├── update      (Gestion)
│   └── delete      (Gestion)
├── client
│   ├── create      (Commercial)
│   ├── list        (Tous)  --mine
│   └── update      (Commercial — ses clients)
├── contract
│   ├── create      (Gestion)
│   ├── list        (Tous)  --unsigned  --unpaid
│   ├── update      (Gestion + Commercial — ses clients)
│   └── sign        (Gestion)
└── event
    ├── create      (Commercial — contrat signé, ses clients)
    ├── list        (Tous)  --mine  --no-support
    ├── update      (Support — ses événements)
    └── assign-support  (Gestion)
```

### Bibliothèques

- **Click** : groupes de commandes, options, arguments, prompts
- **Rich** : tableaux colorés, messages de succès/erreur, prompts interactifs, confirmation

---

## 9. Journalisation Sentry

### Initialisation

Sentry est initialisé au démarrage de chaque commande CLI :

```python
@click.group()
def cli():
    init_sentry()  # no-op si SENTRY_DSN vide
```

### Événements capturés

| Événement | Niveau | Contexte |
|---|---|---|
| Toute exception non gérée | error | action + données pertinentes |
| Création d'un employé | info | email, département |
| Modification d'un employé | info | email cible, email auteur |
| Signature d'un contrat | info | numéro contrat, nom client |

### Activer Sentry

```env
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

Sans DSN configuré, l'application fonctionne normalement (les logs sont silencieux).

---

## 10. Choix techniques

### SQLite plutôt qu'un SGBD externe

SQLite est intégré à Python — aucune installation serveur requise. SQLAlchemy abstrait complètement le dialecte SQL : le code de l'application est identique quel que soit le moteur. La migration vers PostgreSQL en production ne nécessite que de changer `DATABASE_URL`.

### SQLAlchemy ORM

Protection automatique contre les injections SQL, mapping objet-relationnel, gestion des transactions et des sessions. Alternative au SQL brut sans perte de flexibilité.

### Argon2 pour les mots de passe

Algorithme recommandé par l'OWASP, gagnant du Password Hashing Competition 2015. Plus résistant aux attaques GPU que bcrypt ou PBKDF2.

### JWT pour l'authentification

Authentification stateless adaptée à une CLI : le token est stocké localement et relu à chaque commande. Pas de session serveur à maintenir. Expiration automatique après 8 heures.

### Click + Rich pour la CLI

Click simplifie la définition de groupes de commandes, d'options et de prompts interactifs. Rich améliore la lisibilité avec des tableaux et des couleurs, sans complexité supplémentaire.

---

## Conformité au cahier des charges

| Exigence | Statut | Implémentation |
|---|:---:|---|
| Python 3.9+ | ✅ | `python --version` |
| Application CLI | ✅ | Click + Rich |
| Prévention injections SQL | ✅ | SQLAlchemy ORM uniquement |
| Principe du moindre privilège | ✅ | `DEPARTMENT_PERMISSIONS` + vérifications controller |
| Journalisation Sentry | ✅ | Exceptions + création/modification employés + signature contrats |
| Hachage mots de passe | ✅ | Argon2 avec salage automatique |
| Authentification | ✅ | JWT, expiration 8h |
| CRUD clients | ✅ | Commercial (création + ses clients) |
| CRUD contrats | ✅ | Gestion (tous) + Commercial (ses clients) |
| CRUD événements | ✅ | Commercial (création) + Support (ses événements) |
| CRUD employés | ✅ | Gestion (création + modification + **suppression**) |
| Filtres événements sans support | ✅ | `event list --no-support` |
| Filtres contrats non signés / non payés | ✅ | `contract list --unsigned / --unpaid` |
| Assignation support | ✅ | `event assign-support` (Gestion) |

---

**Version :** 1.0.0
