from common_imports import *
from security.hashed_password import hash_password,verify_password
from auth import login
from security.security import SECRET_KEY, ALGORITHM, create_access_token
from datetime import datetime
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/users", methods=["POST"])
@jwt_required
@admin_required
def create_user():
    data = request.get_json()

    # 1️⃣ Validate input
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "email and password are required"}), 400

    role = data.get("role", "staff")  # default role

    if role not in ["admin", "staff"]:
        return jsonify({"error": "Invalid role"}), 400

    # 2️⃣ Hash password
    hashed_password = hash_password(data["password"])

    # 3️⃣ Insert user
    sql = """
    INSERT INTO users (email, password_hash, role)
    VALUES (%s, %s, %s)
    """

    try:
        execute_query(
            sql,
            (data["email"], hashed_password, role),
            commit=True
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "User created"}), 201

@auth_bp.route("/delete_user/<int:user_id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_user(user_id):
    try:
        sql = "DELETE FROM users WHERE id=%s"
        rows_affected = execute_query(
            sql,
            values=(user_id,),
            commit=True
        )

        if rows_affected == 0:
            return jsonify({"message": "User not found"}), 404

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        return handle_exception(e)

@auth_bp.route("/get_user", methods=["GET"])
@jwt_required
@admin_required
def get_user():
    try:
        sql = "SELECT id, email, role FROM users"
        users = execute_query(sql, fetchall=True)

        return jsonify({
            "total": len(users),
            "users": users
        }), 200

    except Exception as e:
        return handle_exception(e)




@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    sql = "SELECT id, password_hash, role FROM users WHERE email=%s"
    user_login = execute_query(sql, (email,), fetchone=True)

    if not user_login or not verify_password(password, user_login["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    # ✅ Generate token
    token = create_access_token({
        "user_id": user_login["id"],
        "email":email,
        "role": user_login["role"]
    })

    ip_address = request.remote_addr

    log_sql = """
    INSERT INTO login_logs (user_id, email, role, login_time, ip_address)
    VALUES (%s, %s, %s, %s, %s)
    """
    execute_query(
        log_sql,
        (
            user_login["id"],
            email,
            user_login["role"],
            datetime.utcnow(),
            ip_address
        ),
        commit=True
    )

    return jsonify({
        "message": "Login Successful",
        "access_token": token,
        "role": user_login["role"]
    })

print("SECRET_KEY:", SECRET_KEY)
print("ALGORITHM:", ALGORITHM)
