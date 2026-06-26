from app.extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    department_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    faculty_id      = db.Column(db.Integer, db.ForeignKey("faculties.faculty_id"), nullable=False)
    department_name = db.Column(db.String(150), nullable=False)
    department_code = db.Column(db.String(2),   nullable=False)
    is_active       = db.Column(db.Boolean, nullable=False, default=True)
    created_at      = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    __table_args__ = (
        db.UniqueConstraint("faculty_id", "department_code", name="uq_faculty_dept_code"),
    )

    faculty = db.relationship("Faculty", back_populates="departments")

    def __repr__(self):
        return f"<Department {self.department_code}: {self.department_name}>"
