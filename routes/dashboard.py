from common_imports import *
from pydantic import ValidationError


dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard", methods=["GET"])
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
