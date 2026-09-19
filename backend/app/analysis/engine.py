"""
نقطة الدخول الموحدة لمحرك التحليل:
يستقبل بيانات الرسالة، يشغّل الـ Parsing ثم القواعد ثم الحساب، ويعيد نتيجة موحدة.
"""
from app.schemas import EmailInput, AnalysisResult, IndicatorResult
from app.analysis.parser import parse_links, parse_attachments
from app.analysis.rules import run_all_rules
from app.analysis.scoring import calculate_risk_score, score_to_level, build_recommendations


def analyze_email(data: EmailInput) -> AnalysisResult:
    """يشغّل خط أنابيب التحليل الكامل: Parsing -> Detection -> Scoring -> Explanation."""

    parsed_links = parse_links(data.links)
    parsed_attachments = parse_attachments(data.attachments)

    indicators = run_all_rules(
        sender=data.sender,
        display_name=data.display_name or "",
        subject=data.subject,
        body=data.body,
        parsed_links=parsed_links,
        parsed_attachments=parsed_attachments,
    )

    score = calculate_risk_score(indicators)
    level = score_to_level(score)
    recommendations = build_recommendations(indicators)

    return AnalysisResult(
        risk_score=score,
        risk_level=level,
        indicators=[IndicatorResult(**ind) for ind in indicators],
        recommendations=recommendations,
    )
