from flask import Flask, request, jsonify
from pydantic import ValidationError
import mysql.connector
from schemas import CustomerCreate,CustomerResponse,TicketCreate,TicketResponse,TicketUpdate
from database_connectivity.database import db_config
from database_connectivity.db_utils import execute_query
from exceptions import handle_exception
from security.hashed_password import hash_password,verify_password
from auth import login
from security.security import SECRET_KEY, ALGORITHM, create_access_token
from decorators import jwt_required,admin_required
from Redis.connection import get_cache,set_cache,delete_cache
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return {"message": "Flask Working"}

@app.route("/create_customer", methods=["POST"])
@jwt_required
def create_customer():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    try:
        customer = CustomerCreate(**request.get_json())
        sql = "INSERT INTO customer (name, age, email, company) VALUES (%s, %s, %s, %s)"
        customer_id = execute_query(
            sql,
            (customer.name, customer.age, customer.email, customer.company),
            commit=True
        )
        return jsonify({"message": "Customer Added",
                        "customer_id": customer_id}), 201

    except Exception as e:
        return handle_exception(e)

    except ValidationError as e:
        return jsonify({
            "message":"Input Invalid",
            "details": e.errors()
        })
    except mysql.connector.IntegrityError as e:
        if "Duplicate entry" in str(e):
            return jsonify({"error": "Email already exists"}), 409



@app.route("/get_customer",methods=["GET"])
@jwt_required
def get_customer():
    try:
        sql="SELECT * from customer"
        customers=execute_query(sql,fetchall=True)
        return jsonify({"total": len(customers),
                        "customers": customers }), 200

    except Exception as e:
        return handle_exception(e)
    
@app.route("/delete_customer/<int:customer_id>",methods=["DELETE"])
@jwt_required
def delete_customer(customer_id:int):
    try:
        sql="DELETE FROM customer where id=%s"
        customer_delete=execute_query(
            sql,(customer_id,),commit=True
        )
        if customer_delete == 0:
            return jsonify({"message": "Customer not found"}), 404

        return jsonify({"message": "Customer deleted successfully"}), 200

    except Exception as e:
        handle_exception(e)

@app.route("/update_customer/<int:customer_id>",methods=["PUT"])
@jwt_required
def update_customer(customer_id):
    try:
        customer=CustomerCreate(**request.get_json())
        sql="UPDATE customer set name=%s,age=%s,email=%s, company=%s WHERE id=%s"
        values=(customer.name, customer.age, customer.email, customer.company,customer_id)
        customer_update=execute_query(sql,values,commit=True)
        if customer_update == 0:
            return {"message": "Customer not found"}
        
        return {
            "message": "Customer updated successfully",
            "customer_id": customer_id
        }
    
    except Exception as e:
        handle_exception(e)

@app.route("/create_ticket",methods=["POST"])
@jwt_required
def create_ticket():
    try:
        ticket=TicketCreate(**request.get_json())
        sql="INSERT INTO ticket (title,description,priority,customer_id) VALUES (%s,%s,%s,%s)"
        values=(ticket.title,ticket.description,ticket.priority,ticket.customer_id)
        ticket_create=execute_query(sql,values,commit=True)
        return jsonify({"message": "Ticket Added",
                        "ticket_id":ticket_create})
    
    except Exception as e:
        handle_exception(e)

    except mysql.connector.IntegrityError as e:
        return jsonify ({"error": "Invalid Customer_id"}),400

@app.route("/get_ticket", methods=["GET"])
@jwt_required
def get_ticket():
    try:
        sql="SELECT * FROM ticket"
        tickets = execute_query(
            sql,
            fetchall=True
        )

        return jsonify({
            "total": len(tickets),
            "ticket": tickets
        }), 200

    except Exception as e:
        handle_exception(e)
        
@app.route("/delete_ticket/<int:ticket_id>", methods=["DELETE"])
@jwt_required
def delete_ticket(ticket_id):
    try:
        rows = execute_query(
            "DELETE FROM ticket WHERE id=%s",
            (ticket_id,),
            commit=True
        )

        if rows == 0:
            return jsonify({"message": "Ticket not found"}), 404

        return jsonify({"message": "Ticket deleted successfully"}), 200

    except Exception as e:
        return handle_exception(e)
