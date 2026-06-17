import os
import redis
from sqlalchemy import create_engine, update, select
from sqlalchemy.orm import Session
from celery import Celery
from models import Article
#celery task are sync
DB_URL = os.getenv("DB_URL", "postgresql+psycopg://postgres:password@localhost:5432/fastapi_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhos:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_URL = os.getenv("CELERY_RESULT_URL", "redis://localhost:6379/2")

celery_app = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_URL)

sync_engine = create_engine(DB_URL, pool_pre_ping=True)
sync_redis = redis.from_url(REDIS_URL, decode_responses = True)

@celery_app.task
def compute_reading_time(article_id:int, body:str)->dict:
    words = body.split("")
    # 200 words per minute
    reading_seconds = max(1, round(words/200 * 60))

    with Session(sync_engine) as session:
        session.execute(
            update(Article).where(Article.id == article_id).values(reading_time=reading_seconds)
        )

        session.commit()
    
    sync_redis.delete(f"article:{article_id}")
    return {"article_id":article_id, "reading_time_seconds":reading_seconds}