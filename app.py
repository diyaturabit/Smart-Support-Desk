from flask import Flask
# from flask_jwt_extended import JWTManager

from routes.customers import customer_bp
from routes.tickets import ticket_bp
from routes.search import search_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from security.security import SECRET_KEY, ALGORITHM, create_access_token

app = Flask(__name__)


from flask import Flask
from routes.customers import customer_bp
from routes.tickets import ticket_bp
from routes.activity_logs import log_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp


app = Flask(__name__)

# Register all blueprints
app.register_blueprint(customer_bp, url_prefix="/customer")
app.register_blueprint(ticket_bp, url_prefix="/ticket")
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
app.register_blueprint(log_bp, url_prefix="/logs")
app.register_blueprint(search_bp, url_prefix="/search")



if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000,debug=True)