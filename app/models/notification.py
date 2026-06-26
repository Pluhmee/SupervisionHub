from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Relationships
    user = db.relationship("User", back_populates="notifications")

    @staticmethod
    def create(user_id, notification_type, title, message, link=None):
        """Factory helper — create and flush a notification without committing."""
        from app.extensions import db as _db
        n = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link,
        )
        _db.session.add(n)
        return n

    def __repr__(self):
        return f"<Notification {self.notification_id} [{self.notification_type}]>"
