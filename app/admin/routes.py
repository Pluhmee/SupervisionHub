from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.extensions import db, bcrypt
from app.models.user import User, UserType, UserStatus
from app.models.project import Project, ProjectStatus
from app.models.milestone import Milestone
from app.models.meeting import Meeting
from app.models.message import Message
from app.utils import role_required


# ---------------------------------------------------------------------------
# DASHBOARD  (FR-18)
# ---------------------------------------------------------------------------
@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    stats = {
        "total_users": User.query.count(),
        "total_students": User.query.filter_by(user_type=UserType.student).count(),
        "total_supervisors": User.query.filter_by(user_type=UserType.supervisor).count(),
        "total_projects": Project.query.count(),
        "active_projects": Project.query.filter_by(status=ProjectStatus.active).count(),
        "completed_projects": Project.query.filter_by(status=ProjectStatus.completed).count(),
        "unassigned_projects": Project.query.filter_by(supervisor_id=None).count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, recent_users=recent_users)


# ---------------------------------------------------------------------------
# USER MANAGEMENT  (FR-15)
# ---------------------------------------------------------------------------
@admin_bp.route("/users")
@login_required
@role_required("admin")
def users():
    role_filter = request.args.get("role", "")
    status_filter = request.args.get("status", "")
    query = User.query

    if role_filter and role_filter in [e.value for e in UserType]:
        query = query.filter_by(user_type=UserType[role_filter])
    if status_filter in ("active", "inactive"):
        query = query.filter_by(status=UserStatus[status_filter])

    all_users = query.order_by(User.created_at.desc()).all()
    return render_template(
        "admin/users.html",
        users=all_users,
        role_filter=role_filter,
        status_filter=status_filter,
    )


