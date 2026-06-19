# Documentation technique — Epic Events CRM

---

## 1. Vue d'ensemble

Le système Epic Events CRM repose sur une base de données relationnelle articulée autour de quatre entités métier principales (`Employee`, `Client`, `Contract`, `Event`) et un référentiel de départements. Cette structure assure la cohérence des données, la traçabilité des assignations et l'intégrité référentielle des opérations commerciales.

---

## 2. Modèle des entités

| Entité | Description |
|---|---|
| **Employee** | Identifié par matricule et email uniques. Rôles définis via l'énumération `Department`. |
| **Client** | Centralise les informations de contact. Relié obligatoirement à un commercial (FK). |
| **Contract** | Définit les aspects financiers. Relié à un client et à un commercial. |
| **Event** | Représente la réalisation technique. Relié à un contrat (FK, unique) et optionnellement à un support (FK). |

---

## 3. Logique des relations

| Relation | Type | Intégrité |
|---|---|---|
| Employee → Client | Association | `RESTRICT` (préservation de l'historique) |
| Client → Contract | Composition (`*--`) | `CASCADE` (suppression en cascade) |
| Contract → Event | Composition (`*--`) | `CASCADE` (suppression en cascade) |
| Employee → Event | Association | `SET NULL` (réassignation possible) |

---

## 4. Conventions de notation

| Notation | Signification |
|---|---|
| `«PK»` (Primary Key) | Identifiant unique de l'enregistrement. |
| `«FK»` (Foreign Key) | Clé étrangère assurant la liaison entre deux tables. |
| `«UK»` (Unique Key) | Contrainte garantissant l'absence de doublons sur un champ. |
| Composition (`*--`) | Indique une dépendance forte ; la durée de vie de l'objet « fille » est conditionnée par l'objet « mère ». |
