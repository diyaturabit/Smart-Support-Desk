from database_connectivity.db_utils import execute_query

def log_activity(user, action, entity, entity_id=None, description=None):
    sql = """
    INSERT INTO activity_log 
    (user_id, user_email, role, action, entity, entity_id, description)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    execute_query(
        sql,
        (
            user.get("user_id"),
            user.get("email"),
            user.get("role"),
            action,
            entity,
            entity_id,
            description
        ),
        commit=True
    )
