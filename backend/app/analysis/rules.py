"""
قواعد تحليل المؤشرات (Detection Rules).
كل قاعدة مستقلة، تُعيد True/False مع تفسير، ولها وزن يُستخدم في حساب Risk Score.
هذا التصميم يسمح بإضافة أو تعديل القواعس والأوزان دون المساس بمحرك الحساب.
"""
from typing import List, Dict
from app.analysis.parser import extract_domain

# كلمات ذات طابع استعجالي/تهديدي شائعة في رسائل التصيد (عربي/إنجليزي)
URGENCY_KEYWORDS = [
    "urgent", "immediately", "verify your account", "suspended",
    "click here", "act now", "limited time", "confirm your password",
    "عاجل", "فوري", "تم تعليق", "يرجى التأكيد", "انقر هنا",
    "تحديث بياناتك", "خلال 24 ساعة", "حسابك سيتم إيقافه",
]

# كلمات تطلب معلومات حساسة
CREDENTIAL_REQUEST_KEYWORDS = [
    "password", "otp", "verification code", "credit card", "cvv",
    "كلمة المرور", "رمز التحقق", "رقم البطاقة",
]


def rule_display_name_mismatch(sender: str, display_name: str) -> Dict:
    """يكشف تعارض بين الاسم الظاهر ونطاق البريد الفعلي (انتحال هوية شائع)."""
    triggered = False
    if display_name:
        sender_domain = extract_domain(sender)
        # إذا كان الاسم الظاهر يحتوي على اسم شركة معروفة لكن النطاق مختلف تمامًا
        known_brands = ["paypal", "microsoft", "apple", "google", "bank", "amazon"]
        for brand in known_brands:
            if brand in display_name.lower() and brand not in sender_domain:
                triggered = True
                break
    return {
        "id": "display_name_mismatch",
        "title": "تعارض بين الاسم الظاهر ونطاق المرسل",
        "triggered": triggered,
        "weight": 25,
        "explanation": (
            "الاسم الظاهر يوحي بجهة معروفة، لكن نطاق البريد الفعلي لا يطابقها — "
            "هذا أسلوب شائع لانتحال الهوية."
            if triggered else
            "لا يوجد تعارض واضح بين الاسم الظاهر ونطاق المرسل."
        ),
    }


def rule_urgency_language(subject: str, body: str) -> Dict:
    """يكشف استخدام لغة استعجالية أو تهديدية للضغط على المستخدم لاتخاذ قرار سريع."""
    text = f"{subject} {body}".lower()
    matched = [kw for kw in URGENCY_KEYWORDS if kw.lower() in text]
    triggered = len(matched) > 0
    return {
        "id": "urgency_language",
        "title": "لغة استعجالية أو تهديدية",
        "triggered": triggered,
        "weight": 15,
        "explanation": (
            f"تم العثور على عبارات استعجالية مثل: {', '.join(matched[:3])} — "
            "الرسائل الشرعية نادرًا ما تضغط على المستخدم لاتخاذ قرار فوري."
            if triggered else
            "لا توجد لغة استعجالية ملحوظة في الرسالة."
        ),
    }


def rule_credential_request(subject: str, body: str) -> Dict:
    """يكشف طلب معلومات حساسة (كلمات مرور، رموز تحقق، بيانات بطاقات)."""
    text = f"{subject} {body}".lower()
    matched = [kw for kw in CREDENTIAL_REQUEST_KEYWORDS if kw.lower() in text]
    triggered = len(matched) > 0
    return {
        "id": "credential_request",
        "title": "طلب معلومات حساسة",
        "triggered": triggered,
        "weight": 25,
        "explanation": (
            "الرسالة تطلب معلومات حساسة مباشرة — الجهات الموثوقة لا تطلب "
            "كلمات المرور أو رموز التحقق عبر البريد."
            if triggered else
            "لم يتم العثور على طلب مباشر لمعلومات حساسة."
        ),
    }


def rule_suspicious_links(parsed_links: List[Dict]) -> Dict:
    """يكشف روابط مشبوهة: مبنية على IP، مختصرة، أو بدون HTTPS."""
    suspicious = [
        l for l in parsed_links
        if l["is_ip_based"] or l["is_shortener"] or not l["has_https"]
    ]
    triggered = len(suspicious) > 0
    reasons = []
    if any(l["is_ip_based"] for l in suspicious):
        reasons.append("روابط مبنية على عنوان IP مباشرة")
    if any(l["is_shortener"] for l in suspicious):
        reasons.append("روابط عبر خدمة اختصار تُخفي الوجهة الحقيقية")
    if any(not l["has_https"] for l in suspicious):
        reasons.append("روابط بدون تشفير HTTPS")
    return {
        "id": "suspicious_links",
        "title": "روابط مشبوهة",
        "triggered": triggered,
        "weight": 20,
        "explanation": (
            "تم رصد: " + "، ".join(reasons) + "."
            if triggered else
            "الروابط الموجودة لا تحمل مؤشرات هيكلية مشبوهة."
        ),
    }


def rule_dangerous_attachments(parsed_attachments: List[Dict]) -> Dict:
    """يكشف مرفقات ذات امتدادات خطيرة أو امتدادات مزدوجة."""
    dangerous = [a for a in parsed_attachments if a["is_dangerous_extension"] or a["has_double_extension"]]
    triggered = len(dangerous) > 0
    return {
        "id": "dangerous_attachments",
        "title": "مرفقات ذات امتداد خطير",
        "triggered": triggered,
        "weight": 30,
        "explanation": (
            "يوجد مرفق بامتداد قابل للتنفيذ أو بامتداد مزدوج (مثل invoice.pdf.exe) — "
            "هذا من أخطر مؤشرات التصيد."
            if triggered else
            "لا توجد مرفقات بامتدادات خطيرة أو مزدوجة."
        ),
    }


def run_all_rules(sender: str, display_name: str, subject: str, body: str,
                   parsed_links: List[Dict], parsed_attachments: List[Dict]) -> List[Dict]:
    """ينفذ جميع القواعد ويعيد قائمة موحدة بالنتائج."""
    return [
        rule_display_name_mismatch(sender, display_name),
        rule_urgency_language(subject, body),
        rule_credential_request(subject, body),
        rule_suspicious_links(parsed_links),
        rule_dangerous_attachments(parsed_attachments),
    ]
