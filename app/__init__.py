import os
from flask import Flask
from app.config import config
from app.extensions import db, migrate, bcrypt, login_manager, mail


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    
    # 1. Force load the default settings object configurations
    app.config.from_object(config[config_name])

    # 2. 🚨 THE NUCLEAR OVERRIDE 🚨
    # This hard-binds your working 141-character URL with an explicit port.
    # It replaces whatever configuration or environment value was loaded above.
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # --- Extensions ---
    # This will now safely read the forced string value directly
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # ... (Keep the rest of your blueprints and routes below exactly the same)
