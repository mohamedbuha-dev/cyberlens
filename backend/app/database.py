"""
إعداد الاتصال بقاعدة البيانات SQLite باستخدام SQLAlchemy.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# مسار قاعدة البيانات - داخل مجلد data ليصمد أمام إعادة تشغيل الحاوية (volume)
DATA_DIR = os.getenv("CYBERLENS_DATA_DIR", "/app/data")
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATA_DIR}/cyberlens.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # مطلوب لـ SQLite مع FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency لحقن جلسة قاعدة البيانات في كل طلب API."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
