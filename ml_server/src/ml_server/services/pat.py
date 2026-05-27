import hashlib


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
