from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.extensions import db, bcrypt
from app.models.user import User, UserType, UserStatus
from app.models.faculty import Faculty
from app.models.department import Department
from app.utils import validate_matric_against_selection


# ---------------------------------------------------------------------------
# REGISTER
# ---------------------------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    # Faculties for initial page load (departments load via AJAX)
    faculties = Faculty.query.filter_by(is_active=True).order_by(Faculty.faculty_name).all()

    if request.method == "POST":
        first_name    = request.form.get("first_name", "").strip()
        last_name     = request.form.get("last_name", "").strip()
        email         = request.form.get("email", "").strip().lower()
        password      = request.form.get("password", "")
        confirm_pw    = request.form.get("confirm_password", "")
        user_type_str = request.form.get("user_type", "")
        phone         = request.form.get("phone", "").strip() or None
        matric_no     = request.form.get("matric_no", "").strip() or None
        staff_id      = request.form.get("staff_id", "").strip() or None
        faculty_id_str    = request.form.get("faculty_id", "").strip()
        department_id_str = request.form.get("department_id", "").strip()

        errors = []

        # Basic presence
        if not all([first_name, last_name, email, password, user_type_str]):
            errors.append("All required fields must be filled.")

        if not faculty_id_str or not department_id_str:
            errors.append("Please select both a faculty and a department.")

        if password != confirm_pw:
            errors.append("Passwords do not match.")

        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")

        # Role
        try:
            user_type = UserType[user_type_str]
        except KeyError:
            errors.append("Invalid user type selected.")
            user_type = None

        # Resolve faculty & department objects
        faculty_obj = department_obj = None
        if faculty_id_str and department_id_str:
            try:
                faculty_obj = Faculty.query.get(int(faculty_id_str))
                department_obj = Department.query.filter_by(
                    department_id=int(department_id_str),
                    faculty_id=int(faculty_id_str)
                ).first()
            except (ValueError, TypeError):
                pass

        if not faculty_obj:
            errors.append("Selected faculty is invalid.")
        if not department_obj:
            errors.append("Selected department is invalid or does not belong to the chosen faculty.")

        # Student: matric required + dummy validation
        if user_type == UserType.student:
            if not matric_no:
                errors.append("Matriculation number is required for students.")
            elif faculty_obj and department_obj:
                err = validate_matric_against_selection(
                    matric_no, faculty_obj.faculty_id, department_obj.department_id
                )
                if err:
                    errors.append(err)

        # Supervisor: staff ID required
        if user_type == UserType.supervisor and not staff_id:
            errors.append("Staff ID is required for supervisors.")

        # Uniqueness
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if matric_no and User.query.filter_by(matric_no=matric_no).first():
            errors.append("This matriculation number is already registered.")
        if staff_id and User.query.filter_by(staff_id=staff_id).first():
            errors.append("This staff ID is already registered.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "auth/register.html",
                form_data=request.form,
                faculties=faculties,
            )

        # Create user — store resolved names from DB, not raw text
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            first_name  = first_name,
            last_name   = last_name,
            email       = email,
            password    = hashed_pw,
            user_type   = user_type,
            department  = department_obj.department_name,
            faculty     = faculty_obj.faculty_name,
            phone       = phone,
            matric_no   = matric_no,
            staff_id    = staff_id,
            status      = UserStatus.active,
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form_data={}, faculties=faculties)


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember_me"))

        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.check_password_hash(user.password, password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        if user.status == UserStatus.inactive:
            flash("Your account is deactivated. Contact the administrator.", "danger")
            return render_template("auth/login.html")

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.first_name}!", "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return _redirect_by_role(user)

    return render_template("auth/login.html")


# ---------------------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------------
# HELPER
# ---------------------------------------------------------------------------
def _redirect_by_role(user):
    role_map = {
        UserType.student:    "student.dashboard",
        UserType.supervisor: "supervisor.dashboard",
        UserType.admin:      "admin.dashboard",
    }
    return redirect(url_for(role_map[user.user_type]))
