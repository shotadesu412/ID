import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, make_response
from flask_login import login_required, current_user
from .models import Question, User, School, ROLE_HQ, ROLE_MANAGER, ROLE_STUDENT
from .utils import require_roles, ensure_question_access_or_403, resolve_view_school_id
from .audit import log_action
from . import db

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return redirect(url_for("main.list_questions"))

@main_bp.route("/questions")
@login_required
def list_questions():
    # school 切替（権限チェック込み）
    requested_school_id = request.args.get("school_id")
    view_school_id = resolve_view_school_id(requested_school_id)

    q = Question.query
    if current_user.role == ROLE_STUDENT:
        q = q.filter(Question.user_id == current_user.id)
    elif current_user.role == ROLE_MANAGER:
        q = q.filter(Question.school_id == view_school_id)
    elif current_user.role == ROLE_HQ:
        if view_school_id:
            q = q.filter(Question.school_id == view_school_id)
    else:
        abort(403)

    q = q.order_by(Question.created_at.desc())

    # ページング
    page = max(int(request.args.get("page", 1)), 1)
    per_page = current_app.config["PAGE_SIZE"]
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)

    schools = None
    if current_user.role in (ROLE_MANAGER, ROLE_HQ):
        schools = School.query.order_by(School.name.asc()).all()

    log_action(current_user, "view_questions", target_type="school", target_id=view_school_id)
    return render_template("questions/list.html",
                           questions=pagination.items,
                           pagination=pagination,
                           schools=schools,
                           current_school_id=view_school_id)

@main_bp.route("/questions/new", methods=["GET","POST"])
@login_required
@require_roles(ROLE_STUDENT)  # 学生のみ投稿
def new_question():
    if request.method == "POST":
        content = request.form.get("content","").strip()
        if not content:
            flash("内容を入力してください", "warning")
        else:
            q = Question(content=content, user_id=current_user.id, school_id=current_user.school_id)
            db.session.add(q)
            db.session.commit()
            flash("質問を投稿しました", "success")
            return redirect(url_for("main.list_questions"))
    return render_template("questions/new.html")

@main_bp.route("/export/questions.csv")
@login_required
def export_questions_csv():
    requested_school_id = request.args.get("school_id")
    view_school_id = resolve_view_school_id(requested_school_id)

    q = Question.query
    if current_user.role == ROLE_STUDENT:
        q = q.filter(Question.user_id == current_user.id)
    elif current_user.role == ROLE_MANAGER:
        q = q.filter(Question.school_id == view_school_id)
    elif current_user.role == ROLE_HQ:
        if view_school_id:
            q = q.filter(Question.school_id == view_school_id)
    else:
        abort(403)

    # CSV生成
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "content", "user_email", "school_name", "created_at"])
    for row in q.join(User, User.id == Question.user_id)\
               .join(School, School.id == Question.school_id).all():
        writer.writerow([
            row.id, row.content,
            row.user.email if row.user else "",
            row.school.name if row.school else "",
            row.created_at.isoformat()
        ])

    csv_bytes = output.getvalue().encode("utf-8")
    response = make_response(csv_bytes)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=questions.csv"

    log_action(current_user, "export_questions", target_type="school", target_id=view_school_id)
    return response
