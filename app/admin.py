from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from .models import School, User, ROLE_HQ, db
from .audit import log_action

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
@login_required
def require_hq():
    if not current_user.is_hq:
        abort(403)

@admin_bp.route("/schools", methods=["GET", "POST"])
def manage_schools():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("学校名を入力してください", "warning")
        elif School.query.filter_by(name=name).first():
            flash("その学校名は既に登録されています", "warning")
        else:
            s = School(name=name)
            db.session.add(s)
            db.session.commit()
            log_action(current_user, "add_school", target_type="school", target_id=s.id)
            flash(f"学校「{name}」を追加しました", "success")
            return redirect(url_for("admin.manage_schools"))

    schools = School.query.order_by(School.id).all()
    return render_template("admin/schools.html", schools=schools)

@admin_bp.route("/users", methods=["GET", "POST"])
def manage_users():
    if request.method == "POST":
        # DELETE action
        user_id = request.form.get("user_id")
        if user_id:
            u = User.query.get(user_id)
            if u:
                if u.id == current_user.id:
                    flash("自分自身は削除できません", "danger")
                else:
                    # 物理削除ではなく論理削除が好ましい場合もあるが、要件は「退会（削除）」なので今回は物理削除する
                    # 関連データ(Questions)があるので注意が必要だが、Cascade設定がない場合はエラーになる可能性。
                    # models.pyを確認すると、backrefはあるがcascadeは明示されていない。
                    # 手動で関連データを消すか、あるいはUserを削除しようとするとDBエラーになるかも。
                    # 安全のため、まずはUser削除を試みる。
                    email = u.email
                    try:
                        db.session.delete(u)
                        db.session.commit()
                        log_action(current_user, "delete_user", target_type="user", target_id=int(user_id))
                        flash(f"ユーザー {email} を削除しました", "success")
                    except Exception as e:
                        db.session.rollback()
                        flash(f"削除に失敗しました (関連データがある可能性があります): {e}", "danger")
            else:
                flash("ユーザーが見つかりません", "warning")
        return redirect(url_for("admin.manage_users"))

    # List users
    users = User.query.order_by(User.id.desc()).limit(100).all() # とりあえず直近100件
    return render_template("admin/users.html", users=users)
