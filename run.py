import os
from app import create_app

# Force 'production' if running on Render, otherwise look at FLASK_ENV
if os.environ.get("RENDER"):
    env_profile = "production"
    
    # Absolute Fail-Safe: If Render's Dashboard value is missing or misnamed,
    # Inject a working hardcoded database connection right here so it CANNOT crash.
    if not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://supervision_db_1ls7_user:HObRsD6CrI1YvjPzoyPr0gdJgn3jxNul@://render.com"
else:
    env_profile = os.environ.get("FLASK_ENV", "development")

# Initialize Flask
app = create_app(env_profile)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
