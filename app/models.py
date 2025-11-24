from datetime import datetime
from flask_login import UserMixin
from . import db, login_manager
import bcrypt

ROLE_STUDENT = "student"
ROLE_MANAGER = "manager"
ROLE_HQ = "hq"
ROLE_CHOICES = (ROLE_STUDENT, ROLE_MANAGER, ROLE_HQ)

class School(db.Model):
    __tablename__ = "schools"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    school = db.relationship("School", backref="users")

    def set_password(self, raw: str):
        self.password_hash = bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, raw: str) -> bool:
        try:
            return bcrypt.checkpw(raw.encode("utf-8"), self.password_hash.encode("utf-8"))
        except Exception:
            return False

    @property
    def is_manager(self): return self.role == ROLE_MANAGER
    @property
    def is_hq(self): return self.role == ROLE_HQ
    @property
    def is_student(self): return self.role == ROLE_STUDENT

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="questions")
    school = db.relationship("School", backref="questions")

    # AI解説用フィールド
    image_path = db.Column(db.String(255), nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    explanation_status = db.Column(db.String(20), default="pending") # pending, processing, completed, failed

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    role = db.Column(db.String(20), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    target_type = db.Column(db.String(120), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip = db.Column(db.String(64), nullable=True)
