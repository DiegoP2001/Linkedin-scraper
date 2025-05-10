from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from routes.api.routes import *
from routes.auth.auth import *
from routes.admin.dashboard import *
from dotenv import load_dotenv
from config.config import Config
from models.models import db
from flask_migrate import Migrate
from tasks.celery_app import celery_init_app
from werkzeug.middleware.proxy_fix import ProxyFix

if Config.ENVIRONMENT != "dev":
    load_dotenv("/home/ekiona/linkedin/.env")

def create_app():

    app = Flask(__name__,)

    app.register_blueprint(routes)
    app.register_blueprint(auth)
    app.register_blueprint(admin_dashboard)

    if Config.ENVIRONMENT == "dev":
        app.debug = True

    if Config.ENVIRONMENT != "dev":
        cors = CORS(app, supports_credentials=True ,resources={r"/*": {"origins": "https://ilumek.es"}})
    else:
        allowed_origins = ["chrome-extension://finffceojabnnhbinccmekdkadpjkmmn", "http://localhost:5173"]
        cors = CORS(app, supports_credentials=True ,resources={r"/*": {"origins": allowed_origins}})

    # Configuration
    app.config.from_object(Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    celery = celery_init_app(app)
    celery.autodiscover_tasks(['tasks.tasks', 'tasks.scheduled_tasks'])
    db.init_app(app)
    migrate = Migrate(app, db)

    jwt = JWTManager(app)
    
    return app, celery


app, celery = create_app()
