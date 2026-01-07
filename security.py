from jose import jwt
from datetime import datetime,timezone,timedelta

SECRET_KEY=["Y1B8Z6STMVZE6FMYucyZWoq7DFwj5S-OI24kB_GOB8k"]
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)