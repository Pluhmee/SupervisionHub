import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# FORCEFULLY hardcode the working 141-character URL to bypass the Render Blueprint bug
PRODUCTION_URI = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-secret")
    
    # If running on Render, force-inject the correct URI string directly
    if os.environ.get("RENDER"):
        SQLALCHEMY_DATABASE_URI = PRODUCTION_URI
    else:
        # Local development fallback
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
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "://gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": ProductionConfig,
}
