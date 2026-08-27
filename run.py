import os
from app import create_app

# Debug print statements that will show up directly in your Render logs
db_env_var = os.environ.get("DATABASE_URL", "NOT_FOUND")
print("=== RENDER DATABASE_URL DIAGNOSTIC ===")
print(f"Variable exists: {db_env_var != 'NOT_FOUND'}")
print(f"String length: {len(db_env_var)}")
print(f"Starts with postgresql: {db_env_var.startswith('postgresql')}")
print("=======================================")

app = create_app("production" if os.environ.get("RENDER") else os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
