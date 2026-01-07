import mysql.connector
from flask import jsonify

def handle_exception(e):
    if isinstance(e, mysql.connector.Error):
        print("MySQL Error:", e)
        return jsonify({"error": "Database error", 
                        "details": str(e)}), 500

    print("Other Error:", e)
    return jsonify({"error": "Bad request",
                    "details": str(e)}), 400