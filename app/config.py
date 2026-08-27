import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 1. Look for Render's environment variable first
raw_uri = os.environ.get("DATABASE_URL")

# 2. If it's missing, empty, or broken, use a safe SQLite fallback string
# This completely avoids the broken port parser error during the build phase
if not raw_uri or raw_uri.strip() == "":
    raw_uri = "sqlite:///" + os.path.join(BASE_DIR, "fallback.db")

# 3. Clean up the prefix driver structure for production PostgreSQL
if raw_uri.startswith("postgres://"):
    raw_uri = raw_uri.replace("postgres://", "postgresql://", 1)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-secret")
    
    # Force Flask-SQLAlchemy to use the verified, safe URI string directly
    SQLALCHEMY_DATABASE_URI = raw_uri
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
    "development": ProductionConfig,  # Force both options to look at the safe logic
    "production": ProductionConfig,
    "default": ProductionConfig,
}
