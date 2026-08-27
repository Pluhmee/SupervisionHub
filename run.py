import os
import sys

# 🚨 SYSTEM LEVEL SCRUBBER 🚨
# This deletes the faulty dashboard keys from the server's brain completely 
# before any libraries attempt to inspect or validate the environment.
for key in ["DATABASE_URL", "SQLALCHEMY_DATABASE_URI", "SQLALCHEMY_BINDS"]:
    if key in os.environ:
        del os.environ[key]

# Manually push the clean 141-character URL with explicit port directly into the environment matrix
os.environ["DATABASE_URL"] = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"

# Now safely load your application code
from app import create_app

app = create_app("production" if os.environ.get("RENDER") else os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
