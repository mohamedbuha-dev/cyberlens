"""
مخططات Pydantic - تحديد شكل البيانات الداخلة والخارجة من الـ API.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EmailInput(BaseModel):
    """البيانات التي يدخلها المستخدم لتحليل رسالة بريد إلكتروني."""
    sender: str = Field(..., description="عنوان البريد الإلكتروني للمرسل")
    display_name: Optional[str] = Field(None, description="الاسم الظاهر للمرسل (إن وجد)")
    subject: str = Field("", description="عنوان الرسالة")
    body: str = Field("", description="نص الرسالة")
    links: List[str] = Field(default_factory=list, description="الروابط الموجودة في الرسالة")
    attachments: List[str] = Field(default_factory=list, description="أسماء ملفات المرفقات")


class IndicatorResult(BaseModel):
    """نتيجة فحص مؤشر واحد."""
    id: str
    title: str
    triggered: bool
    weight: float
    explanation: str


class AnalysisResult(BaseModel):
    """نتيجة التحليل الكاملة المُعادة للمستخدم."""
    risk_score: float
    risk_level: str
    indicators: List[IndicatorResult]
    recommendations: List[str]


class AnalysisRecordOut(BaseModel):
    """شكل السجل عند إعادته من قاعدة البيانات (للتاريخ)."""
    id: int
    sender: Optional[str]
    subject: Optional[str]
    risk_score: float
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisRecordDetail(AnalysisRecordOut):
    """تفاصيل كاملة لسجل واحد بما فيها التفسير والتوصيات."""
    body: Optional[str]
    links: Optional[str]
    attachments: Optional[str]
    triggered_indicators: str
    recommendations: str
