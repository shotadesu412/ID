from app import create_app, db
from app.models import Question

app = create_app()
with app.app_context():
    # Get the latest question
    q = Question.query.order_by(Question.created_at.desc()).first()
    if q:
        print(f"ID: {q.id}")
        print(f"Status: {q.explanation_status}")
        print(f"Explanation Len: {len(q.explanation) if q.explanation else 0}")
        print(f"Explanation Content: '{q.explanation}'")
    else:
        print("No questions found.")
