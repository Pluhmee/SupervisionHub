from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app.student import student_bp
from app.extensions import db
from app.models.project import Project, ProjectStatus
from app.models.document import Document
from app.models.milestone import Milestone, MilestoneStatus
from app.models.message import Message
from app.models.meeting import Meeting, MeetingStatus
from app.models.notification import Notification
from app.utils import role_required, save_uploaded_file, allowed_file, notify_and_email, get_file_extension


# ---------------------------------------------------------------------------
# DASHBOARD  (FR-06)
# ---------------------------------------------------------------------------
@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    projects = current_user.student_projects.all()
    unread_notifications = (
        Notification.query.filter_by(user_id=current_user.user_id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )
    unread_messages_count = Message.query.filter_by(
        receiver_id=current_user.user_id, is_read=False
    ).count()
    return render_template(
        "student/dashboard.html",
        projects=projects,
        notifications=unread_notifications,
        unread_messages_count=unread_messages_count,
    )


# ---------------------------------------------------------------------------
# PROJECT MANAGEMENT  (FR-03)
# ---------------------------------------------------------------------------
@student_bp.route("/projects/create", methods=["GET", "POST"])
@login_required
@role_required("student")
def create_project():
    if request.method == "POST":
        title = request.form.get("project_title", "").strip()
        description = request.form.get("project_description", "").strip() or None
        category = request.form.get("category", "").strip() or None

        if not title:
            flash("Project title is required.", "danger")
            return render_template("student/create_project.html")

        project = Project(
            student_id=current_user.user_id,
            project_title=title,
            project_description=description,
            category=category,
            status=ProjectStatus.draft,
        )
        db.session.add(project)
        db.session.commit()
        flash("Project created successfully.", "success")
        return redirect(url_for("student.view_project", project_id=project.project_id))

    return render_template("student/create_project.html")


@student_bp.route("/projects/<int:project_id>")
@login_required
@role_required("student")
def view_project(project_id):
    project = _get_student_project(project_id)
    milestones = project.milestones.order_by(Milestone.created_at).all()
    documents = project.documents.order_by(Document.version_number.desc()).all()
    meetings = project.meetings.order_by(Meeting.meeting_date.desc()).all()
    return render_template(
        "student/project.html",
        project=project,
        milestones=milestones,
        documents=documents,
        meetings=meetings,
    )


# ---------------------------------------------------------------------------
# DOCUMENT UPLOAD WITH VERSIONING  (FR-04)
# ---------------------------------------------------------------------------
@student_bp.route("/projects/<int:project_id>/documents/upload", methods=["POST"])
@login_required
@role_required("student")
def upload_document(project_id):
    project = _get_student_project(project_id)

    if "file" not in request.files or request.files["file"].filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("student.view_project", project_id=project_id))

    file = request.files["file"]

    if not allowed_file(file.filename):
        flash("File type not allowed. Accepted: pdf, doc, docx, png, jpg, jpeg.", "danger")
        return redirect(url_for("student.view_project", project_id=project_id))

    unique_name, relative_path, file_size = save_uploaded_file(file)

    next_version = Document.next_version(project_id)
    # Link document to a chapter if the student selected one
    milestone_type = request.form.get("milestone_type", "").strip() or None
    chapter_id_str = request.form.get("chapter_id", "").strip()
    if chapter_id_str:
        try:
            from app.models.milestone import Milestone
            ch = Milestone.query.filter_by(
                milestone_id=int(chapter_id_str),
                project_id=project_id
            ).first()
            if ch:
                milestone_type = ch.milestone_name
        except (ValueError, TypeError):
            pass

    doc = Document(
        project_id=project_id,
        uploaded_by=current_user.user_id,
        document_name=file.filename,
        document_path=relative_path,
        document_type=get_file_extension(file.filename),
        document_size=file_size,
        version_number=next_version,
        milestone_type=milestone_type,
    )
    db.session.add(doc)

    # Notify supervisor if assigned
    if project.supervisor:
        notify_and_email(
            project.supervisor,
            notification_type="document_uploaded",
            title="New document uploaded",
            message=f"{current_user.full_name} uploaded a new document (v{next_version}) for project: {project.project_title}",
            link=url_for("supervisor.review_project", project_id=project_id),
        )

    db.session.commit()
    flash(f"Document uploaded successfully (version {next_version}).", "success")
    return redirect(url_for("student.view_project", project_id=project_id))


