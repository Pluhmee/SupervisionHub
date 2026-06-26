"""
seed.py
Run once to bootstrap the admin account:

    python seed.py

Or as a Flask CLI command:

    flask create-admin
"""
import os
import click
from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User, UserType, UserStatus


app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.cli.command("create-admin")
@click.option("--email", default="admin@supervision.com", prompt="Admin email")
@click.option("--password", default="Admin@1234", prompt="Admin password", hide_input=True)
@click.option("--first-name", default="System", prompt="First name")
@click.option("--last-name", default="Admin", prompt="Last name")
def create_admin(email, password, first_name, last_name):
    """Seed the first administrator account."""
    with app.app_context():
        if User.query.filter_by(email=email).first():
            click.echo(f"[!] An account with email '{email}' already exists. Skipping.")
            return

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        admin = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_pw,
            user_type=UserType.admin,
            department="Administration",
            faculty="Administration",
            status=UserStatus.active,
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f"[✓] Admin account created: {email}")


if __name__ == "__main__":
    with app.app_context():
        # Direct run (non-CLI) — uses defaults
        if User.query.filter_by(email="admin@supervision.com").first():
            print("[!] Admin already exists.")
        else:
            hashed_pw = bcrypt.generate_password_hash("Admin@1234").decode("utf-8")
            admin = User(
                first_name="System",
                last_name="Admin",
                email="admin@supervision.com",
                password=hashed_pw,
                user_type=UserType.admin,
                department="Administration",
                faculty="Administration",
                status=UserStatus.active,
            )
            db.session.add(admin)
            db.session.commit()
            print("[✓] Admin created: admin@supervision.com / Admin@1234")


# ── Seed LASU faculties and departments ──────────────────────────
with app.app_context():
    from app.data.seed_lasu import seed_lasu_data
    seed_lasu_data(app)
