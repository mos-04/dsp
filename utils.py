import hashlib

def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()
