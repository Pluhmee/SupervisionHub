from app.extensions import db


class Faculty(db.Model):
    __tablename__ = "faculties"

    faculty_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    faculty_name = db.Column(db.String(150), nullable=False, unique=True)
    faculty_code = db.Column(db.String(2),   nullable=False, unique=True)
    is_active    = db.Column(db.Boolean, nullable=False, default=True)
    created_at   = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    departments = db.relationship(
        "Department", back_populates="faculty",
        lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Faculty {self.faculty_code}: {self.faculty_name}>"
