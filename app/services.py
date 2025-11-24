from .models import Question, School, ROLE_STUDENT, ROLE_MANAGER, ROLE_HQ
from flask import current_app, abort

class QuestionService:
    @staticmethod
    def get_visible_questions(user, view_school_id=None):
        """
        ユーザーの権限に基づいて閲覧可能な質問のクエリを返す
        """
        q = Question.query
        
        if user.role == ROLE_STUDENT:
            # 学生は自分の質問のみ
            q = q.filter(Question.user_id == user.id)
        elif user.role == ROLE_MANAGER:
            # マネージャーは自校舎（または指定校舎）のみ
            # view_school_id は resolve_view_school_id で検証済みであることを前提とするが、
            # ここでも念のためチェックしてもよい。
            # いったん view_school_id を信じる。
            target_school_id = view_school_id if view_school_id else user.school_id
            q = q.filter(Question.school_id == target_school_id)
        elif user.role == ROLE_HQ:
            # 本部は全校舎、または指定校舎
            if view_school_id:
                q = q.filter(Question.school_id == view_school_id)
        else:
            # 未定義のロール
            abort(403)
            
        return q.order_by(Question.created_at.desc())

class AccessControlService:
    @staticmethod
    def resolve_view_school_id(user, param_value):
        """
        ユーザー権限とリクエストパラメータに基づいて、表示対象の school_id を決定する
        """
        allow_manager_cross = current_app.config.get("ALLOW_MANAGER_CROSS_SCHOOL", False)
        sid = None
        try:
            sid = int(param_value) if param_value else None
        except Exception:
            sid = None

        if user.role == ROLE_HQ:
            return sid  # 任意切替可
        if user.role == ROLE_MANAGER:
            if allow_manager_cross and sid:
                return sid
            # 既定は自校舎のみ
            return user.school_id
        if user.role == ROLE_STUDENT:
            return user.school_id
        return None

    @staticmethod
    def can_view_question(user, question):
        if user.role == ROLE_HQ:
            return True
        if user.role == ROLE_MANAGER:
            return question.school_id == user.school_id
        if user.role == ROLE_STUDENT:
            return question.user_id == user.id
        return False
