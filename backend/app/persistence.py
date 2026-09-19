"""
حفظ نتيجة تحليل رسالة في قاعدة البيانات.

مُستخرَج في وحدة مستقلة كي يستخدمه كلٌّ من واجهة الـ API وبوابة البريد (IMAP)
دون تكرار المنطق أو ربط البوابة بطبقة الـ routers.
"""
import json
from sqlalchemy.orm import Session

from app.schemas import EmailInput, AnalysisResult
from app.models import AnalysisRecord


def save_analysis(db: Session, email: EmailInput, result: AnalysisResult) -> AnalysisRecord:
    """يحفظ الرسالة المدخلة ونتيجة تحليلها كسجل واحد ويعيده."""
    record = AnalysisRecord(
        sender=email.sender,
        subject=email.subject,
        body=email.body,
        links=json.dumps(email.links, ensure_ascii=False),
        attachments=json.dumps(email.attachments, ensure_ascii=False),
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        triggered_indicators=json.dumps(
            [ind.model_dump() for ind in result.indicators], ensure_ascii=False
        ),
        recommendations=json.dumps(result.recommendations, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
