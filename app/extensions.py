import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

# ✅ Fixed: Added a custom initialization subclass to catch empty string variables before they hit the URL engine
class SafeSQLAlchemy(SQLAlchemy):
    def init_app(self, app):
        if os.environ.get("RENDER"):
            # Enforce your working production database URL directly into the Flask configuration registry
            app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"
            
            # Wipe the corrupt environment values completely from active server memory
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            if "SQLALCHEMY_DATABASE_URI" in os.environ:
                del os.environ["SQLALCHEMY_DATABASE_URI"]
                
        # Send the clean settings to the base extension initializer
        super().init_app(app)

db = SafeSQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()

# Redirect unauthorised access to the login page
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
