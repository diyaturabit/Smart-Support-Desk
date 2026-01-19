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
from logs.activity_logger import log_activity
# from flask_jwt_extended import jwt_required, get_jwt_identity

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
        staff_id=request.user.get("user_id")

        sql = "INSERT INTO customer (name, age, email, company,created_by) VALUES (%s, %s, %s, %s,%s)"
        customer_id = execute_query(
            sql,
            (customer.name, customer.age, customer.email, customer.company,staff_id),
            commit=True
        )
        log_activity(user=request.user,
                     action="CREATED CUSTOMER",
                     entity="CUSTOMER",
                     entity_id=customer_id,
                     description=f'Created Customer {customer.name}"')
        
        delete_cache("dashboard_stats")
        return jsonify({"message": "Customer Added",
                        "customer_id": customer_id,
                        "staff_id":staff_id}), 201

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
        ticket_entry_query="""
        SELECT DISTINCT c.id, c.name, c.email
        FROM customer c
        JOIN ticket t ON t.customer_id = c.id
        WHERE t.status != 'Closed'
        """

        admin_ticket_query="""SELECT DISTINCT c.id, c.name, c.email
        FROM customer c
        JOIN ticket t ON t.customer_id = c.id"""
        customers=execute_query(sql,fetchall=True)
        admin_ticket=execute_query(admin_ticket_query,fetchall=True)
        ticket_entry=execute_query(ticket_entry_query,fetchall=True)
        return jsonify({"total": len(customers),
                        "customers": customers,
                         "ticket_entry":ticket_entry,
                          "admin_ticket":admin_ticket }), 200

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
        log_activity(
    user=request.user,
    action="CUSTOMER DELETED",
    entity="Customer",
    entity_id=customer_id,
    description=f'{request.user["role"].capitalize()} {request.user["email"]} Deleted Customer ID: {customer_id}"'

)

        delete_cache("dashboard_stats")
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
        if customer_update!=customer_update:
            log_activity(user=request.user,
                         action="CUSTOMER_UPDATED",
                         entity="CUSTOMER",
                         entity_id=customer_id,
                         description=(f'updated customer (ID: {customer_id})'
)

)
        
        delete_cache("dashboard_stats")
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
        log_activity(
            user=request.user,
            action="TICKET_CREATED",
            entity="TICKET",
            entity_id=ticket_create,
            description=f'Created Ticket ID{ticket}"'

        )
        delete_cache("dashboard_stats")
        return jsonify({"message": "Ticket Added",
                        "ticket_id":ticket_create})
        

    except Exception as e:
        return handle_exception(e)

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
        log_activity(
            user=request.user,
            action="DELETED TICKET",
            entity="TICKET",
            entity_id=ticket_id,
            description=f"DELETED ticket"
        )
        delete_cache("dashboard_stats")

        if rows == 0:
            return jsonify({"message": "Ticket not found"}), 404

        return jsonify({"message": "Ticket deleted successfully"}), 200

    except Exception as e:
        return handle_exception(e)
    
@app.route("/update_ticket/<int:ticket_id>", methods=["PUT"])
@jwt_required
def update_ticket(ticket_id):
    try:
        data = request.get_json()
        role = request.user["role"]

        title = data.get("title")
        description = data.get("description")
        priority = data.get("priority")
        status = data.get("status")

        # 🔐 Staff rule
        if role == "staff" and status and status != "Closed":
            return jsonify({"error": "Staff can only close tickets"}), 403

        sql = """
        UPDATE ticket
        SET
            title = COALESCE(%s, title),
            description = COALESCE(%s, description),
            priority = COALESCE(%s, priority),
            status = COALESCE(%s, status)
        WHERE id = %s
        """

        values = (
            title,
            description,
            priority,
            status,
            ticket_id
        )

        rows = execute_query(sql, values, commit=True)



        return jsonify({"message": "Ticket updated successfully"}), 200

    except Exception as e:
        return handle_exception(e)
    
