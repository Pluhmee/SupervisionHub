from app.extensions import db
import enum


class MilestoneStatus(enum.Enum):
    pending   = "pending"
    submitted = "submitted"
    approved  = "approved"
    rejected  = "rejected"


class Milestone(db.Model):
    __tablename__ = "milestones"

    milestone_id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id            = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False)
    milestone_name        = db.Column(db.String(100), nullable=False)
    milestone_description = db.Column(db.Text, nullable=True)
    deadline              = db.Column(db.Date, nullable=True)
    status                = db.Column(db.Enum(MilestoneStatus), nullable=False,
                                      default=MilestoneStatus.pending)
    submitted_date        = db.Column(db.DateTime, nullable=True)
    feedback              = db.Column(db.Text, nullable=True)
    created_at            = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Chapter sequencing — 1-5 for the five project chapters, NULL for custom milestones
    chapter_order = db.Column(db.Integer, nullable=True)
    is_chapter    = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    project = db.relationship("Project", back_populates="milestones")

    # ----------------------------------------------------------------
    def is_locked(self) -> bool:
        """
        A chapter is locked if the previous chapter is not yet approved.
        Chapter 1 is never locked.
        Non-chapter milestones are never locked.
        """
        if not self.is_chapter or self.chapter_order == 1:
            return False
        prev = Milestone.query.filter_by(
            project_id=self.project_id,
            chapter_order=self.chapter_order - 1,
            is_chapter=True,
        ).first()
        if prev is None:
            return False
        return prev.status != MilestoneStatus.approved

    def __repr__(self):
        return f"<Milestone {self.milestone_name} [{self.status.value}]>"


# ----------------------------------------------------------------
# Fixed chapter definitions used when a project is first assigned
# ----------------------------------------------------------------
CHAPTER_DEFINITIONS = [
    {
        "order": 1,
        "name": "Chapter 1 — Introduction",
        "description": (
            "Background of the study, statement of the problem, aims and objectives, "
            "scope, significance, and definition of terms."
        ),
    },
    {
        "order": 2,
        "name": "Chapter 2 — Literature Review",
        "description": (
            "Review of related works, theoretical framework, conceptual framework, "
            "and gap in existing literature."
        ),
    },
    {
        "order": 3,
        "name": "Chapter 3 — Methodology",
        "description": (
            "Research design, system analysis, system design, tools and technologies, "
            "database design, and implementation plan."
        ),
    },
    {
        "order": 4,
        "name": "Chapter 4 — Implementation & Results",
        "description": (
            "System implementation, testing, results, screenshots, and discussion "
            "of findings."
        ),
    },
    {
        "order": 5,
        "name": "Chapter 5 — Conclusion & Recommendations",
        "description": (
            "Summary of work, conclusion, recommendations, limitations, "
            "and areas for future work."
        ),
    },
]


def create_chapters_for_project(project_id: int):
    """
    Auto-create the 5 chapter milestones for a project.
    Called by admin when assigning a supervisor.
    Safe to call multiple times — skips if chapters already exist.
    """
    from app.extensions import db as _db
    existing = Milestone.query.filter_by(
        project_id=project_id, is_chapter=True
    ).count()
    if existing > 0:
        return   # already created

    for ch in CHAPTER_DEFINITIONS:
        _db.session.add(Milestone(
            project_id            = project_id,
            milestone_name        = ch["name"],
            milestone_description = ch["description"],
            chapter_order         = ch["order"],
            is_chapter            = True,
            status                = MilestoneStatus.pending,
        ))