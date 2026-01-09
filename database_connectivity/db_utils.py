import mysql.connector
from database_connectivity.database import db_config

def execute_query(sql, values=None, fetchone=False, fetchall=False, commit=False):
    conn = cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, values)

        if commit:
            conn.commit()
            return cursor.lastrowid

        if fetchone:
            return cursor.fetchone()

        if fetchall:
            return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

