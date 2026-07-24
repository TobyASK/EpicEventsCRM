from config import (
    init_db,
    SessionLocal,
    DEFAULT_ADMIN_EMPLOYEE_NUMBER,
    DEFAULT_ADMIN_FULL_NAME,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD,
)
from models import Employee, Department
from utils import hash_password


def create_admin_user():
    """Crée l'utilisateur administrateur par défaut s'il est absent."""
    db = SessionLocal()
    try:
        existing = db.query(Employee).filter(
            Employee.email == DEFAULT_ADMIN_EMAIL).first()
        if existing:
            print("[!] Un utilisateur admin existe déjà")
            return

        admin = Employee(
            employee_number=DEFAULT_ADMIN_EMPLOYEE_NUMBER,
            full_name=DEFAULT_ADMIN_FULL_NAME,
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            department=Department.GESTION
        )

        db.add(admin)
        db.commit()

        print("[OK] Utilisateur administrateur créé avec succès!")
        print(f"  Email: {DEFAULT_ADMIN_EMAIL}")
        print(f"  Mot de passe: {DEFAULT_ADMIN_PASSWORD}")
        print("  [!] ATTENTION: Changez ce mot de passe en production!")

    except Exception as e:
        print(f"[ERREUR] Création de l'admin: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Initialisation de la base de données Epic Events CRM...")
    print()

    print("Création des tables...")
    init_db()
    print("[OK] Tables créées avec succès!")
    print()

    print("Création de l'utilisateur administrateur...")
    create_admin_user()
    print()

    print("[OK] Initialisation terminée!")
    print()
    print("Pour vous connecter:")
    print("  python main.py login")
