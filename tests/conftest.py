import pytest
from app import create_app, db
from app.models import User, School, ROLE_STUDENT, ROLE_MANAGER, ROLE_HQ

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,  # テスト時はCSRF無効化
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def seed_data(app):
    """テスト用データの投入"""
    s1 = School(name="Test School A")
    s2 = School(name="Test School B")
    db.session.add_all([s1, s2])
    db.session.commit()

    student = User(email="student@example.com", role=ROLE_STUDENT, school_id=s1.id)
    student.set_password("password")
    
    manager = User(email="manager@example.com", role=ROLE_MANAGER, school_id=s1.id)
    manager.set_password("password")
    
    hq = User(email="hq@example.com", role=ROLE_HQ, school_id=None)
    hq.set_password("password")

    db.session.add_all([student, manager, hq])
    db.session.commit()
    
    return {
        "school_a": s1,
        "school_b": s2,
        "student": student,
        "manager": manager,
        "hq": hq
    }
