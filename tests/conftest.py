import pytest
import sqlite3
from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker
from config import Base
from models import Employee, Department
from utils import hash_password


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @sa_event.listens_for(engine, "connect")
    def _set_fk(dbapi_conn, _record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    from models import employee, client, contract, event
    _ = (employee, client, contract, event)
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def admin_user(db_session):
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
