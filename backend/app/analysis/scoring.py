"""
حساب درجة الخطورة (Risk Score) من نتائج القواعد المُفعّلة،
وتحويلها إلى مستوى مفهوم للمستخدم: منخفضة / متوسطة / مرتفعة / حرجة.

نموذج الأوزان موثق وقابل للتعديل بسهولة أثناء التنفيذ (كما هو مخطط في وثيقة المشروع).
"""
from typing import List, Dict, Tuple

MAX_POSSIBLE_SCORE = 115  # مجموع أوزان كل القواعد الحالية (25+15+25+20+30)

# حدود تصنيف المستوى كنسبة مئوية من الدرجة القصوى
THRESHOLDS = [
    (0, 20, "منخفضة"),
    (20, 45, "متوسطة"),
    (45, 70, "مرتفعة"),
    (70, 101, "حرجة"),
]


def calculate_risk_score(indicators: List[Dict]) -> float:
    """يجمع أوزان كل المؤشرات المُفعّلة ويحولها لنسبة مئوية من 0 إلى 100."""
    total = sum(ind["weight"] for ind in indicators if ind["triggered"])
    percentage = min(100.0, round((total / MAX_POSSIBLE_SCORE) * 100, 1))
    return percentage


def score_to_level(score: float) -> str:
    """يحوّل الدرجة الرقمية إلى تصنيف نصي."""
    for low, high, label in THRESHOLDS:
        if low <= score < high:
            return label
    return "حرجة"


def build_recommendations(indicators: List[Dict]) -> List[str]:
    """يولّد توصيات توعوية مرتبطة بالمؤشرات المُفعّلة فعليًا."""
    recs = []
    triggered_ids = {ind["id"] for ind in indicators if ind["triggered"]}

    if "display_name_mismatch" in triggered_ids:
        recs.append("تحقق دائمًا من نطاق البريد الفعلي للمرسل وليس فقط الاسم الظاهر.")
    if "urgency_language" in triggered_ids:
        recs.append("كن حذرًا من أي رسالة تضغط عليك لاتخاذ قرار فوري — توقف وتحقق أولاً.")
    if "credential_request" in triggered_ids:
        recs.append("لا تُدخل كلمات المرور أو رموز التحقق عبر روابط واردة في البريد.")
    if "suspicious_links" in triggered_ids:
        recs.append("مرر مؤشر الفأرة فوق الرابط قبل الضغط، وتجنب الروابط المختصرة أو المبنية على IP.")
    if "dangerous_attachments" in triggered_ids:
        recs.append("لا تفتح مرفقات بامتدادات تنفيذية أو ذات امتداد مزدوج غير متوقع.")

    if not recs:
        recs.append("لم يتم رصد مؤشرات خطر واضحة، لكن يُنصح دائمًا بالتحقق من مصدر أي رسالة غير متوقعة.")

    return recs
