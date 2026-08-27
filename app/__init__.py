import os
from flask import Flask
from app.config import config
from app.extensions import db, migrate, bcrypt, login_manager, mail


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    
    # Load default base setups first
    app.config.from_object(config[config_name])

    # 🚨 FORCED PRODUCTION OVERRIDE FOR RENDER 🚨
    # This directly forces the correct, explicit port string format into the app dictionary
    # It overwrites any empty strings pulled from files or dashboard settings.
    if os.environ.get("RENDER"):
        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"
        
        # Prevent Flask-SQLAlchemy from checking alternative database strings background memory
        if "SQLALCHEMY_BINDS" in app.config:
            del app.config["SQLALCHEMY_BINDS"]

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # ... (Keep the rest of your blueprints and routes below exactly the same)
