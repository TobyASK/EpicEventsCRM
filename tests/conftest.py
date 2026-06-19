"""
Fixtures pytest partagées entre tous les modules de test.

Chaque test reçoit une session SQLite en mémoire isolée :
les tables sont créées avant le test et supprimées après,
garantissant l'indépendance totale entre les tests.
"""
import pytest
import sqlite3
from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker
from config.database import Base
from models.employee import Employee, Department
from utils.auth import hash_password


# ── Session de base de données ──────────────────────────────────────────

@pytest.fixture(scope="function")
def db_session():
    """
    Crée une base SQLite en mémoire pour un test, puis la détruit.

    L'utilisation de scope="function" garantit qu'aucun état ne persiste
    d'un test à l'autre.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Activer les clés étrangères sur chaque connexion ouverte par le pool
    @sa_event.listens_for(engine, "connect")
    def _set_fk(dbapi_conn, _record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    # Importer les modèles pour que Base.metadata les connaisse
    from models import employee, client, contract, event
    _ = (employee, client, contract, event)
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ── Utilisateurs de test ────────────────────────────────────────────────

@pytest.fixture
def admin_user(db_session):
    """Employé du département gestion (admin)."""
    emp = Employee(
        employee_number="ADM001",
        full_name="Admin Test",
        email="admin@test.com",
        password_hash=hash_password("adminpass"),
        department=Department.GESTION,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return {
        "employee_id": emp.id,
        "email": emp.email,
        "department": emp.department.value,
    }


@pytest.fixture
def commercial_user(db_session):
    """Employé du département commercial."""
    emp = Employee(
        employee_number="COM001",
        full_name="Commercial Test",
        email="commercial@test.com",
        password_hash=hash_password("compass"),
        department=Department.COMMERCIAL,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return {
        "employee_id": emp.id,
        "email": emp.email,
        "department": emp.department.value,
    }


@pytest.fixture
def support_user(db_session):
    """Employé du département support."""
    emp = Employee(
        employee_number="SUP001",
        full_name="Support Test",
        email="support@test.com",
        password_hash=hash_password("suppass"),
        department=Department.SUPPORT,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return {
        "employee_id": emp.id,
        "email": emp.email,
        "department": emp.department.value,
    }
