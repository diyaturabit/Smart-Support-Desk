from common_imports import *

search_bp = Blueprint("search", __name__)

@search_bp.route("/search", methods=["GET"])
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


