import os
import sys

# 🚨 PURGE THE CORRUPTED ENVIRONMENT VARIABLE 🚨
# This stops Flask-SQLAlchemy from checking the dashboard value behind your back.
if "DATABASE_URL" in os.environ:
    del os.environ["DATABASE_URL"]

# Force the working database string explicitly into the runtime configuration dictionary
os.environ["SQLALCHEMY_DATABASE_URI"] = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"

from app import create_app

app = create_app("production" if os.environ.get("RENDER") else os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
