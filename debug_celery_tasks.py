
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.getcwd())

print("Attempting to import celery_worker...")
try:
    import celery_worker
    print("Successfully imported celery_worker")
except Exception as e:
    print(f"Failed to import celery_worker: {e}")
    sys.exit(1)

celery_app = celery_worker.celery
print(f"Celery App Name: {celery_app.main}")

print("\n--- Registered Tasks ---")
found = False
for task_name in celery_app.tasks.keys():
    print(f"- {task_name}")
    if task_name == 'app.tasks.analyze_image_task':
        found = True

print("------------------------")

if found:
    print("SUCCESS: 'app.tasks.analyze_image_task' found in registry.")
else:
    print("FAILURE: 'app.tasks.analyze_image_task' NOT found in registry.")
