from app.extensions import db


class Document(db.Model):
    __tablename__ = "documents"

    document_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    document_name = db.Column(db.String(255), nullable=False)
    document_path = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    document_size = db.Column(db.Integer, nullable=False)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    milestone_type = db.Column(db.String(100), nullable=True)
    upload_date = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Unique constraint: each project/version pair must be unique (append-only versioning)
    __table_args__ = (
        db.UniqueConstraint("project_id", "version_number", name="uq_project_version"),
    )

    # Relationships
    project = db.relationship("Project", back_populates="documents")
    uploader = db.relationship(
        "User", foreign_keys=[uploaded_by], back_populates="uploaded_documents"
    )

    @staticmethod
    def next_version(project_id):
        """Return the next version number for a given project (append-only)."""
        latest = (
            Document.query.filter_by(project_id=project_id)
            .order_by(Document.version_number.desc())
            .first()
        )
        return (latest.version_number + 1) if latest else 1

    @staticmethod
    def latest_for_project(project_id):
        """Return the most recent document version for a project."""
        return (
            Document.query.filter_by(project_id=project_id)
            .order_by(Document.version_number.desc())
            .first()
        )

    def __repr__(self):
        return f"<Document {self.document_name} v{self.version_number}>"
