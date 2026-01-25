
import sys
import os

# Ensure current dir is in path
sys.path.append(os.getcwd())

try:
    from app import celery
    # Mimic celery_worker.py
    import app.tasks
    
    print("Tasks registered:")
    found = False
    for task_name in celery.tasks.keys():
        print(f" - {task_name}")
        if 'analyze_image' in task_name:
            found = True
            print(f"FOUND MATCH: {task_name}")

    if not found:
        print("XXX MISSING: app.tasks.analyze_image_task XXX")
    else:
        print("SUCCESS: Task is registered")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
