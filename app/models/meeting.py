from app.extensions import db
import enum


class MeetingStatus(enum.Enum):
    requested = "requested"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class Meeting(db.Model):
    __tablename__ = "meetings"

    meeting_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    meeting_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    agenda = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(MeetingStatus), nullable=False, default=MeetingStatus.requested
    )
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Relationships
    student = db.relationship(
        "User", foreign_keys=[student_id], back_populates="student_meetings"
    )
    supervisor = db.relationship(
        "User", foreign_keys=[supervisor_id], back_populates="supervisor_meetings"
    )
    project = db.relationship("Project", back_populates="meetings")

    def __repr__(self):
        return f"<Meeting {self.meeting_id} on {self.meeting_date} [{self.status.value}]>"
