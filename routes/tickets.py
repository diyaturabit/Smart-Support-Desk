from common_imports import *

ticket_bp = Blueprint("ticket", __name__)

@ticket_bp.route("/create_ticket",methods=["POST"])
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

@ticket_bp.route("/get_ticket", methods=["GET"])
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
        
@ticket_bp.route("/delete_ticket/<int:ticket_id>", methods=["DELETE"])
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
    
@ticket_bp.route("/update_ticket/<int:ticket_id>", methods=["PUT"])
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


   
@ticket_bp.route("/tickets", methods=["GET"])
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
            params.ticket_bpend(status)

        if priority:
            sql += " AND priority = %s"
            params.ticket_bpend(priority)

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
    

    
@ticket_bp.route("/tickets/<int:ticket_id>/assign",methods=["PUT"])
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
        
@ticket_bp.route("/tickets/<int:ticket_id>", methods=["GET"])
@jwt_required
def get_ticket_detail(ticket_id):
    try:
        sql = """
            SELECT 
                t.id, t.title, t.description, t.status, t.priority,
                t.created_at,
                c.name AS customer_name,
                c.email AS customer_email
            FROM ticket t
            JOIN customer c ON t.customer_id = c.id
            WHERE t.id = %s
        """
        ticket = execute_query(sql, (ticket_id,), fetchone=True)

        return jsonify(ticket), 200

    except Exception as e:
        return handle_exception(e)

