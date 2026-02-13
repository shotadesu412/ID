
import pytest
from app import create_app, db
from app.models import User, School, ROLE_HQ, ROLE_STUDENT

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def login(client, email, password):
    return client.post("/auth/login", data=dict(
        email=email,
        password=password
    ), follow_redirects=True)

def test_admin_access(client):
    # Setup
    with client.application.app_context():
        # Create HQ user
        hq = User(email="hq@test.com", role=ROLE_HQ, school_id=None)
        hq.set_password("password")
        # Create Student
        st = User(email="student@test.com", role=ROLE_STUDENT, school_id=None)
        st.set_password("password")
        db.session.add_all([hq, st])
        db.session.commit()

    # 1. Access without login -> 302/401 (redirect to login)
    resp = client.get("/admin/schools", follow_redirects=True)
    assert b"Login" in resp.data

    # 2. Access as Student -> 403
    login(client, "student@test.com", "password")
    resp = client.get("/admin/schools")
    assert resp.status_code == 403

    # 3. Access as HQ -> 200
    login(client, "hq@test.com", "password")
    resp = client.get("/admin/schools")
    assert resp.status_code == 200
    assert b"School Management" in resp.data

def test_add_school(client):
    with client.application.app_context():
        hq = User(email="hq@test.com", role=ROLE_HQ, school_id=None)
        hq.set_password("password")
        db.session.add(hq)
        db.session.commit()

    login(client, "hq@test.com", "password")

    # Add school
    resp = client.post("/admin/schools", data=dict(name="New School A"), follow_redirects=True)
    assert resp.status_code == 200
    assert "学校「New School A」を追加しました".encode("utf-8") in resp.data or b"New School A" in resp.data

    # Verify in DB
    with client.application.app_context():
        assert School.query.filter_by(name="New School A").first() is not None

def test_delete_user(client):
    with client.application.app_context():
        hq = User(email="hq@test.com", role=ROLE_HQ, school_id=None)
        hq.set_password("password")
        target = User(email="target@test.com", role=ROLE_STUDENT, school_id=None)
        target.set_password("password")
        db.session.add_all([hq, target])
        db.session.commit()
        target_id = target.id

    login(client, "hq@test.com", "password")

    # Delete User
    resp = client.post("/admin/users", data=dict(user_id=target_id), follow_redirects=True)
    assert resp.status_code == 200
    assert b"target@test.com" in resp.data # Flash message or list might contain it?
    # Flash message should say deleted.
    
    # Verify in DB
    with client.application.app_context():
        assert User.query.get(target_id) is None
