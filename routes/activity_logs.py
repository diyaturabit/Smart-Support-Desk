from common_imports import *


log_bp = Blueprint("log_activity", __name__)
    
@log_bp.route("/activity_logs", methods=["GET"])
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
