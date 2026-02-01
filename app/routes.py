import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, make_response
from flask_login import login_required, current_user
from .models import Question, User, School, ROLE_HQ, ROLE_MANAGER, ROLE_STUDENT
from .services import QuestionService, AccessControlService
from .utils import require_roles
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
    view_school_id = AccessControlService.resolve_view_school_id(current_user, requested_school_id)

    # クエリ取得
    q = QuestionService.get_visible_questions(current_user, view_school_id)

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
        file = request.files.get("image")
        grade = request.form.get("grade")
        
        # 画像必須
        if not file or file.filename == '':
            flash("画像をアップロードしてください", "warning")
        else:
            # 画像保存 (S3)
            from .utils_s3 import upload_file_to_s3
            try:
                save_path = upload_file_to_s3(file, file.filename, content_type=file.content_type)
            except Exception as e:
                flash(f"画像のアップロードに失敗しました: {e}", "danger")
                return redirect(url_for("main.new_question"))

            q = Question(
                content="[画像による質問]", # 内容は自動入力
                user_id=current_user.id, 
                school_id=current_user.school_id,
                image_path=save_path,
                grade=grade,
                explanation_status="processing"
            )
            db.session.add(q)
            db.session.commit()
            
            # 自動解説タスク起動
            from .tasks import analyze_image_task
            print(f"DEBUG: [Web] Dispatching task for question_id={q.id}")
            task = analyze_image_task.delay(q.id)
            print(f"DEBUG: [Web] Task dispatched. Task ID: {task.id}")

            flash("質問を送信しました。解説が作成されるまでお待ちください。", "success")
            return redirect(url_for("main.new_question"))

    # 履歴取得
    history = Question.query.filter_by(user_id=current_user.id).order_by(Question.created_at.desc()).limit(10).all()
    
    return render_template("questions/new.html", history=history)

@main_bp.route("/export/questions.csv")
@login_required
def export_questions_csv():
    requested_school_id = request.args.get("school_id")
    view_school_id = AccessControlService.resolve_view_school_id(current_user, requested_school_id)

    # クエリ取得
    q = QuestionService.get_visible_questions(current_user, view_school_id)

    # CSV生成
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "content", "user_email", "school_name", "created_at"])
    
    # N+1対策: joinedloadで関連データを一括取得
    from sqlalchemy.orm import joinedload
    questions = q.options(joinedload(Question.user), joinedload(Question.school)).all()

    for row in questions:
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

@main_bp.route("/questions/<int:id>/explain", methods=["POST"])
@login_required
def explain_question(id):
    q = Question.query.get_or_404(id)
    
    # 権限チェック (自分の質問か、マネージャー以上)
    if current_user.role == ROLE_STUDENT and q.user_id != current_user.id:
        abort(403)
    if current_user.role == ROLE_MANAGER and q.school_id != current_user.school_id:
        abort(403)
        
    if not q.image_path:
        flash("画像がないため解説できません", "warning")
        return redirect(url_for("main.list_questions"))

    # Celeryタスク起動
    from .tasks import analyze_image_task
    analyze_image_task.delay(q.id)
    
    q.explanation_status = "processing"
    db.session.commit()
    
    flash("AI解説の生成を開始しました。しばらくお待ちください。", "info")
    return redirect(url_for("main.list_questions"))

