import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Pure static string assignment - zero risk of empty string extraction
PRODUCTION_URI = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"


class Config:
    # Use standard static keys instead of os.environ polling to avoid empty evaluations
    SECRET_KEY = "supervision-hub-secure-fallback-key-998877"
    SQLALCHEMY_DATABASE_URI = PRODUCTION_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "documents")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}

    # Flask-Mail
    MAIL_SERVER = "://gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "fallback@gmail.com"
    MAIL_PASSWORD = "fallbackpassword"
    MAIL_DEFAULT_SENDER = "fallback@gmail.com"


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:money%40123@localhost:5432/supervision_hub_db"


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = PRODUCTION_URI


config = {
    "development": ProductionConfig,
    "production": ProductionConfig,
    "default": ProductionConfig,  # Force all profiles to hit the correct production URL layout
}