@app.route("/tickets", methods=["GET"])
@jwt_required
def list_tickets():
    try:
        status = request.args.get("status")
        priority = request.args.get("priority")

        user_id = request.user["user_id"]
        role = request.user["role"]

        sql = "SELECT * FROM ticket WHERE 1=1"
        params = []

        if status:
            sql += " AND status = %s"
            params.append(status)

        if priority:
            sql += " AND priority = %s"
            params.append(priority)

        tickets = execute_query(sql, tuple(params), fetchall=True)
      
        assigned_sql = """
        SELECT 
            t.id,
            t.title,
            t.status,
            t.priority,
            t.created_at,
            c.name  AS customer_name,
            c.email AS customer_email
        FROM ticket t
        JOIN customer c ON c.id = t.customer_id
        WHERE t.assigned_to = %s
        ORDER BY t.created_at DESC
        """
    
        assigned_to_user = execute_query(
            assigned_sql,
            (user_id,),
            fetchall=True
        )

        return jsonify({
            "count": len(tickets),
            "tickets": tickets,
            "assigned_to_user":assigned_to_user

        }), 200

    except Exception as e:
        return handle_exception(e)


@app.route("/customer/<int:customer_id>/tickets", methods=["GET"])
@jwt_required
def customer_ticket(customer_id):
    try:
        role=request.user.get("role")
        sql = """
        SELECT * FROM ticket
        WHERE customer_id = %s 
        """
        params=[customer_id]
        if role=="staff":
            sql+=" AND status!='Closed'"
        tickets = execute_query(sql,tuple(params), fetchall=True)

        if not tickets:
            return jsonify({
                "tickets": [],
                "message": "No tickets found for this customer"
            }), 200

        return jsonify({
            "tickets": tickets
        }), 200

    except Exception as e:
        return handle_exception(e)

        
@app.route("/customers/<int:customer_id>/tickets",methods=["GET"])
@jwt_required
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


# # Backend
# @app.route("/tickets/<int:ticket_id>/close", methods=["PUT"])
# @jwt_required
# def close_ticket(ticket_id):
#     try:
#         # No need to read JSON if you just use g.user
#         user = g.user

#         if not user or user["role"] != "staff":
#             return jsonify({"error": "Only staff can close tickets"}), 403

#         sql = "UPDATE ticket SET status = 'Closed' WHERE id = %s AND assigned_to = %s"
#         rows = execute_query(sql, (ticket_id, user["id"]), commit=True)

#         if rows == 0:
#             return jsonify({"error": "Ticket not found or not assigned to you"}), 404

#         return jsonify({"message": "Ticket closed successfully"}), 200



#     except Exception as e:
#         return handle_exception(e)


