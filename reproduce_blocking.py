
import time
import sys
import os
from unittest.mock import MagicMock, patch

# Add current dir to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Question, User
from app.tasks import analyze_image_task

def test_blocking_behavior():
    app = create_app()
    app.config['TESTING'] = True
    
    # Mock OpenAI to avoid real calls and simulate delay
    with patch('app.tasks.client') as mock_openai:
        # Create a mock response
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Test Explanation"
        mock_choice.finish_reason = "stop"
        mock_completion.choices = [mock_choice]
        
        # Simulate OpenAI taking 2 seconds
        def side_effect(*args, **kwargs):
            print("  [Mock OpenAI] Processing...")
            time.sleep(2)
            return mock_completion
            
        mock_openai.chat.completions.create.side_effect = side_effect

        with app.app_context():
            # Setup User and Question
            user = User.query.first()
            if not user:
                print("No user found, creating dummy user")
                user = User(email="test@example.com", password_hash="hash", role="student")
                db.session.add(user)
                db.session.commit()
                
            q = Question(content="test", user_id=user.id, school_id=1, explanation_status="processing")
            db.session.add(q)
            db.session.commit()
            q_id = q.id
            print(f"Created Question ID: {q_id}")

            print("Dispatching task...")
            start_time = time.time()
            
            # CALL THE TASK (This is what routes.py does)
            # Check if this blocks
            try:
                task = analyze_image_task.delay(q_id)
                print(f"Task dispatched. ID: {task.id}")
            except Exception as e:
                print(f"Task dispatch failed: {e}")
            
            end_time = time.time()
            duration = end_time - start_time
            print(f"Dispatch blocked for: {duration:.4f} seconds")
            
            if duration > 1.5:
                print("!! BLOCKING DETECTED !!")
            else:
                print("!! ASYNC DISPATCH CONFIRMED !!")

            # Check DB status immediately
            db.session.refresh(q)
            print(f"Question status immediately after dispatch: {q.explanation_status}")

            if duration > 1.5:
                # If blocked, task should be done effectively
                print(f"Question explanation after blocking: {q.explanation}")
                if q.explanation_status != 'completed':
                    print("!! STATUS NOT COMPLETED AFTER BLOCKING !!")
            
if __name__ == "__main__":
    test_blocking_behavior()