@app.route("/update_ticket/<int:ticket_id>", methods=["PUT"])
@jwt_required
def update_ticket(ticket_id):
    try:
        data = TicketUpdate(**request.get_json())

        sql = """
        UPDATE ticket
        SET
            title = COALESCE(%s, title),
            description = COALESCE(%s, description),
            priority = COALESCE(%s, priority),
            status = COALESCE(%s, status),
            customer_id = COALESCE(%s, customer_id)
        WHERE id = %s
        """

        values = (
            data.title,
            data.description,
            data.priority,
            data.status,
            data.customer_id,
            ticket_id
        )

        rows = execute_query(sql, values, commit=True)

        if rows == 0:
            return {"message": "Ticket not found"}, 404

        return {"message": "Ticket updated"}, 200

    except Exception as e:
        return handle_exception(e)

@app.route("/tickets",methods=["GET"])
@jwt_required
def list_tickets():
    try:
        status=request.args.get("status")
        priority=request.args.get("priority")
        sql="SELECT * from ticket WHERE 1=1"
        query=[]
        if status:
            sql+=" AND status=%s"
            query.append(status)
        if priority:
            sql+=" AND priority=%s"
            query.append(priority)
        
        tickets=execute_query(sql,tuple(query),fetchall=True)
        return jsonify ({
            "count":len(tickets),
            "tickets":tickets
        })

    except Exception as e:
        return handle_exception(e)

@app.route("/customer/<int:customer_id>/tickets",methods=["GET"])
@jwt_required
@admin_required
def customer_ticket(customer_id):
    try:
        sql="SELECT * FROM ticket WHERE customer_id=%s"
        customer_tic=execute_query(sql,(customer_id,),fetchall=True)
        if customer_tic==0:
            return jsonify({
                "message":"No tickets registered for this customer"
            })
        return jsonify({
            "customer_ticket":customer_tic
        })

    except Exception as e:
        return handle_exception(e)
        
@app.route("/customers/<int:customer_id>/tickets",methods=["GET"])
@jwt_required
@admin_required
def customer_tickets(customer_id):
    try:
        status=request.args.get("status")
        priority=request.args.get("priority")
        sql="SELECT * from ticket where customer_id=%s"
        query=[customer_id]
        if status:
            sql+=" AND status=%s"
            query.append(status)
        if priority:
            sql+=" AND priority=%s"
            query.append(priority)
        customer_tic=execute_query(sql,tuple(query),fetchall=True)
        if customer_tic==0:
            return jsonify({
                "message":"no tickets are found with this filtering"
            })
        return jsonify({
            "count":len(customer_tic),
            "customer_tic":customer_tic
        })
    except Exception as e:
        return handle_exception(e)


@app.route("/dashboard", methods=["GET"])
@jwt_required
def dashboard():
    try:
        # 1️⃣ Check Redis cache
        cache_key = "dashboard_stats"
        cache=get_cache(cache_key)
        if cache:
            return jsonify(cache),200
        total_customer = execute_query("SELECT COUNT(*) AS count FROM customer", fetchone=True)
        open_tickets = execute_query("SELECT COUNT(*) AS count FROM ticket WHERE status='Open'", fetchone=True)
        high_tickets = execute_query("SELECT COUNT(*) AS count FROM ticket WHERE priority='High'", fetchone=True)
        medium_tickets = execute_query("SELECT COUNT(*) AS count FROM ticket WHERE priority='Medium'", fetchone=True)
        low_tickets = execute_query("SELECT COUNT(*) AS count FROM ticket WHERE priority='Low'", fetchone   =True)

        stats = {
            "total_customer":total_customer["count"],
            "open": open_tickets["count"],
            "high": high_tickets["count"],
            "medium": medium_tickets["count"],
            "low": low_tickets["count"]
        }

        set_cache(cache_key,set_cache,ttl=100)
        return jsonify(stats),200

    except Exception as e:
        return handle_exception(e)



@app.route("/users", methods=["POST"])
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

@app.route("/delete_user/<int:user_id>", methods=["DELETE"])
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

@app.route("/get_user", methods=["GET"])
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

    


@app.route("/login", methods=["POST"])
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
        "role": user_login["role"]
    })

    # ✅ NEW: store login info
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
    


if __name__=="__main__":
    app.run(debug=True)
