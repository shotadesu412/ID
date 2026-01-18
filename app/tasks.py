import os
import json
import base64
from datetime import datetime
from celery import Celery
from openai import OpenAI
from . import db, create_app
from .models import Question

# Celeryインスタンスは __init__.py で作成されるが、
# ここではタスク定義のために必要。循環参照を避けるため、
# make_celery パターンを使うか、あるいはここで定義するか。
# 今回はシンプルに、app/__init__.py で作成された celery をインポートする形をとるが、
# 循環参照になるため、タスク定義はここで行い、__init__.py からインポートさせる。

# しかし、Celeryのベストプラクティスとして、タスクは独立させるのが良い。
# ここでは shared_task を使う。
from datetime import datetime
from openai import OpenAI
from . import db, create_app, celery
from .models import Question

# Explicitly use the configured celery instance
# @shared_task was falling back to unconfigured default (AMQP)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@celery.task(bind=True, max_retries=3, name='app.tasks.analyze_image_task')
def analyze_image_task(self, question_id):
    """
    画像解析タスク
    """
    # アプリケーションコンテキストが必要（DBアクセス用）
    # Flask-Celery-Helper等を使っていない場合は手動でpushが必要な場合があるが、
    # Flask 2.x/3.x + Celery 5.x の標準的な統合では自動で扱えることが多い。
    # 念のため明示的に書くなら:
    # with app.app_context(): ...
    
    # ここでは循環参照を避けるため、タスク内で app を import するか、
    # あるいは create_app() を呼ぶかだが、
    # 実行時には current_app が使えるはず... いや、Workerプロセスは別なので
    # アプリコンテキストを作る必要がある。
    
    from app import create_app
    app = create_app()
    
    with app.app_context():
        try:
            question = Question.query.get(question_id)
            if not question or not question.image_path:
                return {"status": "failed", "error": "Question or Image not found"}

            question.explanation_status = "processing"
            db.session.commit()

            # 画像読み込み (ローカルファイルシステム前提)
            # 本番(Render)では永続ディスクがないと消えるが、
            # 今回はプロトタイプとしてローカル保存/一時保存を想定。
            # ※本来はS3等に上げるべき。
            try:
                with open(question.image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            except FileNotFoundError:
                 question.explanation_status = "failed"
                 question.explanation = "Image file not found."
                 db.session.commit()
                 return

            # プロンプト作成 (saas/app.py のロジックを流用)
            # 学年判定ロジックがないため、一旦デフォルト(中学生)とする
            prompt = """
            あなたは優秀な教師です。この画像に写っている問題を分析して、学習者に適した教育的な指導をしてください。

            【絶対に守ること】
            - 計算しなくていいから、解き方の手順だけ教えてください
            - 専門用語は避け、平易な言葉で説明してください
            - できるだけで細かく、わかりやすく説明してください

            【表示形式】
            - 考え方と手順のみ表示
            - 重要な数式は $$...$$ で中央揃え表示
            - 式に番号を振ってください
            """

            gpt_response = client.chat.completions.create(
                model="gpt-5.2", # コストパフォーマンス重視
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "auto"
                        }}
                    ]}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            explanation_text = gpt_response.choices[0].message.content.strip()

            question.explanation = explanation_text
            question.explanation_status = "completed"
            db.session.commit()
            
            return {"status": "completed", "question_id": question_id}

        except Exception as e:
            db.session.rollback()
            # エラー記録
            if question:
                question.explanation_status = "failed"
                question.explanation = str(e)
                db.session.commit()
            raise self.retry(exc=e, countdown=60)
