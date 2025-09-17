from flask import request
from . import db
from .models import AuditLog

def _client_ip():
    # ProxyFix適用済み。念のためX-Forwarded-Forを先頭優先で取得
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr

def log_action(user, action: str, target_type: str = None, target_id: int = None):
    role = getattr(user, "role", None)
    user_id = getattr(user, "id", None)
    ip = _client_ip()
    entry = AuditLog(user_id=user_id, role=role, action=action,
                     target_type=target_type, target_id=target_id, ip=ip)
    db.session.add(entry)
    db.session.commit()
