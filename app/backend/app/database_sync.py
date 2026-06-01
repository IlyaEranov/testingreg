"""Синхронное подключение к БД для Celery-воркера.

Celery-задачи выполняются в обычном (не async) контексте, поэтому
используют синхронный движок SQLAlchemy и отдельную фабрику сессий.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

sync_engine = create_engine(settings.DATABASE_URL_SYNC, echo=False, future=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)
