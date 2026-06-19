# Guide des Commandes - Epic Events CRM

## Démarrage rapide

```bash
# 1. Activer l'environnement virtuel
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# 2. Initialiser la base (première fois uniquement)
python init_database.py

# 3. Se connecter
python epicevents.py login
# Email: admin@epicevents.com | Mot de passe: admin123
```

---

## Authentification

### Se connecter
```bash
python epicevents.py login
```
Génère un token JWT valide 8 heures, stocké dans `.auth_token`.

### Se déconnecter
```bash
python epicevents.py logout
```

---

## Employés

> **Permissions :** Gestion uniquement (création, modification, suppression)
> Lecture : Gestion uniquement

### Créer un employé
```bash
python epicevents.py employee create
```
Prompts : numéro d'employé · nom · email · mot de passe · département (commercial/support/gestion)

```
Numéro d'employé: COM001
Nom complet: Jean Dupont
Email: jean.dupont@epicevents.com
Mot de passe: ********
Département: commercial
✓ Employé Jean Dupont créé avec succès!
```

### Lister les employés
```bash
python epicevents.py employee list
```

### Modifier un employé
```bash
python epicevents.py employee update <id>
```
Les champs non modifiés conservent leur valeur par défaut.

### Supprimer un employé
```bash
python epicevents.py employee delete <id>
```
Demande une confirmation avant suppression. Impossible de supprimer son propre compte.

```
Vous allez supprimer : Jean Dupont (jean.dupont@epicevents.com)
Confirmer la suppression ? [y/N]: y
✓ Employé supprimé avec succès!
```

---

## Clients

> **Permissions :**
> - Lecture : tous les collaborateurs
> - Création : Commercial (auto-assigné comme contact)
> - Modification : Commercial (ses propres clients uniquement)

### Créer un client
```bash
python epicevents.py client create
```
Prompts : nom · email · téléphone · entreprise

```
Nom complet: Kevin Casey
Email: kevin@startup.io
Téléphone: +678 123 456 78
Nom de l'entreprise: Cool Startup LLC
✓ Client Kevin Casey créé avec succès!
```

### Lister les clients
```bash
python epicevents.py client list           # Tous les clients
python epicevents.py client list --mine    # Mes clients uniquement (Commercial)
```

### Modifier un client
```bash
python epicevents.py client update <id>
```
Un commercial ne peut modifier que ses propres clients.

---

## Contrats

> **Permissions :**
> - Lecture + filtres : tous les collaborateurs
> - Création : Gestion uniquement
> - Modification : Gestion (tous) · Commercial (ses clients uniquement)
> - Signature : Gestion uniquement

### Créer un contrat
```bash
python epicevents.py contract create
```
Prompts : numéro · ID client · montant total · montant restant (optionnel, défaut = montant total)

```
Numéro de contrat: CT-2026-001
ID du client: 1
Montant total: 50000
Montant restant (laisser vide = montant total): 25000
✓ Contrat CT-2026-001 créé avec succès!
```

### Lister les contrats
```bash
python epicevents.py contract list              # Tous les contrats
python epicevents.py contract list --unsigned   # Non signés seulement
python epicevents.py contract list --unpaid     # Non payés seulement
```

### Modifier un contrat
```bash
python epicevents.py contract update <id>
```
Modifie le montant total et/ou le montant restant.
Un commercial ne peut modifier que les contrats de ses propres clients.

### Signer un contrat
```bash
python epicevents.py contract sign <id>
```
Réservé à la Gestion. Requis avant de pouvoir créer un événement.

```
✓ Contrat CT-2026-001 signé avec succès!
```

---

## Événements

> **Permissions :**
> - Lecture : tous les collaborateurs
> - Création : Commercial (pour ses clients ayant un contrat signé)
> - Modification : Support (ses propres événements uniquement)
> - Assignation support : Gestion uniquement

### Créer un événement
```bash
python epicevents.py event create
```
Prompts : ID contrat · nom · lieu · participants · date début · date fin · notes

```
ID du contrat: 1
Nom de l'événement: Lancement Produit X
Lieu: Convention Center Paris
Nombre de participants: 150
Date de début (YYYY-MM-DD HH:MM): 2026-06-15 14:00
Date de fin (YYYY-MM-DD HH:MM): 2026-06-15 18:00
Notes (optionnel): VIP lounge requis
✓ Événement Lancement Produit X créé avec succès!
```

> Le contrat doit être signé, et appartenir à un client du commercial connecté.

### Lister les événements
```bash
python epicevents.py event list               # Tous les événements
python epicevents.py event list --mine        # Mes événements (Support)
python epicevents.py event list --no-support  # Sans support assigné (Gestion)
```

### Modifier un événement
```bash
python epicevents.py event update <id>
```
Un support ne peut modifier que les événements qui lui sont assignés.

### Assigner un support
```bash
python epicevents.py event assign-support <event_id> <support_id>
```
Réservé à la Gestion. Le destinataire doit être du département support.

```
python epicevents.py employee list            # Trouver l'ID du support
python epicevents.py event assign-support 1 3
✓ Support assigné à l'événement Lancement Produit X!
```

---

## Workflows typiques

### Workflow Commercial — Nouveau client et événement

```bash
python epicevents.py login

# Créer le client (auto-assigné)
python epicevents.py client create

# Vérifier les contrats disponibles (créés par Gestion)
python epicevents.py contract list

# Une fois le contrat signé par Gestion, créer l'événement
python epicevents.py event create
```

### Workflow Gestion — Signature et assignation

```bash
python epicevents.py login

# Voir les contrats non signés
python epicevents.py contract list --unsigned

# Signer
python epicevents.py contract sign <id>

# Voir les événements sans support
python epicevents.py event list --no-support

# Trouver un support disponible
python epicevents.py employee list

# Assigner
python epicevents.py event assign-support <event_id> <support_id>
```

### Workflow Support — Gérer ses événements

```bash
python epicevents.py login

# Voir mes événements
python epicevents.py event list --mine

# Mettre à jour un événement
python epicevents.py event update <id>

# Consulter les clients et contrats (lecture seule)
python epicevents.py client list
python epicevents.py contract list
```

---

## Gestion des erreurs fréquentes

| Message | Cause | Solution |
|---|---|---|
| `Vous devez être authentifié` | Token absent ou expiré | `python epicevents.py login` |
| `Permission refusée` | Action interdite pour votre département | Vérifier le tableau des permissions |
| `Le contrat doit être signé` | Événement créé sur un contrat non signé | Demander à Gestion de signer |
| `Vous ne pouvez modifier que vos propres clients` | Commercial sur un client d'un autre commercial | Action limitée à vos clients |
| `L'employé n'est pas du département support` | `assign-support` ciblant un non-support | Vérifier l'ID avec `employee list` |

---

## Astuces

```bash
# Aide générale
python epicevents.py --help

# Aide par groupe
python epicevents.py employee --help
python epicevents.py contract --help

# Format des dates
2026-06-15 14:00   # YYYY-MM-DD HH:MM
```

---

**Version :** 1.0.0
