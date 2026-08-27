import os
from flask import Flask
from app.config import config
from app.extensions import db, migrate, bcrypt, login_manager, mail


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 🚨 SYSTEM-LEVEL ENVIRONMENT CLEANUP 🚨
    # This deletes the faulty dashboard keys from active memory completely
    # right before Flask-SQLAlchemy inspects the runtime state.
    for key in ["DATABASE_URL", "SQLALCHEMY_DATABASE_URI", "SQLALCHEMY_BINDS"]:
        if key in os.environ:
            del os.environ[key]

    # Explicitly enforce your verified 141-character database string layout
    correct_uri = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"
    
    app.config["SQLALCHEMY_DATABASE_URI"] = correct_uri
    
    # Debug print verification sequence to view real-time mapping state
    print("=== CRITICAL RENDER APP ENGINE CONFIG CHECK ===")
    print(f"Final App Config target string: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"System memory DATABASE_URL check: {os.environ.get('DATABASE_URL')}")
    print("==============================================")

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # --- Import all models so Flask-Migrate sees them ---
    with app.app_context():
        from app.models import (  # noqa: F401
            User, Project, Document, Message, Milestone, Meeting, Notification,
            Faculty, Department
        )

    # --- Blueprints ---
    from app.auth import auth_bp
    from app.student import student_bp
    from app.supervisor import supervisor_bp
    from app.admin import admin_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(supervisor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # --- Landing page ---
    from flask import render_template, redirect, url_for
    from flask_login import current_user

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            from app.models.user import UserType
            role_map = {
                UserType.student: "student.dashboard",
                UserType.supervisor: "supervisor.dashboard",
                UserType.admin: "admin.dashboard",
            }
            return redirect(url_for(role_map[current_user.user_type]))
        return render_template("shared/landing.html")

    # --- Error handlers ---
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("shared/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("shared/404.html"), 404

    @app.errorhandler(413)
    def file_too_large(e):
        from flask import flash, redirect, request as req
        flash("File too large. Maximum allowed size is 10 MB.", "danger")
        return redirect(req.referrer or url_for("index")), 413

    return app
