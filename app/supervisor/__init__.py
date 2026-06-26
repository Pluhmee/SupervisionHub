from flask import Blueprint

supervisor_bp = Blueprint("supervisor", __name__, url_prefix="/supervisor")

from app.supervisor import routes  # noqa: E402, F401
