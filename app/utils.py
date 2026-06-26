"""
app/utils.py
Shared utility functions used across blueprints.
"""
import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db, mail
from flask_mail import Message as MailMessage


# ---------------------------------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file) -> tuple[str, str, int]:
    """
    Save an uploaded FileStorage object to the uploads directory.

    Returns:
        (stored_filename, relative_path, file_size_bytes)
    """
    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    full_path = os.path.join(upload_dir, unique_name)
    file.save(full_path)
    file_size = os.path.getsize(full_path)
    relative_path = os.path.join("uploads", "documents", unique_name)
    return unique_name, relative_path, file_size


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


# ---------------------------------------------------------------------------
# EMAIL NOTIFICATIONS
# ---------------------------------------------------------------------------
def send_email(subject: str, recipients: list[str], body: str, html: str = None):
    """
    Send an email via Flask-Mail (SMTP).
    Silently logs errors in development rather than crashing.
    """
    try:
        msg = MailMessage(subject=subject, recipients=recipients, body=body, html=html)
        mail.send(msg)
    except Exception as exc:
        current_app.logger.error(f"[EMAIL ERROR] Failed to send to {recipients}: {exc}")


def notify_user(user_id: int, notification_type: str, title: str, message: str, link: str = None):
    """
    Create an in-app notification record for a user.
    Caller must commit the session.
    """
    from app.models.notification import Notification
    Notification.create(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )


def notify_and_email(user, notification_type: str, title: str, message: str, link: str = None):
    """
    Create an in-app notification AND send an email for the same event.
    """
    notify_user(user.user_id, notification_type, title, message, link)
    send_email(
        subject=title,
        recipients=[user.email],
        body=message,
    )


# ---------------------------------------------------------------------------
# ROLE GUARD DECORATOR
# ---------------------------------------------------------------------------
from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    """Decorator that restricts a view to specific user_type values."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                from flask import redirect, url_for
                return redirect(url_for("auth.login"))
            if current_user.user_type.value not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


# ---------------------------------------------------------------------------
# MATRIC NUMBER VALIDATION  (DUMMY MODE — presentation build)
# ---------------------------------------------------------------------------
def parse_matric(matric_no: str) -> dict | None:
    """
    Parse a 9-digit LASU matric number: YYFFDDNNN
      YY  = 2-digit admission year  (positions 0-1)
      FF  = 2-digit faculty code    (positions 2-3)
      DD  = 2-digit dept code       (positions 4-5)
      NNN = 3-digit serial          (positions 6-8)

    Returns parsed dict or None if format is wrong.
    """
    matric_no = matric_no.strip()
    if not matric_no.isdigit() or len(matric_no) != 9:
        return None
    return {
        "year":         matric_no[0:2],
        "faculty_code": matric_no[2:4],
        "dept_code":    matric_no[4:6],
        "serial":       matric_no[6:9],
    }


def validate_matric_against_selection(
    matric_no: str, faculty_id: int, department_id: int
) -> str | None:
    """
    DUMMY VALIDATOR for presentation purposes.

    Rules enforced:
      1. Must be exactly 9 digits.
      2. Faculty code digits (positions 2-3) must match the selected faculty's code.
      3. Department code digits (positions 4-5) must match the selected dept's code.
      4. Serial (positions 6-8) must be 001-999 — any non-zero serial is accepted.

    No real student records are checked. Any structurally valid matric number
    that encodes the correct faculty and department codes will pass.

    Example: student in Faculty of Science (code=01), Computer Science (code=04)
             entering year 2022, serial 020 → matric = 220104020  ✓
    """
    from app.models.faculty import Faculty
    from app.models.department import Department

    parsed = parse_matric(matric_no)
    if parsed is None:
        return "Matric number must be exactly 9 digits with no spaces or letters (e.g. 220104020)."

    faculty = Faculty.query.get(faculty_id)
    if not faculty:
        return "Selected faculty does not exist."

    department = Department.query.filter_by(
        department_id=department_id, faculty_id=faculty_id
    ).first()
    if not department:
        return "Selected department does not belong to the chosen faculty."

    # Pad codes to 2 digits
    if parsed["faculty_code"] != faculty.faculty_code.zfill(2):
        return (
            f"Matric faculty code '{parsed['faculty_code']}' does not match "
            f"'{faculty.faculty_name}' (expected code {faculty.faculty_code.zfill(2)})."
        )

    if parsed["dept_code"] != department.department_code.zfill(2):
        return (
            f"Matric department code '{parsed['dept_code']}' does not match "
            f"'{department.department_name}' (expected code {department.department_code.zfill(2)})."
        )

    if parsed["serial"] == "000":
        return "Serial number (last 3 digits) cannot be 000."

    return None   # ✓ valid