# ---------------------------------------------------------------------------
# MILESTONE SUBMISSION  (FR-05)
# ---------------------------------------------------------------------------
@student_bp.route("/projects/<int:project_id>/milestones/<int:milestone_id>/submit", methods=["POST"])
@login_required
@role_required("student")
def submit_milestone(project_id, milestone_id):
    project = _get_student_project(project_id)
    milestone = Milestone.query.filter_by(
        milestone_id=milestone_id, project_id=project_id
    ).first_or_404()

    if milestone.status not in (MilestoneStatus.pending, MilestoneStatus.rejected):
        flash("This milestone cannot be submitted in its current state.", "warning")
        return redirect(url_for("student.view_project", project_id=project_id))

    if milestone.is_locked():
        flash(
            f"Complete Chapter {milestone.chapter_order - 1} first "
            f"before submitting Chapter {milestone.chapter_order}.",
            "warning",
        )
        return redirect(url_for("student.view_project", project_id=project_id))

    milestone.status = MilestoneStatus.submitted
    milestone.submitted_date = datetime.utcnow()

    if project.supervisor:
        notify_and_email(
            project.supervisor,
            notification_type="milestone_submitted",
            title="Milestone submitted for review",
            message=f"{current_user.full_name} submitted milestone '{milestone.milestone_name}' for project: {project.project_title}",
            link=url_for("supervisor.review_project", project_id=project_id),
        )

    db.session.commit()
    flash(f"Milestone '{milestone.milestone_name}' submitted for review.", "success")
    return redirect(url_for("student.view_project", project_id=project_id))


# ---------------------------------------------------------------------------
# MESSAGING  (FR-07)
# ---------------------------------------------------------------------------
@student_bp.route("/messages")
@login_required
@role_required("student")
def messages():
    inbox = (
        Message.query.filter_by(receiver_id=current_user.user_id)
        .order_by(Message.sent_at.desc())
        .all()
    )
    return render_template("student/messages.html", inbox=inbox)


@student_bp.route("/messages/send", methods=["GET", "POST"])
@login_required
@role_required("student")
def send_message():
    if request.method == "POST":
        receiver_id = request.form.get("receiver_id", type=int)
        project_id = request.form.get("project_id", type=int) or None
        subject = request.form.get("subject", "").strip() or None
        body = request.form.get("message_body", "").strip()

        if not receiver_id or not body:
            flash("Receiver and message body are required.", "danger")
            return redirect(url_for("student.send_message"))

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
                link=url_for("supervisor.messages"),
            )

        db.session.commit()
        flash("Message sent successfully.", "success")
        return redirect(url_for("student.messages"))

    # Load supervisors for the dropdown (only those supervising this student)
    projects = current_user.student_projects.all()
    supervisors = [p.supervisor for p in projects if p.supervisor]
    return render_template("student/send_message.html", supervisors=supervisors)


@student_bp.route("/messages/<int:message_id>")
@login_required
@role_required("student")
def view_message(message_id):
    msg = Message.query.filter_by(
        message_id=message_id, receiver_id=current_user.user_id
    ).first_or_404()
    if not msg.is_read:
        msg.is_read = True
        db.session.commit()
    return render_template("student/view_message.html", message=msg)


# ---------------------------------------------------------------------------
# MEETING REQUEST  (FR-08)
# ---------------------------------------------------------------------------
@student_bp.route("/meetings")
@login_required
@role_required("student")
def meetings():
    all_meetings = (
        Meeting.query.filter_by(student_id=current_user.user_id)
        .order_by(Meeting.meeting_date.desc())
        .all()
    )
    return render_template("student/meetings.html", meetings=all_meetings)


@student_bp.route("/meetings/request", methods=["GET", "POST"])
@login_required
@role_required("student")
def request_meeting():
    projects = [p for p in current_user.student_projects.all() if p.supervisor]

    if request.method == "POST":
        project_id = request.form.get("project_id", type=int)
        meeting_date_str = request.form.get("meeting_date", "")
        meeting_time_str = request.form.get("meeting_time", "")
        location = request.form.get("location", "").strip() or None
        agenda = request.form.get("agenda", "").strip() or None

        if not all([project_id, meeting_date_str, meeting_time_str]):
            flash("Project, date, and time are required.", "danger")
            return render_template("student/request_meeting.html", projects=projects)

        project = _get_student_project(project_id)
        if not project.supervisor:
            flash("No supervisor is assigned to this project yet.", "warning")
            return render_template("student/request_meeting.html", projects=projects)

        try:
            meeting_date = datetime.strptime(meeting_date_str, "%Y-%m-%d").date()
            meeting_time = datetime.strptime(meeting_time_str, "%H:%M").time()
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return render_template("student/request_meeting.html", projects=projects)

        meeting = Meeting(
            student_id=current_user.user_id,
            supervisor_id=project.supervisor_id,
            project_id=project_id,
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            location=location,
            agenda=agenda,
            status=MeetingStatus.requested,
        )
        db.session.add(meeting)

        notify_and_email(
            project.supervisor,
            notification_type="meeting_request",
            title="Meeting requested",
            message=f"{current_user.full_name} has requested a meeting on {meeting_date} at {meeting_time} for project: {project.project_title}",
            link=url_for("supervisor.meetings"),
        )

        db.session.commit()
        flash("Meeting request sent to your supervisor.", "success")
        return redirect(url_for("student.meetings"))

    return render_template("student/request_meeting.html", projects=projects)


