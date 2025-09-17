from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from .models import User, School
from . import db
from .audit import log_action

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="pwd-reset")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            log_action(current_user, "login_success")
            flash("ログインしました", "success")
            return redirect(url_for("main.list_questions"))
        flash("メールまたはパスワードが違います", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("ログアウトしました", "info")
    return redirect(url_for("auth.login"))

# パスワードリセット（雛形／メールはダミー出力）
@auth_bp.route("/password/reset", methods=["GET","POST"])
def request_reset():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = _serializer().dumps({"uid": user.id})
            reset_url = url_for("auth.reset_with_token", token=token, _external=True)
            # ダミー送信: ログに出すだけ
            current_app.logger.info(f"[DUMMY MAIL] To={email} Reset URL={reset_url}")
            flash("パスワード再設定リンクを送信しました（ダミー）", "info")
        else:
            flash("該当メールが見つかりません", "warning")
    return render_template("request_reset.html")

@auth_bp.route("/password/reset/<token>", methods=["GET","POST"])
def reset_with_token(token):
    try:
        data = _serializer().loads(token, max_age=3600)
        uid = data["uid"]
    except SignatureExpired:
        flash("リンクの有効期限切れです", "danger")
        return redirect(url_for("auth.request_reset"))
    except BadSignature:
        flash("不正なトークンです", "danger")
        return redirect(url_for("auth.request_reset"))

    user = User.query.get(uid)
    if not user:
        flash("ユーザーが見つかりません", "danger")
        return redirect(url_for("auth.request_reset"))

    if request.method == "POST":
        pw1 = request.form.get("password","")
        pw2 = request.form.get("password2","")
        if not pw1 or pw1 != pw2:
            flash("パスワードが一致しません", "danger")
        else:
            user.set_password(pw1)
            db.session.commit()
            flash("パスワードを更新しました。ログインしてください。", "success")
            return redirect(url_for("auth.login"))
    return render_template("reset_password.html", user=user)