@admin_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@login_required
@role_required("admin")
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = UserStatus.active
    db.session.commit()
    flash(f"{user.full_name}'s account has been activated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@login_required
@role_required("admin")
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.user_type == UserType.admin:
        flash("Admin accounts cannot be deactivated here.", "danger")
        return redirect(url_for("admin.users"))
    user.status = UserStatus.inactive
    db.session.commit()
    flash(f"{user.full_name}'s account has been deactivated.", "warning")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_user():
    """Admin can manually create any user account."""
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user_type_str = request.form.get("user_type", "")
        department = request.form.get("department", "").strip()
        faculty = request.form.get("faculty", "").strip()
        matric_no = request.form.get("matric_no", "").strip() or None
        staff_id = request.form.get("staff_id", "").strip() or None
        phone = request.form.get("phone", "").strip() or None

        errors = []
        if not all([first_name, last_name, email, password, user_type_str, department, faculty]):
            errors.append("All required fields must be filled.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        try:
            user_type = UserType[user_type_str]
        except KeyError:
            errors.append("Invalid user type.")
            user_type = None

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("admin/create_user.html", form_data=request.form)

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_pw,
            user_type=user_type,
            department=department,
            faculty=faculty,
            matric_no=matric_no,
            staff_id=staff_id,
            phone=phone,
            status=UserStatus.active,
        )
        db.session.add(user)
        db.session.commit()
        flash(f"User {user.full_name} created successfully.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/create_user.html", form_data={})


# ---------------------------------------------------------------------------
# STUDENT–SUPERVISOR ASSIGNMENT  (FR-16)
# ---------------------------------------------------------------------------
@admin_bp.route("/assign")
@login_required
@role_required("admin")
def assign():
    unassigned_projects = Project.query.filter_by(supervisor_id=None).all()
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    supervisors = User.query.filter_by(
        user_type=UserType.supervisor, status=UserStatus.active
    ).all()
    return render_template(
        "admin/assign.html",
        projects=unassigned_projects,
        all_projects=all_projects,
        supervisors=supervisors,
    )


@admin_bp.route("/assign/submit", methods=["POST"])
@login_required
@role_required("admin")
def assign_submit():
    project_id = request.form.get("project_id", type=int)
    supervisor_id = request.form.get("supervisor_id", type=int)

    if not project_id or not supervisor_id:
        flash("Project and supervisor are required.", "danger")
        return redirect(url_for("admin.assign"))

    project = Project.query.get_or_404(project_id)
    supervisor = User.query.get_or_404(supervisor_id)

    if supervisor.user_type != UserType.supervisor:
        flash("Selected user is not a supervisor.", "danger")
        return redirect(url_for("admin.assign"))

    project.supervisor_id = supervisor_id
    if project.status == ProjectStatus.draft:
        project.status = ProjectStatus.active

    # Auto-create the 5 chapter milestones
    from app.models.milestone import create_chapters_for_project
    create_chapters_for_project(project.project_id)

    db.session.commit()
    flash(
        f"Project '{project.project_title}' assigned to {supervisor.full_name}.", "success"
    )
    return redirect(url_for("admin.assign"))


# ---------------------------------------------------------------------------
# MILESTONE MANAGEMENT  (FR-17 — configure milestones system-wide)
# ---------------------------------------------------------------------------
@admin_bp.route("/projects/<int:project_id>/milestones/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_milestone(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == "POST":
        from app.models.milestone import Milestone
        import datetime

        name = request.form.get("milestone_name", "").strip()
        description = request.form.get("milestone_description", "").strip() or None
        deadline_str = request.form.get("deadline", "") or None

        if not name:
            flash("Milestone name is required.", "danger")
            return render_template("admin/add_milestone.html", project=project)

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid deadline format.", "danger")
                return render_template("admin/add_milestone.html", project=project)

        milestone = Milestone(
            project_id=project_id,
            milestone_name=name,
            milestone_description=description,
            deadline=deadline,
        )
        db.session.add(milestone)
        db.session.commit()
        flash(f"Milestone '{name}' added.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_milestone.html", project=project)


# ---------------------------------------------------------------------------
# ALL PROJECTS VIEW
# ---------------------------------------------------------------------------
@admin_bp.route("/projects")
@login_required
@role_required("admin")
def projects():
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("admin/projects.html", projects=all_projects)


# ---------------------------------------------------------------------------
# FACULTY MANAGEMENT
# ---------------------------------------------------------------------------
@admin_bp.route("/faculties")
@login_required
@role_required("admin")
def faculties():
    from app.models.faculty import Faculty
    all_faculties = Faculty.query.order_by(Faculty.faculty_code).all()
    return render_template("admin/faculties.html", faculties=all_faculties)


@admin_bp.route("/faculties/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_faculty():
    from app.models.faculty import Faculty
    if request.method == "POST":
        name = request.form.get("faculty_name", "").strip()
        code = request.form.get("faculty_code", "").strip().zfill(2)
        if not name or not code:
            flash("Faculty name and code are required.", "danger")
            return redirect(url_for("admin.create_faculty"))
        if Faculty.query.filter_by(faculty_code=code).first():
            flash(f"Faculty code '{code}' already exists.", "danger")
            return redirect(url_for("admin.create_faculty"))
        db.session.add(Faculty(faculty_name=name, faculty_code=code))
        db.session.commit()
        flash(f"Faculty '{name}' created.", "success")
        return redirect(url_for("admin.faculties"))
    return render_template("admin/faculty_form.html", faculty=None)


@admin_bp.route("/faculties/<int:faculty_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_faculty(faculty_id):
    from app.models.faculty import Faculty
    faculty = Faculty.query.get_or_404(faculty_id)
    if request.method == "POST":
        faculty.faculty_name = request.form.get("faculty_name", "").strip()
        faculty.faculty_code = request.form.get("faculty_code", "").strip().zfill(2)
        faculty.is_active    = bool(request.form.get("is_active"))
        db.session.commit()
        flash("Faculty updated.", "success")
        return redirect(url_for("admin.faculties"))
    return render_template("admin/faculty_form.html", faculty=faculty)


# ---------------------------------------------------------------------------
# DEPARTMENT MANAGEMENT
# ---------------------------------------------------------------------------
@admin_bp.route("/faculties/<int:faculty_id>/departments")
@login_required
@role_required("admin")
def departments(faculty_id):
    from app.models.faculty import Faculty
    from app.models.department import Department
    faculty = Faculty.query.get_or_404(faculty_id)
    depts   = Department.query.filter_by(faculty_id=faculty_id).order_by(Department.department_code).all()
    return render_template("admin/departments.html", faculty=faculty, departments=depts)


@admin_bp.route("/faculties/<int:faculty_id>/departments/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_department(faculty_id):
    from app.models.faculty import Faculty
    from app.models.department import Department
    faculty = Faculty.query.get_or_404(faculty_id)
    if request.method == "POST":
        name = request.form.get("department_name", "").strip()
        code = request.form.get("department_code", "").strip().zfill(2)
        if not name or not code:
            flash("Department name and code are required.", "danger")
            return redirect(url_for("admin.create_department", faculty_id=faculty_id))
        if Department.query.filter_by(faculty_id=faculty_id, department_code=code).first():
            flash(f"Code '{code}' already exists in this faculty.", "danger")
            return redirect(url_for("admin.create_department", faculty_id=faculty_id))
        db.session.add(Department(faculty_id=faculty_id, department_name=name, department_code=code))
        db.session.commit()
        flash(f"Department '{name}' created.", "success")
        return redirect(url_for("admin.departments", faculty_id=faculty_id))
    return render_template("admin/department_form.html", faculty=faculty, department=None)


@admin_bp.route("/faculties/<int:faculty_id>/departments/<int:dept_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_department(faculty_id, dept_id):
    from app.models.faculty import Faculty
    from app.models.department import Department
    faculty = Faculty.query.get_or_404(faculty_id)
    dept    = Department.query.filter_by(department_id=dept_id, faculty_id=faculty_id).first_or_404()
    if request.method == "POST":
        dept.department_name = request.form.get("department_name", "").strip()
        dept.department_code = request.form.get("department_code", "").strip().zfill(2)
        dept.is_active       = bool(request.form.get("is_active"))
        db.session.commit()
        flash("Department updated.", "success")
        return redirect(url_for("admin.departments", faculty_id=faculty_id))
    return render_template("admin/department_form.html", faculty=faculty, department=dept)


# ---------------------------------------------------------------------------
# DOCUMENT DOWNLOAD (admin)
# ---------------------------------------------------------------------------
@admin_bp.route("/documents/<int:document_id>/download")
@login_required
@role_required("admin")
def download_document(document_id):
    from app.models.document import Document
    from flask import send_from_directory, current_app
    import os

    doc       = Document.query.get_or_404(document_id)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    filename   = os.path.basename(doc.document_path)

    if not os.path.exists(os.path.join(upload_dir, filename)):
        flash("File not found on server.", "danger")
        return redirect(url_for("admin.projects"))

    return send_from_directory(
        upload_dir,
        filename,
        as_attachment=True,
        download_name=doc.document_name,
    )