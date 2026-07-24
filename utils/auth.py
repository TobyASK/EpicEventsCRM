import jwt
import argon2
from datetime import datetime
from typing import Optional
from config import (
    JWT_SECRET_KEY, JWT_ALGORITHM, AUTH_TOKEN_FILE,
)


ph = argon2.PasswordHasher()


def hash_password(password: str) -> str:
    """Hash un mot de passe en utilisant Argon2."""
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie qu'un mot de passe correspond à un hash Argon2."""
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
    """Crée un token JWT pour une session utilisateur."""
    payload = {
        'employee_id': employee_id,
        'email': employee_email,
        'department': department,
        'iat': datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_jwt_token(token: str) -> Optional[dict]:
    """Décode un token JWT et valide uniquement sa signature."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        return payload
    except jwt.InvalidTokenError:
        return None


def save_token_to_file(token: str, filepath: str = AUTH_TOKEN_FILE):
    """Sauvegarde un token JWT dans un fichier local."""
    with open(filepath, 'w') as f:
        f.write(token)


def load_token_from_file(filepath: str = AUTH_TOKEN_FILE) -> Optional[str]:
    """Charge un token JWT depuis un fichier local."""
    try:
        with open(filepath, 'r') as f:
            token = f.read().strip()
            return token if token else None
    except FileNotFoundError:
        return None


def delete_token_file(filepath: str = AUTH_TOKEN_FILE):
    """Supprime le fichier de token local s'il existe."""
    try:
        from os import remove
        remove(filepath)
    except FileNotFoundError:
        pass
