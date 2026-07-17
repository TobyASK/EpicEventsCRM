"""
Gestion de l'authentification avec JWT et hachage des mots de passe
"""
import jwt
import argon2
from os import remove
from datetime import datetime, timedelta, UTC
from typing import Optional
from config.settings import (
    JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS, AUTH_TOKEN_FILE,
)


# Hasher pour les mots de passe avec Argon2
ph = argon2.PasswordHasher()

TOKEN_PATH = AUTH_TOKEN_FILE


def hash_password(password: str) -> str:
    """
    Hache un mot de passe avec Argon2

    Args:
        password: Le mot de passe en clair

    Returns:
        Le hash du mot de passe
    """
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Vérifie qu'un mot de passe correspond à son hash

    Args:
        password: Le mot de passe en clair
        password_hash: Le hash à vérifier

    Returns:
        True si le mot de passe est correct
    """
    try:
        ph.verify(password_hash, password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
    except Exception:
        return False


def create_jwt_token(
    employee_id: int,
    employee_email: str,
    department: str,
) -> str:
    """
    Crée un token JWT pour un employé authentifié

    Args:
        employee_id: L'ID de l'employé
        employee_email: L'email de l'employé
        department: Le département de l'employé

    Returns:
        Le token JWT encodé
    """
    payload = {
        'employee_id': employee_id,
        'email': employee_email,
        'department': department,
        'iat': datetime.now(UTC)
    }
    if JWT_EXPIRATION_HOURS > 0:
        payload['exp'] = datetime.now(UTC) + timedelta(hours=JWT_EXPIRATION_HOURS)

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_jwt_token(token: str) -> Optional[dict]:
    """
    Décode et vérifie un token JWT

    Args:
        token: Le token JWT à décoder

    Returns:
        Le payload du token si valide, None sinon
    """
    try:
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def save_token_to_file(token: str, filepath: str = TOKEN_PATH):
    """
    Sauvegarde le token dans un fichier

    Args:
        token: Le token à sauvegarder
        filepath: Le chemin du fichier
    """
    with open(filepath, 'w') as f:
        f.write(token)


def load_token_from_file(filepath: str = TOKEN_PATH) -> Optional[str]:
    """
    Charge le token depuis un fichier

    Args:
        filepath: Le chemin du fichier

    Returns:
        Le token si trouvé, None sinon
    """
    try:
        with open(filepath, 'r') as f:
            token = f.read().strip()
            return token if token else None
    except FileNotFoundError:
        return None


def delete_token_file(filepath: str = TOKEN_PATH):
    """
    Supprime le fichier de token

    Args:
        filepath: Le chemin du fichier
    """
    try:
        remove(filepath)
    except FileNotFoundError:
        pass
