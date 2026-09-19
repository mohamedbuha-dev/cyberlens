"""
تحويل رسالة بريد خام (RFC822 / .eml) إلى EmailInput جاهز للتحليل.

يعتمد كليًا على مكتبات بايثون القياسية (email / html.parser) — بدون أي حزم إضافية.
لا يتم فتح أو تشغيل أي رابط أو مرفق؛ التفكيك نصي/بنيوي آمن بالكامل.
"""
import re
from email import message_from_bytes, message_from_string
from email.header import decode_header, make_header
from email.utils import parseaddr
from email.message import Message
from html.parser import HTMLParser
from typing import List, Optional

from app.schemas import EmailInput

# نمط عام لالتقاط الروابط الظاهرة كنص داخل الرسالة
URL_IN_TEXT = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)


def _decode(value: Optional[str]) -> str:
    """يفك ترميز ترويسة قد تكون مُرمّزة (MIME encoded-word) إلى نص واضح."""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value))).strip()
    except Exception:
        return value.strip()


class _LinkExtractor(HTMLParser):
    """يستخرج قيم href من وسوم <a> داخل جسم HTML دون تنفيذ أي شيء."""

    def __init__(self):
        super().__init__()
        self.links: List[str] = []
        self.text_parts: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for name, val in attrs:
                if name.lower() == "href" and val:
                    self.links.append(val.strip())

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped)


def _html_to_text_and_links(html: str) -> tuple[str, List[str]]:
    """يحوّل جسم HTML إلى نص مبسّط + قائمة روابط href."""
    extractor = _LinkExtractor()
    try:
        extractor.feed(html)
    except Exception:
        # في أسوأ الحالات نعيد النص الخام دون وسوم بشكل تقريبي
        return re.sub(r"<[^>]+>", " ", html), []
    return " ".join(extractor.text_parts), extractor.links


def _get_payload_text(part: Message) -> str:
    """يفك ترميز محتوى جزء نصي إلى str مع احترام charset المعلن."""
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, TypeError):
        return payload.decode("utf-8", errors="replace")


def parse_raw_email(raw: bytes | str) -> EmailInput:
    """
    يفكّك رسالة بريد خام إلى الحقول التي يفهمها محرّك التحليل.

    - يستخرج المرسل الفعلي والاسم الظاهر من ترويسة From.
    - يفضّل جسم text/plain، ويرجع لـ text/html عند غيابه.
    - يجمع الروابط من نص الرسالة ومن روابط <a> في HTML.
    - يجمع أسماء المرفقات من الأجزاء التي تحمل filename.
    """
    msg = message_from_bytes(raw) if isinstance(raw, bytes) else message_from_string(raw)

    display_name, sender = parseaddr(msg.get("From", ""))
    display_name = _decode(display_name)
    subject = _decode(msg.get("Subject", ""))

    plain_parts: List[str] = []
    html_parts: List[str] = []
    links: List[str] = []
    attachments: List[str] = []

    for part in msg.walk():
        if part.is_multipart():
            continue

        content_type = part.get_content_type()
        disposition = (part.get("Content-Disposition") or "").lower()
        filename = part.get_filename()

        # مرفق: أي جزء له اسم ملف أو disposition=attachment
        if filename or "attachment" in disposition:
            if filename:
                attachments.append(_decode(filename))
            continue

        if content_type == "text/plain":
            plain_parts.append(_get_payload_text(part))
        elif content_type == "text/html":
            html_parts.append(_get_payload_text(part))

    # اختيار الجسم: نص عادي أولًا، وإلا نستخرجه من الـ HTML
    if plain_parts:
        body = "\n".join(plain_parts).strip()
    else:
        text_from_html, html_links = "", []
        for html in html_parts:
            t, l = _html_to_text_and_links(html)
            text_from_html += " " + t
            html_links.extend(l)
        body = text_from_html.strip()
        links.extend(html_links)

    # روابط <a> من كل أجزاء HTML (حتى لو كان هناك جسم نصي)
    for html in html_parts:
        _, html_links = _html_to_text_and_links(html)
        links.extend(html_links)

    # روابط ظاهرة كنص داخل الجسم
    links.extend(URL_IN_TEXT.findall(body))

    # إزالة التكرار مع الحفاظ على الترتيب، واستبعاد روابط mailto/tel
    seen = set()
    clean_links: List[str] = []
    for link in links:
        if link.lower().startswith(("mailto:", "tel:")):
            continue
        if link not in seen:
            seen.add(link)
            clean_links.append(link)

    return EmailInput(
        sender=sender or "unknown@unknown",
        display_name=display_name or None,
        subject=subject,
        body=body,
        links=clean_links,
        attachments=attachments,
    )
