import os
import sys

# 🚨 EMERGENCY SYSTEM-LEVEL INTERCEPTOR 🚨
# Completely remove Render's broken configuration from memory 
# before any Flask modules can auto-fetch it.
if "DATABASE_URL" in os.environ:
    del os.environ["DATABASE_URL"]

# Inject the working 141-character database string explicitly into the system environment
os.environ["DATABASE_URL"] = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"
os.environ["SQLALCHEMY_DATABASE_URI"] = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"

# Now safely import and build your app
from app import create_app

app = create_app("production" if os.environ.get("RENDER") else os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
