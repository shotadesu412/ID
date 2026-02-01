import os
import json
import base64
from datetime import datetime
from celery import Celery
from openai import OpenAI
import boto3
from urllib.parse import urlparse
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
            print(f"DEBUG: Starting task for question_id={question_id}")
            question = Question.query.get(question_id)
            if not question:
                print("ERROR: Question not found")
                return {"status": "failed", "error": "Question not found"}
            
            if not question.image_path:
                print("ERROR: Image path not found")
                return {"status": "failed", "error": "Image path not found"}

            question.explanation_status = "processing"
            db.session.commit()

            # 画像URL (S3)
            original_url = question.image_path
            print(f"DEBUG: Original URL: {original_url}")

            # Presigned URLの発行 (非公開バケット対応)
            try:
                # URLからキーを抽出 (https://bucket.s3.region.amazonaws.com/KEY)
                parsed = urlparse(original_url)
                s3_key = parsed.path.lstrip('/')
                
                print(f"DEBUG: Extracting key: {s3_key} from bucket: {app.config.get('AWS_S3_BUCKET_NAME')}")

                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=app.config.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=app.config.get("AWS_SECRET_ACCESS_KEY"),
                    region_name=app.config.get("AWS_REGION")
                )

                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': app.config.get("AWS_S3_BUCKET_NAME"),
                        'Key': s3_key
                    },
                    ExpiresIn=300 # 5分間有効
                )
                image_url = presigned_url
                print(f"DEBUG: Generated presigned URL successfully (len={len(image_url)})")

            except Exception as e:
                print(f"WARNING: Failed to generate presigned URL: {e}")
                import traceback
                traceback.print_exc()
                # 失敗時は元のURLを使用
                image_url = original_url

            # プロンプト作成
            # ... (omitted for brevity, keeping original prompt logic)
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

            print("DEBUG: Calling OpenAI API...")
            gpt_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": image_url,
                            "detail": "auto"
                        }}
                    ]}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            print("DEBUG: OpenAI API returned response.")

            explanation_text = gpt_response.choices[0].message.content.strip()

            question.explanation = explanation_text
            question.explanation_status = "completed"
            db.session.commit()
            print("DEBUG: Task completed successfully.")
            
            return {"status": "completed", "question_id": question_id}

        except Exception as e:
            print(f"ERROR: Task failed with exception: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            # エラー記録
            if question:
                question.explanation_status = "failed"
                question.explanation = str(e)
                try:
                    db.session.commit()
                except:
                    pass
            raise self.retry(exc=e, countdown=60)
