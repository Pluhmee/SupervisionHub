import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ✅ FIXED: Removed the typo at the end and restored your correct, public Render database address with an explicit port
PRODUCTION_URI = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        "postgresql://postgres:money%40123@localhost:5432/supervision_hub_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "documents")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))  # 10 MB
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}

    # Flask-Mail
    # ✅ FIXED: Changed "://gmail.com" back to standard Google SMTP
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # 🚨 FORCED OVERRIDE: Overwrite the inherited Config property explicitly
    SQLALCHEMY_DATABASE_URI = PRODUCTION_URI


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": ProductionConfig, # Force production to handle the build commands
}
