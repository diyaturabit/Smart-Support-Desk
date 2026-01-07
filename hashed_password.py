import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # Step 1: SHA-256 pre-hash
    passw = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # Step 2: bcrypt hash
    return pwd_context.hash(passw)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    passw = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return pwd_context.verify(passw, hashed_password)

# password = "diya"   # password you want for admin
# hashed_password = pwd_context.hash(password)

