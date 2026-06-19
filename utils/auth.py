"""
Gestion de l'authentification avec JWT et hachage des mots de passe
"""
import os
import jwt
import argon2
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from config.settings import (
    JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
)


# Hasher pour les mots de passe avec Argon2
ph = argon2.PasswordHasher()

# Emplacement du jeton de session : dans le dossier personnel de
# l'utilisateur (chemin absolu stable, retrouvé quel que soit le dossier
# courant et conservé après un redémarrage du PC). Surchargeable via .env.
TOKEN_PATH = os.getenv(
    'AUTH_TOKEN_FILE', str(Path.home() / '.epicevents_auth_token'))


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
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

    payload = {
        'employee_id': employee_id,
        'email': employee_email,
        'department': department,
        'exp': expiration,
        'iat': datetime.utcnow()
    }

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


def load_token_from_file(filepath: str = '.auth_token') -> Optional[str]:
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


def delete_token_file(filepath: str = '.auth_token'):
    """
    Supprime le fichier de token

    Args:
        filepath: Le chemin du fichier
    """
    try:
        import os
        os.remove(filepath)
    except FileNotFoundError:
        pass
