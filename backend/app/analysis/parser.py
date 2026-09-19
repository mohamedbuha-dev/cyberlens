"""
استخراج الحقول والمعلومات القابلة للتحليل من بيانات الرسالة المدخلة.
لا يتم تشغيل أي رابط أو مرفق - فقط تحليل نصي/بنيوي آمن.
"""
import re
from urllib.parse import urlparse
from typing import List, Dict

# امتدادات مرفقات عالية الخطورة شائعة في هجمات التصيد
DANGEROUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".cmd", ".vbs", ".js", ".jar",
    ".msi", ".ps1", ".pif", ".hta", ".wsf",
}

# خدمات اختصار روابط شائعة (لا تعني بالضرورة خطورة لكنها مؤشر يستحق الفحص)
URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
    "is.gd", "buff.ly", "shorte.st", "cutt.ly",
}

IP_PATTERN = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def extract_domain(email_or_url: str) -> str:
    """يستخرج النطاق من بريد إلكتروني أو رابط."""
    if "@" in email_or_url:
        return email_or_url.split("@")[-1].strip().lower()
    parsed = urlparse(email_or_url if "://" in email_or_url else f"//{email_or_url}")
    return (parsed.hostname or "").lower()


def parse_links(links: List[str]) -> List[Dict]:
    """يحلل كل رابط ويستخرج معلومات بنيوية عنه دون فتحه."""
    parsed_links = []
    for link in links:
        domain = extract_domain(link)
        parsed_links.append({
            "raw": link,
            "domain": domain,
            "is_ip_based": bool(IP_PATTERN.match(domain)),
            "is_shortener": domain in URL_SHORTENERS,
            "has_https": link.lower().startswith("https://"),
        })
    return parsed_links


def parse_attachments(attachments: List[str]) -> List[Dict]:
    """يفحص أسماء المرفقات ويستخرج الامتداد والامتداد المزدوج."""
    parsed = []
    for name in attachments:
        lower = name.lower().strip()
        ext = ""
        if "." in lower:
            ext = "." + lower.rsplit(".", 1)[-1]

        # امتداد مزدوج مثل invoice.pdf.exe
        parts = lower.split(".")
        double_extension = len(parts) >= 3 and f".{parts[-1]}" in DANGEROUS_EXTENSIONS

        parsed.append({
            "raw": name,
            "extension": ext,
            "is_dangerous_extension": ext in DANGEROUS_EXTENSIONS,
            "has_double_extension": double_extension,
        })
    return parsed
