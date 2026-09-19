"""
نماذج قاعدة البيانات - جدول تخزين نتائج التحليل وسجل الاختبارات.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class AnalysisRecord(Base):
    """
    يمثل سجل تحليل واحد لرسالة بريد إلكتروني:
    البيانات المدخلة + النتيجة + التفسير + التوصيات.
    """
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True)

    # الحقول المدخلة من الرسالة
    sender = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)
    links = Column(Text, nullable=True)          # JSON string لقائمة الروابط
    attachments = Column(Text, nullable=True)    # JSON string لقائمة أسماء المرفقات

    # نتيجة التحليل
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=False)   # منخفضة / متوسطة / مرتفعة / حرجة
    triggered_indicators = Column(Text, nullable=False)  # JSON string
    recommendations = Column(Text, nullable=False)       # JSON string

    created_at = Column(DateTime(timezone=True), server_default=func.now())
