import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def _normalize_db_url(url: str, require_ssl: bool) -> str:
    # Heroku/古い形式の互換
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if require_ssl and parsed.scheme.startswith("postgresql"):
        if "sslmode" not in query:
            query["sslmode"] = ["require"]
        # Renderでもssl必須
    new_query = urlencode(query, doseq=True)
    normalized = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )
    return normalized

class Config:
    def __call__(self):
        # SECRET_KEY
        secret = os.getenv("SECRET_KEY", "dev-secret-change-me")

        # DB
        db_url_raw = os.getenv("DATABASE_URL", "sqlite:///local.db")
        environment = os.getenv("ENVIRONMENT", os.getenv("FLASK_ENV", "development"))
        require_db_ssl = os.getenv("REQUIRE_DB_SSL", "true" if environment == "production" else "false").lower() == "true"
        db_url = _normalize_db_url(db_url_raw, require_db_ssl)

        return {
            "SECRET_KEY": secret,
            "SQLALCHEMY_DATABASE_URI": db_url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "ENVIRONMENT": environment,
            # Cookie security (本番はSecure/HttpOnly)
            "SESSION_COOKIE_SECURE": environment == "production",
            "REMEMBER_COOKIE_SECURE": environment == "production",
            "SESSION_COOKIE_HTTPONLY": True,
            "REMEMBER_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
            # 役割関連設定
            "ALLOW_MANAGER_CROSS_SCHOOL": os.getenv("ALLOW_MANAGER_CROSS_SCHOOL", "false").lower() == "true",
            # Password reset (ダミー)
            "MAIL_FROM": os.getenv("MAIL_FROM", "no-reply@example.com"),
            # ページング
            "PAGE_SIZE": int(os.getenv("PAGE_SIZE", "20")),
        }
