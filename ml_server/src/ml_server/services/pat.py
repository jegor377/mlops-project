import hashlib


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
