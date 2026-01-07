from flask import request,jsonify
from db_utils import execute_query
from exceptions import handle_exception
from hashed_password import *
from security import create_access_token
def login():
    try:
        data=request.get_json()
        email=data.get("email")
        password=data.get("password")
        sql="SELECT id,password_hash,role from users WHERE email=%s,(email,)"
        user_login=execute_query(sql,fetchone=True)

        if not user_login or not  verify_password(password, user_login["password_hash"]):
            return jsonify({"error": "Invalid credentials"}), 401
        
        tokens=create_access_token({
            "user_id":user_login["id"],
            "role":user_login["role"]
        })

        return jsonify({
                "message":"Login Successfull",
                "accress token":tokens,
                "user":user_login["role"]
            })
    except Exception as e:
        return handle_exception(e)
        