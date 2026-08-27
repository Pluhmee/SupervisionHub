import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 1. Fetch the raw environment string safely
raw_db_url = os.environ.get("DATABASE_URL", "").strip()

# 2. Strip any accidental wrap-around quote characters if they exist
if (raw_db_url.startswith("'") and raw_db_url.endswith("'")) or (raw_db_url.startswith('"') and raw_db_url.endswith('"')):
    raw_db_url = raw_db_url[1:-1].strip()

# 3. Safely handle the prefix or provide a local fallback string
if raw_db_url:
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    PRODUCTION_DB_URI = raw_db_url
else:
    # Local fallback for development machines
    PRODUCTION_DB_URI = "postgresql://postgres:money%40123@localhost:5432/supervision_hub_db"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-secret")
    SQLALCHEMY_DATABASE_URI = PRODUCTION_DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "documents")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))  # 10 MB
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}

    # Flask-Mail
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


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": ProductionConfig,  # ✅ Changed to production for Render safety
}
