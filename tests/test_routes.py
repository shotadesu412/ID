from app.models import Question, ROLE_STUDENT

def test_student_can_post_question(client, seed_data):
    # Login as student
    client.post("/auth/login", data={"email": "student@example.com", "password": "password"})

    response = client.post("/questions/new", data={
        "content": "This is a test question"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"This is a test question" in response.data
    
    # DB check
    q = Question.query.first()
    assert q.content == "This is a test question"
    assert q.user_id == seed_data["student"].id

def test_manager_can_view_school_questions(client, seed_data):
    # Setup: Student posts a question
    with client.application.app_context():
        q = Question(content="Q1", user_id=seed_data["student"].id, school_id=seed_data["school_a"].id)
        from app import db
        db.session.add(q)
        db.session.commit()

    # Login as manager (same school)
    client.post("/auth/login", data={"email": "manager@example.com", "password": "password"})
    
    response = client.get("/questions")
    assert response.status_code == 200
    assert b"Q1" in response.data

def test_csv_export(client, seed_data):
    # Login as HQ
    client.post("/auth/login", data={"email": "hq@example.com", "password": "password"})
    
    response = client.get("/export/questions.csv")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv; charset=utf-8"
