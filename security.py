from jose import jwt
from datetime import datetime, timedelta
import os

# ----------------------
# JWT Config
# ----------------------
# Robust SECRET_KEY assignment
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # fallback for local/dev environment
    SECRET_KEY = "supersecuredevkey1234567890"  # must be str, not None

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 750

# ----------------------
# Create JWT
# ----------------------
def create_access_token(data: dict):
    """
    Creates a JWT token with an expiration.
    Ensures SECRET_KEY is always a valid string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Encode token using jose
    token = jwt.encode(to_encode, str(SECRET_KEY), algorithm=ALGORITHM)
    return token

# ----------------------
# Test
# ----------------------
if __name__ == "__main__":
    sample_data = {"user_id": 1, "role": "admin"}
    token = create_access_token(sample_data)
    print("JWT:", token)