# ---------------------------------------------------------------------------
# NOTIFICATIONS
# ---------------------------------------------------------------------------
@student_bp.route("/notifications/mark-read/<int:notification_id>", methods=["POST"])
@login_required
@role_required("student")
def mark_notification_read(notification_id):
    notif = Notification.query.filter_by(
        notification_id=notification_id, user_id=current_user.user_id
    ).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# PRIVATE HELPER
# ---------------------------------------------------------------------------
def _get_student_project(project_id: int) -> Project:
    """Return a project that belongs to the current student, or 403."""
    project = Project.query.filter_by(
        project_id=project_id, student_id=current_user.user_id
    ).first()
    if not project:
        abort(403)
    return project


# ---------------------------------------------------------------------------
# DOCUMENT DOWNLOAD / VIEW  — shared secure route for all roles
# ---------------------------------------------------------------------------
from flask import send_from_directory, current_app
import os

@student_bp.route("/documents/<int:document_id>/download")
@login_required
def download_document(document_id):
    """
    Secure file download. Accessible by:
      - The student who owns the project
      - The supervisor assigned to the project
      - Admin users
    """
    from app.models.document import Document
    from app.models.user import UserType

    doc = Document.query.get_or_404(document_id)
    project = doc.project
    user = current_user

    # Access control
    is_student     = (user.user_type == UserType.student and
                      project.student_id == user.user_id)
    is_supervisor  = (user.user_type == UserType.supervisor and
                      project.supervisor_id == user.user_id)
    is_admin       = (user.user_type == UserType.admin)

    if not (is_student or is_supervisor or is_admin):
        abort(403)

    # doc.document_path is stored as "uploads/documents/uuid_filename.pdf"
    upload_dir = current_app.config["UPLOAD_FOLDER"]   # absolute path to uploads/documents/
    filename   = os.path.basename(doc.document_path)

    if not os.path.exists(os.path.join(upload_dir, filename)):
        flash("File not found on server. It may have been removed.", "danger")
        from flask import redirect, request as req
        return redirect(req.referrer or url_for("student.dashboard"))

    return send_from_directory(
        upload_dir,
        filename,
        as_attachment=True,
        download_name=doc.document_name,   # restores original filename for download
    )


# ---------------------------------------------------------------------------
# SUBMIT CHAPTER  — combined upload + milestone submit in one POST
# ---------------------------------------------------------------------------
@student_bp.route(
    "/projects/<int:project_id>/chapters/<int:milestone_id>/submit",
    methods=["POST"]
)
@login_required
@role_required("student")
def submit_chapter(project_id, milestone_id):
    from app.models.milestone import Milestone, MilestoneStatus
    from app.utils import save_uploaded_file, allowed_file, get_file_extension
    from app.models.document import Document
    from datetime import datetime

    project   = _get_student_project(project_id)
    milestone = Milestone.query.filter_by(
        milestone_id=milestone_id, project_id=project_id
    ).first_or_404()

    # Guard: sequential lock
    if milestone.is_locked():
        flash(
            f"Complete Chapter {milestone.chapter_order - 1} first "
            f"before submitting Chapter {milestone.chapter_order}.",
            "warning"
        )
        return redirect(url_for("student.view_project", project_id=project_id))

    # Guard: only pending or rejected can be submitted
    if milestone.status not in (MilestoneStatus.pending, MilestoneStatus.rejected):
        flash("This chapter cannot be submitted in its current state.", "warning")
        return redirect(url_for("student.view_project", project_id=project_id))

    # File is required
    if "file" not in request.files or request.files["file"].filename == "":
        flash("Please attach a document before submitting.", "danger")
        return redirect(url_for("student.view_project", project_id=project_id))

    file = request.files["file"]
    if not allowed_file(file.filename):
        flash("File type not allowed. Use PDF, DOC, or DOCX.", "danger")
        return redirect(url_for("student.view_project", project_id=project_id))

    # Save file
    _, relative_path, file_size = save_uploaded_file(file)
    next_version = Document.next_version(project_id)
    note = request.form.get("note", "").strip() or None

    doc = Document(
        project_id     = project_id,
        uploaded_by    = current_user.user_id,
        document_name  = file.filename,
        document_path  = relative_path,
        document_type  = get_file_extension(file.filename),
        document_size  = file_size,
        version_number = next_version,
        milestone_type = milestone.milestone_name,
    )
    db.session.add(doc)

    # Mark chapter submitted
    milestone.status         = MilestoneStatus.submitted
    milestone.submitted_date = datetime.utcnow()
    if note:
        milestone.feedback = f"[Student note]: {note}"


    # Notify supervisor
    if project.supervisor:
        notify_and_email(
            project.supervisor,
            notification_type="chapter_submitted",
            title=f"Chapter submitted: {milestone.milestone_name}",
            message=(
                f"{current_user.full_name} submitted {milestone.milestone_name} "
                f"for project: {project.project_title}"
            ),
            link=url_for(
                "supervisor.review_project", project_id=project_id
            ),
        )

    db.session.commit()
    flash(
        f"{milestone.milestone_name} submitted successfully. "
        f"Awaiting supervisor review.",
        "success"
    )
    return redirect(url_for("student.view_project", project_id=project_id))