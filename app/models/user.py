from flask_login import UserMixin
from app.extensions import db, login_manager
import enum


class UserType(enum.Enum):
    student = "student"
    supervisor = "supervisor"
    admin = "admin"


class UserStatus(enum.Enum):
    active = "active"
    inactive = "inactive"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    matric_no = db.Column(db.String(20), unique=True, nullable=True)
    staff_id = db.Column(db.String(20), unique=True, nullable=True)
    department = db.Column(db.String(100), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.Enum(UserStatus), nullable=False, default=UserStatus.active)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Relationships
    # Projects where this user is the student
    student_projects = db.relationship(
        "Project",
        foreign_keys="Project.student_id",
        back_populates="student",
        lazy="dynamic",
    )
    # Projects where this user is the supervisor
    supervised_projects = db.relationship(
        "Project",
        foreign_keys="Project.supervisor_id",
        back_populates="supervisor",
        lazy="dynamic",
    )
    sent_messages = db.relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender", lazy="dynamic"
    )
    received_messages = db.relationship(
        "Message", foreign_keys="Message.receiver_id", back_populates="receiver", lazy="dynamic"
    )
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")
    uploaded_documents = db.relationship(
        "Document", foreign_keys="Document.uploaded_by", back_populates="uploader", lazy="dynamic"
    )
    student_meetings = db.relationship(
        "Meeting", foreign_keys="Meeting.student_id", back_populates="student", lazy="dynamic"
    )
    supervisor_meetings = db.relationship(
        "Meeting",
        foreign_keys="Meeting.supervisor_id",
        back_populates="supervisor",
        lazy="dynamic",
    )

    # Flask-Login requires get_id() to return a string
    def get_id(self):
        return str(self.user_id)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email} [{self.user_type.value}]>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
