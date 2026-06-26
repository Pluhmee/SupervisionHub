from flask import jsonify, request
from flask_login import login_required, current_user
from app.api import api_bp
from app.extensions import db
from app.models.notification import Notification
from app.models.message import Message


# ---------------------------------------------------------------------------
# NOTIFICATIONS
# ---------------------------------------------------------------------------
@api_bp.route("/notifications/unread")
@login_required
def unread_notifications():
    """AJAX: return unread notification count and latest 5 items."""
    notifications = (
        Notification.query.filter_by(user_id=current_user.user_id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )
    count = Notification.query.filter_by(
        user_id=current_user.user_id, is_read=False
    ).count()
    return jsonify(
        {
            "count": count,
            "notifications": [
                {
                    "id": n.notification_id,
                    "type": n.notification_type,
                    "title": n.title,
                    "message": n.message,
                    "link": n.link,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in notifications
            ],
        }
    )


@api_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    notif = Notification.query.filter_by(
        notification_id=notification_id, user_id=current_user.user_id
    ).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({"status": "ok"})


@api_bp.route("/notifications/mark-all-read", methods=["POST"])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(
        user_id=current_user.user_id, is_read=False
    ).update({"is_read": True})
    db.session.commit()
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# MESSAGES
# ---------------------------------------------------------------------------
@api_bp.route("/messages/unread-count")
@login_required
def unread_message_count():
    count = Message.query.filter_by(
        receiver_id=current_user.user_id, is_read=False
    ).count()
    return jsonify({"count": count})


# ---------------------------------------------------------------------------
# FACULTIES & DEPARTMENTS  (public — no login required, used on register page)
# ---------------------------------------------------------------------------
@api_bp.route("/faculties")
def get_faculties():
    """Return all active faculties."""
    from app.models.faculty import Faculty
    faculties = Faculty.query.filter_by(is_active=True).order_by(Faculty.faculty_name).all()
    return jsonify([
        {"id": f.faculty_id, "name": f.faculty_name, "code": f.faculty_code}
        for f in faculties
    ])


@api_bp.route("/faculties/<int:faculty_id>/departments")
def get_departments(faculty_id):
    """Return active departments for a faculty (cascading dropdown AJAX)."""
    from app.models.department import Department
    departments = (
        Department.query
        .filter_by(faculty_id=faculty_id, is_active=True)
        .order_by(Department.department_name)
        .all()
    )
    return jsonify([
        {"id": d.department_id, "name": d.department_name, "code": d.department_code}
        for d in departments
    ])
