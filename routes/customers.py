from common_imports import *
from pydantic import ValidationError

customer_bp = Blueprint("customer", __name__)

@customer_bp.route("/create_customer", methods=["POST"])
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



@customer_bp.route("/get_customer",methods=["GET"])
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
    
@customer_bp.route("/delete_customer/<int:customer_id>",methods=["DELETE"])
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

@customer_bp.route("/update_customer/<int:customer_id>",methods=["PUT"])
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



@customer_bp.route("/customer/<int:customer_id>/tickets", methods=["GET"])
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

        
@customer_bp.route("/customers/<int:customer_id>/tickets",methods=["GET"])
@jwt_required
def customer_tickets(customer_id):
    try:
        status=request.args.get("status")
        priority=request.args.get("priority")
        sql="SELECT * from ticket where customer_id=%s"
        query=[customer_id]
        if status:
            sql+=" AND status=%s"
            query.customer_bpend(status)
        if priority:
            sql+=" AND priority=%s"
            query.customer_bpend(priority)
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


@customer_bp.route("/customers/<int:customer_id>", methods=["GET"])
@jwt_required
def get_customer_detail(customer_id):
    try:
        customer_sql = """
            SELECT id, name, email, company, created_at
            FROM customer
            WHERE id = %s
        """
        customer = execute_query(customer_sql, (customer_id,), fetchone=True)

        ticket_count_sql = """
            SELECT COUNT(*) AS ticket_count
            FROM ticket
            WHERE customer_id = %s
        """
        ticket_count = execute_query(ticket_count_sql, (customer_id,), fetchone=True)

        tickets_sql = """
            SELECT id, title, status, priority, created_at
            FROM ticket
            WHERE customer_id = %s
        """
        tickets = execute_query(tickets_sql, (customer_id,), fetchall=True)

        return jsonify({
            "customer": customer,
            "ticket_count": ticket_count["ticket_count"],
            "tickets": tickets
        }), 200

    except Exception as e:
        return handle_exception(e)
