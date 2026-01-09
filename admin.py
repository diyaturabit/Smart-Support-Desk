from security.hashed_password import hash_password
from database_connectivity.db_utils import execute_query

sql = """
INSERT INTO users (email, password_hash, role)
VALUES (%s, %s, 'admin')
"""

params = ("admin@gmail.com", hash_password("diya123"))

execute_query(sql, params,commit=True)
print("diya")