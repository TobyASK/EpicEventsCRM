# Guide d'Installation - Epic Events CRM

## Prérequis

- **Python 3.9+** — [python.org](https://www.python.org/downloads/)
- **pip** — inclus avec Python
- Aucune base de données externe : SQLite est intégré à Python

### Vérifier Python

```bash
python --version
# ou sur Linux/Mac :
python3 --version
```

---

## Étape 1 : Récupérer le projet

```bash
git clone <url-du-repository>
cd projet12
```

Ou télécharger et extraire le ZIP, puis ouvrir un terminal dans le dossier.

---

## Étape 2 : Créer l'environnement virtuel

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

Le prompt doit afficher `(venv)` une fois activé.

---

## Étape 3 : Installer les dépendances

```bash
pip install -r requirements.txt
```

**Packages installés :**
- `sqlalchemy` — ORM
- `click` — framework CLI
- `rich` — interface enrichie
- `argon2-cffi` — hachage de mots de passe
- `pyjwt` — tokens JWT
- `sentry-sdk` — monitoring
- `python-dotenv` — variables d'environnement

---

## Étape 4 : Configurer les variables d'environnement

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Ouvrir `.env` et renseigner :

```env
# Base de données SQLite (chemin vers le fichier .db)
DATABASE_URL=sqlite:///./epicevents.db

# Clé secrète JWT — générer une clé aléatoire :
JWT_SECRET_KEY=votre-cle-secrete-ici

# Sentry (optionnel)
SENTRY_DSN=
```

### Générer une clé JWT sécurisée

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copier la valeur générée dans `JWT_SECRET_KEY`.

---

## Étape 5 : Initialiser la base de données

```bash
python init_database.py
```

Le fichier `epicevents.db` est créé automatiquement. Vous devriez voir :

```
Initialisation de la base de données Epic Events CRM...

Création des tables...
Tables créées avec succès!

Création de l'utilisateur administrateur...
Utilisateur administrateur créé avec succès!
  Email: admin@epicevents.com
  Mot de passe: admin123
  ATTENTION: Changez ce mot de passe en production!

Initialisation terminée!
```

---

## Étape 6 : Vérifier l'installation

```bash
python epicevents.py login
```

Entrer :
- Email : `admin@epicevents.com`
- Mot de passe : `admin123`

Résultat attendu :
```
Connexion réussie!
Bienvenue Administrateur (gestion)
```

Tester une commande :
```bash
python epicevents.py employee list
```

---

## Étape 7 : Sécuriser l'installation

### Changer le mot de passe admin

```bash
python epicevents.py employee update 1
```

### Créer les premiers utilisateurs

```bash
# Créer un commercial
python epicevents.py employee create
# Numéro: COM001 | Département: commercial

# Créer un support
python epicevents.py employee create
# Numéro: SUP001 | Département: support
```

### Configurer Sentry (optionnel)

1. Créer un projet Python sur [sentry.io](https://sentry.io)
2. Copier le DSN dans `.env` :
```env
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

---

## Réinitialisation complète

Pour repartir de zéro :

```bash
# 1. Supprimer la base de données
del epicevents.db        # Windows
rm epicevents.db         # Linux/Mac

# 2. Supprimer le token de session
del .auth_token          # Windows
rm .auth_token           # Linux/Mac

# 3. Réinitialiser
python init_database.py
```

---

## Dépannage

### "python: command not found"
Utiliser `py` (Windows) ou `python3` (Linux/Mac).

### "No module named 'click'"
L'environnement virtuel n'est pas activé. Relancer `venv\Scripts\activate`.

### "unable to open database file"
Vérifier que le dossier courant est bien `projet12/` et que `DATABASE_URL` pointe vers un chemin accessible.

### Token expiré
Les tokens JWT expirent après 8 heures :
```bash
python epicevents.py logout
python epicevents.py login
```

---

## Checklist d'installation

- [ ] Python 3.9+ installé
- [ ] Environnement virtuel créé et activé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Fichier `.env` configuré avec `JWT_SECRET_KEY`
- [ ] Base de données initialisée (`python init_database.py`)
- [ ] Connexion testée (`python epicevents.py login`)
- [ ] Mot de passe admin changé
- [ ] Premiers utilisateurs créés

---

**Version :** 1.0.0
