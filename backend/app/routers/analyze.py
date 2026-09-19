"""
نقاط API الخاصة بتحليل رسائل البريد الإلكتروني.
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import EmailInput, AnalysisResult
from app.analysis.engine import analyze_email
from app.analysis.email_parser import parse_raw_email
from app.persistence import save_analysis

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResult)
def analyze(email: EmailInput, db: Session = Depends(get_db)):
    """
    يستقبل بيانات رسالة بريد إلكتروني (حقول منظمة)، يحللها عبر محرك التحليل،
    يحفظ النتيجة في قاعدة البيانات، ويعيدها للمستخدم.
    """
    result = analyze_email(email)
    save_analysis(db, email, result)
    return result


@router.post("/analyze/raw", response_model=AnalysisResult)
def analyze_raw(
    raw_email: str = Body(..., media_type="text/plain",
                          description="محتوى رسالة البريد الخام (RFC822 / .eml)"),
    db: Session = Depends(get_db),
):
    """
    يستقبل رسالة بريد خام كاملة (ترويسات + جسم)، يفكّكها تلقائيًا إلى حقول،
    ثم يحللها ويحفظها ويعيد النتيجة.

    هذه النقطة تخدم أي مصدر لا يملك حقولًا جاهزة: رفع ملف .eml،
    أو بوابة البريد (IMAP)، أو تحويل رسالة مشبوهة — كلها بنفس المنطق.
    """
    email = parse_raw_email(raw_email)
    result = analyze_email(email)
    save_analysis(db, email, result)
    return result
