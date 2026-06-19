"""
Script d'initialisation de la base de données
Crée les tables et un utilisateur administrateur par défaut
"""
from config.database import init_db, SessionLocal
from models.employee import Employee, Department
from utils.auth import hash_password


def create_admin_user():
    """Crée un utilisateur administrateur par défaut"""
    db = SessionLocal()
    try:
        # Vérifier si un admin existe déjà
        existing = db.query(Employee).filter(
            Employee.email == "admin@epicevents.com").first()
        if existing:
            print("[!] Un utilisateur admin existe déjà")
            return

        # Créer l'admin
        admin = Employee(
            employee_number="ADMIN001",
            full_name="Administrateur",
            email="admin@epicevents.com",
            password_hash=hash_password("admin123"),
            department=Department.GESTION
        )

        db.add(admin)
        db.commit()

        print("[OK] Utilisateur administrateur créé avec succès!")
        print("  Email: admin@epicevents.com")
        print("  Mot de passe: admin123")
        print("  [!] ATTENTION: Changez ce mot de passe en production!")

    except Exception as e:
        print(f"[ERREUR] Création de l'admin: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Initialisation de la base de données Epic Events CRM...")
    print()

    # Créer les tables
    print("Création des tables...")
    init_db()
    print("[OK] Tables créées avec succès!")
    print()

    # Créer l'utilisateur admin
    print("Création de l'utilisateur administrateur...")
    create_admin_user()
    print()

    print("[OK] Initialisation terminée!")
    print()
    print("Pour vous connecter:")
    print("  python epicevents.py login")
