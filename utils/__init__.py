import hashlib


def hash_password(password: str) -> str:
    """Parolni SHA-256 bilan shifrlash."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Parolni tekshirish."""
    return hash_password(password) == hashed
