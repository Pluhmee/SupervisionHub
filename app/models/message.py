from app.extensions import db


class Message(db.Model):
    __tablename__ = "messages"

    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.project_id"), nullable=True
    )
    subject = db.Column(db.String(255), nullable=True)
    message_body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    sent_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Relationships
    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = db.relationship(
        "User", foreign_keys=[receiver_id], back_populates="received_messages"
    )
    project = db.relationship("Project", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.message_id} from {self.sender_id} to {self.receiver_id}>"
