import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_talisman import Talisman

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    from .config import Config
    app = Flask(__name__)
    app.config.from_object(Config())

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




