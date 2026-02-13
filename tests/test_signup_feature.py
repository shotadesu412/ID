
import pytest
from app import create_app, db
from app.models import User, School, ROLE_STUDENT

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Seed a school
            s = School(name="Test School")
            db.session.add(s)
            db.session.commit()
            yield client
            db.session.remove()
            db.drop_all()

def test_signup_flow(client):
    # 1. GET register page
    resp = client.get("/auth/register")
    assert resp.status_code == 200
    assert b"Test School" in resp.data

    # 2. POST valid data
    with client.application.app_context():
        school = School.query.first()
        sid = school.id

    resp = client.post("/auth/register", data=dict(
        email="newstudent@test.com",
        password="password123",
        confirm_password="password123",
        school_id=sid
    ), follow_redirects=True)

    assert resp.status_code == 200
    # Should be logged in and redirected to questions list
    # Because of redirects, we check content
    # If login is required for main.index -> questions.list, it will show questions list page content
    # or flash message "登録が完了しました"
    assert "登録が完了しました".encode("utf-8") in resp.data

    # Verify DB
    with client.application.app_context():
        u = User.query.filter_by(email="newstudent@test.com").first()
        assert u is not None
        assert u.role == ROLE_STUDENT
        assert u.school_id == sid

def test_signup_duplicate_email(client):
    # Seed user
    with client.application.app_context():
        s = School.query.first()
        u = User(email="dup@test.com", role=ROLE_STUDENT, school_id=s.id)
        u.set_password("p")
        db.session.add(u)
        db.session.commit()
        sid = s.id

    resp = client.post("/auth/register", data=dict(
        email="dup@test.com",
        password="p",
        confirm_password="p",
        school_id=sid
    ), follow_redirects=True)

    assert "このメールアドレスは既に登録されています".encode("utf-8") in resp.data
