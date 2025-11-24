from app.config import Config
try:
    c = Config()()
    print("Config generated successfully")
    print(c["SQLALCHEMY_DATABASE_URI"])
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
