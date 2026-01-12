import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_talisman import Talisman
from celery import Celery

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
celery = Celery(__name__)

def create_app():
    from .config import Config
    app = Flask(__name__)
    app.config.from_mapping(Config()())

    # Celery config
    broker_url = app.config.get("CELERY_BROKER_URL")
    if not broker_url:
        print("WARNING: CELERY_BROKER_URL not found in app.config, using env var or localhost fallback")
        broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    print(f"DEBUG: Celery Broker URL directly from Config: {broker_url}")

    # Force update with both new and old style keys to be safe
    celery.conf.update(
        broker_url=broker_url,
        result_backend=app.config.get("CELERY_RESULT_BACKEND", broker_url),
        broker_use_ssl=app.config.get("CELERY_BROKER_USE_SSL"),
        redis_backend_use_ssl=app.config.get("CELERY_REDIS_BACKEND_USE_SSL"),
        # Legacy/Alternative keys
        BROKER_URL=broker_url,
        CELERY_BROKER_URL=broker_url,
        CELERY_RESULT_BACKEND=app.config.get("CELERY_RESULT_BACKEND", broker_url),
    )
    # Ensure transport is not overridden or cached
    if broker_url.startswith("redis"):
        print("DEBUG: Enforcing Redis transport") 
        # celery.conf.broker_transport = 'redis' # Optional, usually auto-detected

    print(f"DEBUG: Final Celery Conf Broker: {celery.conf.broker_url}")

    # Proxy (Render等のリバースプロキシ配下)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"

    # セキュリティヘッダ（本番のみ HTTPS 強制）
    if app.config.get("ENVIRONMENT") == "production":
        Talisman(app, content_security_policy=None, force_https=True)

    # Blueprints
    from .auth import auth_bp
    from .routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app