@app.route("/dashboard", methods=["GET"])
@jwt_required
def dashboard():
    try:
        # --- Check Redis cache ---
        cache_key = "dashboard_stats"
        user_id=request.user.get("user_id")
        cache = get_cache(cache_key)
        if cache:
            return jsonify(cache), 200

        # --- Combined stats query ---
        stats_query = """
        SELECT
            (SELECT COUNT(*) FROM customer) AS total_customer,
            (SELECT COUNT(*) FROM ticket WHERE status='Open') AS open_tickets,
            (SELECT COUNT(*) FROM ticket WHERE priority='High') AS high_tickets,
            (SELECT COUNT(*) FROM ticket WHERE priority='Medium') AS medium_tickets,
            (SELECT COUNT(*) FROM ticket WHERE priority='Low') AS low_tickets,
            (SELECT COUNT(*) FROM ticket WHERE assigned_to = %s and status='Inprogress') AS assigned_count
        """
        stats = execute_query(stats_query,(user_id,),fetchone=True)

        # --- Customer & Ticket summary (latest 50 customers) ---
        customer_ticket_query = """
        SELECT 
            c.name AS customer_name,
            c.email AS customer_email,
            u.email AS staff_email,
            COUNT(t.id) AS ticket_count
        FROM customer c
        LEFT JOIN users u ON c.created_by = u.id
        LEFT JOIN ticket t ON t.customer_id = c.id
        GROUP BY c.id, u.email
        ORDER BY c.id DESC
        LIMIT 50
        """
        user_ticket_count_query = """
            SELECT 
                u.id AS user_id,
                u.email,
                COUNT(t.id) AS ticket_count
            FROM users u
            LEFT JOIN ticket t 
                ON t.assigned_to = u.id AND t.status != 'Closed'
            GROUP BY u.id, u.email
            """

        user_ticket_count = execute_query(user_ticket_count_query, fetchall=True)

        customer_ticket = execute_query(customer_ticket_query,fetchall=True)
        unassigned_ticket_query="SELECT id,title from ticket WHERE status='Open' AND assigned_to is NULL"
        unassigned_ticket=execute_query(unassigned_ticket_query,fetchall=True)
        # --- Combine into one dictionary ---
        data = {
            "total_customer": stats["total_customer"],
            "open": stats["open_tickets"],
            "high": stats["high_tickets"],
            "medium": stats["medium_tickets"],
            "low": stats["low_tickets"],
            "customer_ticket": customer_ticket,
            "unassigned_ticket":unassigned_ticket,
            "assigned_count":stats["assigned_count"],
            "user_ticket_count":user_ticket_count
        }

        # --- Cache for 2 minutes ---
        set_cache(cache_key, data, ttl=120)

        return jsonify(data), 200

    except Exception as e:
        return handle_exception(e)

@app.route("/search", methods=["GET"])
@jwt_required
def search():
    try:
        query = request.args.get("q", "").strip()

        if not query:
            return jsonify({"error": "Search query is required"}), 400

        like_query = f"%{query}%"

        customer_sql = """
            SELECT id, name, email, company
            FROM customer
            WHERE name LIKE %s OR email LIKE %s
            LIMIT 10
        """
        customers = execute_query(
            customer_sql,
            (like_query, like_query),fetchall=True
        )

        ticket_sql = """
            SELECT 
                t.id,
                t.title,
                t.status,
                t.priority,
                c.name AS customer_name
            FROM ticket t
            JOIN customer c ON t.customer_id = c.id
            WHERE t.title LIKE %s OR t.description LIKE %s
            LIMIT 10
        """
        tickets = execute_query(
            ticket_sql,
            (like_query, like_query),fetchall=True
        )

        return jsonify({
            "customers": customers,
            "tickets": tickets
        }), 200
    except Exception as e:
        return handle_exception(e)



@app.route("/dashboard/admin",methods=["GET"])
def admin_dashboard():
    try:
        pass
    except:
        pass

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

@app.route("/tickets/<int:ticket_id>/assign",methods=["PUT"])
@jwt_required
@admin_required
def ticket_assignment(ticket_id):
    try:
        data=request.get_json()
        agent_id=data.get("agent_id")
        sql="UPDATE ticket SET assigned_to=%s,assigned_at=NOW(),status='Inprogress' where id=%s and assigned_to IS NULL"
        rows=execute_query(sql,(agent_id,ticket_id),commit=True)
        log_activity(
            user=request.user,
            action="Ticket Assigned",
            entity="Ticket",
            entity_id=ticket_id,
            description=f"Assigned ticket to agent_id={agent_id}, Status->Inprogress"
        )
        if rows==0:
            return jsonify({"message":"Ticket already assigned or not found"})
        
        return jsonify({
            "message":"Ticket Assigned"
        })
    except Exception as e:
        return handle_exception(e)
        



    
@app.route("/activity_logs", methods=["GET"])
@jwt_required
@admin_required
def get_activity_logs():
    logs = execute_query(
        """
        SELECT user_email, role, action, entity, description, created_at
        FROM activity_log
        ORDER BY created_at DESC
        LIMIT 15
        """,
        fetchall=True
    )
    return jsonify({"logs": logs})


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
    


if __name__=="__main__":
    app.run(debug=True)
