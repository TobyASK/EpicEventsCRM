"""
Configuration de la base de données (SQLite)
"""
import os
import sqlite3
from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./epicevents.db')

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# SQLite désactive les clés étrangères par défaut
@sa_event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Active PRAGMA foreign_keys=ON sur chaque nouvelle connexion SQLite.

    SQLite n'applique pas les contraintes de clé étrangère sans ce pragma.
    L'événement 'connect' garantit qu'il est exécuté pour chaque connexion
    ouverte par le pool, y compris après un recyclage.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Générateur de session — ferme automatiquement après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crée toutes les tables (idempotent)."""
    from models import employee, client, contract, event
    # Référencer les modules garantit leur enregistrement auprès de
    # Base.metadata avant create_all() (import nécessaire pour son effet
    # de bord, pas pour son usage direct)
    _ = (employee, client, contract, event)
    Base.metadata.create_all(bind=engine)
