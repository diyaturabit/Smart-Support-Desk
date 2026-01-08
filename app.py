from flask import Flask, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from pydantic import ValidationError
import mysql.connector
from schemas import CustomerCreate,CustomerResponse,TicketCreate,TicketResponse,TicketUpdate
from database import db_config
from db_utils import execute_query
from exceptions import handle_exception
from hashed_password import hash_password,verify_password
from auth import login
from security import SECRET_KEY, ALGORITHM, create_access_token

import jwt
from functools import wraps

app = Flask(__name__)

SWAGGER_URL = '/docs'
API_URL = '/static/swagger.json'  # JSON file with your API spec
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "My Flask API"})
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Token missing"}), 401

        try:
            # Expect: "Bearer <token>"
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = payload
        except IndexError:
            return jsonify({"error": "Invalid Authorization header format"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper


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


# @app.route("/dashboard", methods=["GET"])
# @jwt_required
# def dashboard():
#     try:

#         # Open tickets
        
#         sql= "SELECT COUNT(*) AS count FROM ticket WHERE status = 'Open'"
#         tickets_count=execute_query(sql,fetchone=True)
    

#         # Closed tickets
#         sql_closed="SELECT COUNT(*) AS count FROM ticket WHERE priority = 'High'"
#         closed_tickets = execute_query(sql_closed,fetchone=True)

#         # High priority tickets
#         sql_high="SELECT COUNT(*) AS count FROM ticket WHERE priority = 'Low'"
#         high_ticket=execute_query(sql_high,fetchone=True)
    
      

#         return jsonify({
#             "open":tickets_count["count"],
#             "high": closed_tickets["count"],
#             "low": high_ticket["count"]
#         })

#     except Exception as e:
#         return handle_exception(e) 

import redis
import json



# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Cache TTL (seconds)
CACHE_TTL = 5

@app.route("/dashboard", methods=["GET"])
@jwt_required
def dashboard():
    try:
        # 1️⃣ Check Redis cache
        cached = r.get("dashboard_stats")
        if cached:
            return jsonify(json.loads(cached))  # return cached JSON
        total_customer = execute_query("SELECT COUNT(*) AS count FROM customer", fetchone=True)
        open_tickets = execute_query("SELECT COUNT(*) AS count FROM ticket WHERE status='Open'", fetchone=True)
        high_tickets = execute_query("SELECT COUNT(*) AS count FROM ticket WHERE priority='High'", fetchone=True)
        medium_tickets = execute_query("SELECT COUNT(*) AS count FROM ticket WHERE priority='Medium'", fetchone=True)
        low_tickets = execute_query("SELECT COUNT(*) AS count FROM ticket WHERE priority='Low'", fetchone=True)

        stats = {
            "total_customer":total_customer["count"],
            "open": open_tickets["count"],
            "high": high_tickets["count"],
            "medium": medium_tickets["count"],
            "low": low_tickets["count"]
        }

        r.setex("dashboard_stats", CACHE_TTL, json.dumps(stats))

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


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    print(f"DAATA:",data)
    sql = "SELECT id, password_hash, role FROM users WHERE email=%s"
    user_login = execute_query(sql, (email,), fetchone=True)
    print(user_login)

    if not user_login or not verify_password(password, user_login["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    # ✅ Only pass the payload
    token = create_access_token({
        "user_id": user_login["id"],
        "role": user_login["role"]
    })

    return jsonify({
        "message": "Login Successful",
        "access_token": token,
        "role": user_login["role"]
    })
print("SECRET_KEY:", SECRET_KEY)
print("ALGORITHM:", ALGORITHM)
    


if __name__=="__main__":
    app.run(debug=True)

# def login_user():
#     try:
#         data=request.get_json()
#         sql="SELECT id, password_hash FROM users WHERE email=%s",
#         (data["email"],)
#         user_login=execute_query(sql,fetchone=True)

#         if not user_login:
#             return jsonify({"error": "Invalid credentials"}), 401

#         if not verify_password(data["password"], user_login["password_hash"]):
#             return jsonify({"error": "Invalid credentials"}), 401
#         return jsonify({
#             "message":"Login Successfull"
#         })
#     except Exception as e:
#         return handle_exception(e)
        
    

