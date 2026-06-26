from app.extensions import db
import enum


class ProjectStatus(enum.Enum):
    draft = "draft"
    active = "active"
    completed = "completed"


class Project(db.Model):
    __tablename__ = "projects"

    project_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    project_title = db.Column(db.String(255), nullable=False)
    project_description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Enum(ProjectStatus), nullable=False, default=ProjectStatus.draft)
    overall_progress = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    # Relationships
    student = db.relationship("User", foreign_keys=[student_id], back_populates="student_projects")
    supervisor = db.relationship(
        "User", foreign_keys=[supervisor_id], back_populates="supervised_projects"
    )
    documents = db.relationship("Document", back_populates="project", lazy="dynamic")
    messages = db.relationship("Message", back_populates="project", lazy="dynamic")
    milestones = db.relationship("Milestone", back_populates="project", lazy="dynamic")
    meetings = db.relationship("Meeting", back_populates="project", lazy="dynamic")

def recalculate_progress(self):
    from app.models.milestone import Milestone, MilestoneStatus
    try:
        approved = Milestone.query.filter_by(
            project_id=self.project_id,
            is_chapter=True,
            status=MilestoneStatus.approved,
        ).count()
    except Exception:
        return
    self.overall_progress = approved * 20
    if approved == 5:
        self.status = ProjectStatus.completed

    def __repr__(self):
        return f"<Project {self.project_id}: {self.project_title}>"