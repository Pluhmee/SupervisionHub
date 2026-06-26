from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app.supervisor import supervisor_bp
from app.extensions import db
from app.models.project import Project
from app.models.document import Document
from app.models.milestone import Milestone, MilestoneStatus
from app.models.message import Message
from app.models.meeting import Meeting, MeetingStatus
from app.models.notification import Notification
from app.utils import role_required, notify_and_email
from datetime import datetime


# ---------------------------------------------------------------------------
# DASHBOARD  (FR-09)
# ---------------------------------------------------------------------------
@supervisor_bp.route("/dashboard")
@login_required
@role_required("supervisor")
def dashboard():
    projects = current_user.supervised_projects.all()
    unread_notifications = (
        Notification.query.filter_by(user_id=current_user.user_id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )
    unread_messages_count = Message.query.filter_by(
        receiver_id=current_user.user_id, is_read=False
    ).count()
    pending_meetings = Meeting.query.filter_by(
        supervisor_id=current_user.user_id, status=MeetingStatus.requested
    ).count()
    return render_template(
        "supervisor/dashboard.html",
        projects=projects,
        notifications=unread_notifications,
        unread_messages_count=unread_messages_count,
        pending_meetings=pending_meetings,
    )


# ---------------------------------------------------------------------------
# PROJECT REVIEW  (FR-10, FR-11)
# ---------------------------------------------------------------------------
@supervisor_bp.route("/projects/<int:project_id>")
@login_required
@role_required("supervisor")
def review_project(project_id):
    project = _get_supervised_project(project_id)
    milestones = project.milestones.order_by(Milestone.created_at).all()
    documents = project.documents.order_by(Document.version_number.desc()).all()
    meetings = project.meetings.order_by(Meeting.meeting_date.desc()).all()
    return render_template(
        "supervisor/review_project.html",
        project=project,
        milestones=milestones,
        documents=documents,
        meetings=meetings,
    )


# ---------------------------------------------------------------------------
# MILESTONE APPROVE / REJECT  (FR-12)
# ---------------------------------------------------------------------------
@supervisor_bp.route("/milestones/<int:milestone_id>/approve", methods=["POST"])
@login_required
@role_required("supervisor")
def approve_milestone(milestone_id):
    milestone = _get_supervised_milestone(milestone_id)
    project = milestone.project

    if milestone.status != MilestoneStatus.submitted:
        flash("Only submitted milestones can be approved.", "warning")
        return redirect(url_for("supervisor.review_project", project_id=project.project_id))

    feedback_text = request.form.get("feedback", "").strip() or None
    milestone.status = MilestoneStatus.approved
    milestone.feedback = feedback_text
    db.session.flush()   # ← ADD THIS LINE

    # Recalculate project progress
    project.recalculate_progress()
    
    notify_and_email(
        project.student,
        notification_type="milestone_approved",
        title="Milestone approved",
        message=f"Your milestone '{milestone.milestone_name}' has been approved by {current_user.full_name}.",
        link=url_for("student.view_project", project_id=project.project_id),
    )

    db.session.commit()
    flash(f"Milestone '{milestone.milestone_name}' approved.", "success")
    return redirect(url_for("supervisor.review_project", project_id=project.project_id))


@supervisor_bp.route("/milestones/<int:milestone_id>/reject", methods=["POST"])
@login_required
@role_required("supervisor")
def reject_milestone(milestone_id):
    milestone = _get_supervised_milestone(milestone_id)
    project = milestone.project

    if milestone.status != MilestoneStatus.submitted:
        flash("Only submitted milestones can be rejected.", "warning")
        return redirect(url_for("supervisor.review_project", project_id=project.project_id))

    feedback_text = request.form.get("feedback", "").strip()
    if not feedback_text:
        flash("Feedback is required when rejecting a milestone.", "danger")
        return redirect(url_for("supervisor.review_project", project_id=project.project_id))

    milestone.status = MilestoneStatus.rejected
    milestone.feedback = feedback_text

    notify_and_email(
        project.student,
        notification_type="milestone_rejected",
        title="Milestone rejected",
        message=f"Your milestone '{milestone.milestone_name}' was rejected. Feedback: {feedback_text}",
        link=url_for("student.view_project", project_id=project.project_id),
    )

    db.session.commit()
    flash(f"Milestone '{milestone.milestone_name}' rejected.", "warning")
    return redirect(url_for("supervisor.review_project", project_id=project.project_id))


# ---------------------------------------------------------------------------
# MESSAGING  (FR-10 / FR-11)
# ---------------------------------------------------------------------------
@supervisor_bp.route("/messages")
@login_required
@role_required("supervisor")
def messages():
    inbox = (
        Message.query.filter_by(receiver_id=current_user.user_id)
        .order_by(Message.sent_at.desc())
        .all()
    )
    return render_template("supervisor/messages.html", inbox=inbox)


@supervisor_bp.route("/messages/send", methods=["GET", "POST"])
@login_required
@role_required("supervisor")
def send_message():
    if request.method == "POST":
        receiver_id = request.form.get("receiver_id", type=int)
        project_id = request.form.get("project_id", type=int) or None
        subject = request.form.get("subject", "").strip() or None
        body = request.form.get("message_body", "").strip()

        if not receiver_id or not body:
            flash("Receiver and message body are required.", "danger")
            return redirect(url_for("supervisor.send_message"))

        msg = Message(
            sender_id=current_user.user_id,
            receiver_id=receiver_id,
            project_id=project_id,
            subject=subject,
            message_body=body,
        )
        db.session.add(msg)

        from app.models.user import User
        receiver = User.query.get(receiver_id)
        if receiver:
            notify_and_email(
                receiver,
                notification_type="new_message",
                title=f"New message from {current_user.full_name}",
                message=body[:120],
                link=url_for("student.messages"),
            )

        db.session.commit()
        flash("Message sent.", "success")
        return redirect(url_for("supervisor.messages"))

    students = [p.student for p in current_user.supervised_projects.all()]
    return render_template("supervisor/send_message.html", students=students)


@supervisor_bp.route("/messages/<int:message_id>")
@login_required
@role_required("supervisor")
def view_message(message_id):
    msg = Message.query.filter_by(
        message_id=message_id, receiver_id=current_user.user_id
    ).first_or_404()
    if not msg.is_read:
        msg.is_read = True
        db.session.commit()
    return render_template("supervisor/view_message.html", message=msg)


# ---------------------------------------------------------------------------
# MEETINGS  (FR-13)
# ---------------------------------------------------------------------------
@supervisor_bp.route("/meetings")
@login_required
@role_required("supervisor")
def meetings():
    all_meetings = (
        Meeting.query.filter_by(supervisor_id=current_user.user_id)
        .order_by(Meeting.meeting_date.desc())
        .all()
    )
    return render_template("supervisor/meetings.html", meetings=all_meetings)


@supervisor_bp.route("/meetings/<int:meeting_id>/confirm", methods=["POST"])
@login_required
@role_required("supervisor")
def confirm_meeting(meeting_id):
    meeting = _get_supervised_meeting(meeting_id)
    if meeting.status != MeetingStatus.requested:
        flash("Only requested meetings can be confirmed.", "warning")
        return redirect(url_for("supervisor.meetings"))

    meeting.status = MeetingStatus.confirmed
    notify_and_email(
        meeting.student,
        notification_type="meeting_confirmed",
        title="Meeting confirmed",
        message=f"Your meeting on {meeting.meeting_date} at {meeting.meeting_time} has been confirmed.",
        link=url_for("student.meetings"),
    )
    db.session.commit()
    flash("Meeting confirmed.", "success")
    return redirect(url_for("supervisor.meetings"))


@supervisor_bp.route("/meetings/<int:meeting_id>/cancel", methods=["POST"])
@login_required
@role_required("supervisor")
def cancel_meeting(meeting_id):
    meeting = _get_supervised_meeting(meeting_id)
    if meeting.status in (MeetingStatus.completed, MeetingStatus.cancelled):
        flash("This meeting cannot be cancelled.", "warning")
        return redirect(url_for("supervisor.meetings"))

    meeting.status = MeetingStatus.cancelled
    notify_and_email(
        meeting.student,
        notification_type="meeting_cancelled",
        title="Meeting cancelled",
        message=f"Your meeting on {meeting.meeting_date} at {meeting.meeting_time} has been cancelled.",
        link=url_for("student.meetings"),
    )
    db.session.commit()
    flash("Meeting cancelled.", "warning")
    return redirect(url_for("supervisor.meetings"))


@supervisor_bp.route("/meetings/<int:meeting_id>/complete", methods=["POST"])
@login_required
@role_required("supervisor")
def complete_meeting(meeting_id):
    meeting = _get_supervised_meeting(meeting_id)
    notes = request.form.get("notes", "").strip() or None
    meeting.status = MeetingStatus.completed
    meeting.notes = notes
    db.session.commit()
    flash("Meeting marked as completed.", "success")
    return redirect(url_for("supervisor.meetings"))


# ---------------------------------------------------------------------------
# PROGRESS REPORT  (FR-14)
# ---------------------------------------------------------------------------
@supervisor_bp.route("/projects/<int:project_id>/report")
@login_required
@role_required("supervisor")
def progress_report(project_id):
    project = _get_supervised_project(project_id)
    milestones = project.milestones.order_by(Milestone.created_at).all()
    documents = project.documents.order_by(Document.version_number.desc()).all()
    meetings = project.meetings.filter_by(status=MeetingStatus.completed).all()
    return render_template(
        "supervisor/progress_report.html",
        project=project,
        milestones=milestones,
        documents=documents,
        meetings=meetings,
        generated_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# PRIVATE HELPERS
# ---------------------------------------------------------------------------
def _get_supervised_project(project_id: int) -> Project:
    project = Project.query.filter_by(
        project_id=project_id, supervisor_id=current_user.user_id
    ).first()
    if not project:
        abort(403)
    return project


def _get_supervised_milestone(milestone_id: int) -> Milestone:
    milestone = db.session.get(Milestone, milestone_id)
    if milestone is None:
        abort(404)
    if milestone.project.supervisor_id != current_user.user_id:
        abort(403)
    return milestone


def _get_supervised_meeting(meeting_id: int) -> Meeting:
    meeting = Meeting.query.filter_by(
        meeting_id=meeting_id, supervisor_id=current_user.user_id
    ).first_or_404()
    return meeting
