from functools import wraps
from flask import abort, current_app, request
from flask_login import current_user
from .models import ROLE_HQ, ROLE_MANAGER, ROLE_STUDENT, Question

def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def ensure_question_access_or_403(question: Question):
    if current_user.role == ROLE_HQ:
        return
    if current_user.role == ROLE_MANAGER:
        if question.school_id != current_user.school_id:
            abort(403)
        return
    if current_user.role == ROLE_STUDENT:
        if question.user_id != current_user.id:
            abort(403)
        return
    abort(403)

def resolve_view_school_id(param_value: str):
    """list画面のschool切替の正当性チェック"""
    allow_manager_cross = current_app.config.get("ALLOW_MANAGER_CROSS_SCHOOL", False)
    sid = None
    try:
        sid = int(param_value) if param_value else None
    except Exception:
        sid = None

    if current_user.role == ROLE_HQ:
        return sid  # 任意切替可
    if current_user.role == ROLE_MANAGER:
        if allow_manager_cross and sid:
            return sid
        # 既定は自校舎のみ
        return current_user.school_id
    if current_user.role == ROLE_STUDENT:
        return current_user.school_id
    return None
