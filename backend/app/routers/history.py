"""
نقاط API الخاصة بعرض سجل التحليلات السابقة (لأغراض المتابعة والتقرير النهائي).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisRecord
from app.schemas import AnalysisRecordOut, AnalysisRecordDetail

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=List[AnalysisRecordOut])
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """يعيد آخر التحليلات المحفوظة، الأحدث أولًا."""
    records = (
        db.query(AnalysisRecord)
        .order_by(AnalysisRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return records


@router.get("/history/{record_id}", response_model=AnalysisRecordDetail)
def get_history_detail(record_id: int, db: Session = Depends(get_db)):
    """يعيد تفاصيل تحليل واحد بالكامل."""
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="السجل غير موجود")
    return record


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """إحصائيات سريعة لعرضها في الـ Dashboard: عدد التحليلات حسب المستوى."""
    records = db.query(AnalysisRecord).all()
    stats = {"منخفضة": 0, "متوسطة": 0, "مرتفعة": 0, "حرجة": 0}
    for r in records:
        if r.risk_level in stats:
            stats[r.risk_level] += 1
    return {"total": len(records), "by_level": stats}
