"""
بوابة البريد (Mail Gateway) عبر IMAP.

تتصل بصندوق بريد (Gmail تجريبي مثلًا)، تسحب الرسائل غير المقروءة، تحللها عبر نفس
محرّك CyberLens، وتخزّن النتيجة — بشكل دوري وتلقائي بالكامل. المستخدم لا يُدخل شيئًا.

تعمل كخيط (thread) في الخلفية داخل حاوية الـ backend، فتقلع مع
`docker compose up` دون أي خدمة أو أمر إضافي. إن لم تُضبط بيانات الدخول،
تتوقف بهدوء وتبقى بقية المنصة (الفورم اليدوي) تعمل طبيعيًا.
"""
import imaplib
import logging
import os
import threading
import time

from app.database import SessionLocal
from app.analysis.engine import analyze_email
from app.analysis.email_parser import parse_raw_email
from app.persistence import save_analysis

logger = logging.getLogger("cyberlens.mailbox")

# لا نتوقف عند رسالة واحدة تالفة؛ نسجّل ونكمل البقية.


class MailboxConfig:
    """يقرأ إعدادات الاتصال من متغيّرات البيئة."""

    def __init__(self):
        self.host = os.getenv("IMAP_HOST", "").strip()
        self.port = int(os.getenv("IMAP_PORT", "993"))
        self.user = os.getenv("IMAP_USER", "").strip()
        self.password = os.getenv("IMAP_PASSWORD", "").strip()
        self.mailbox = os.getenv("IMAP_MAILBOX", "INBOX").strip()
        self.poll_interval = int(os.getenv("IMAP_POLL_INTERVAL", "20"))
        # هل نضع علامة "مقروء" على الرسالة بعد تحليلها كي لا تتكرر؟
        self.mark_seen = os.getenv("IMAP_MARK_SEEN", "true").lower() == "true"

    @property
    def enabled(self) -> bool:
        """البوابة مفعّلة فقط إذا توفّرت بيانات الدخول الأساسية."""
        return bool(self.host and self.user and self.password)


def _process_message(raw_bytes: bytes) -> None:
    """يحلّل رسالة خام واحدة ويحفظ نتيجتها في جلسة قاعدة بيانات مستقلة."""
    email = parse_raw_email(raw_bytes)
    result = analyze_email(email)
    db = SessionLocal()
    try:
        save_analysis(db, email, result)
        logger.info(
            "بوابة البريد: حُلّلت رسالة من %s — الخطورة %s%% (%s)",
            email.sender, result.risk_score, result.risk_level,
        )
    finally:
        db.close()


def _poll_once(config: MailboxConfig) -> int:
    """جولة سحب واحدة: يجلب غير المقروء، يحلّله، ويعيد عدد الرسائل المعالجة."""
    processed = 0
    conn = imaplib.IMAP4_SSL(config.host, config.port)
    try:
        conn.login(config.user, config.password)
        conn.select(config.mailbox)

        # نجلب الرسائل غير المقروءة فقط — الجديدة الواردة
        status, data = conn.search(None, "UNSEEN")
        if status != "OK":
            return 0

        msg_ids = data[0].split()
        for msg_id in msg_ids:
            # BODY.PEEK لا يغيّر حالة القراءة تلقائيًا؛ نتحكم بها بأنفسنا
            fetch_flag = "(BODY.PEEK[])" if not config.mark_seen else "(RFC822)"
            status, msg_data = conn.fetch(msg_id, fetch_flag)
            if status != "OK" or not msg_data or not msg_data[0]:
                continue

            raw_bytes = msg_data[0][1]
            try:
                _process_message(raw_bytes)
                processed += 1
            except Exception:
                logger.exception("بوابة البريد: فشل تحليل رسالة id=%s", msg_id)

            if config.mark_seen:
                conn.store(msg_id, "+FLAGS", "\\Seen")

        return processed
    finally:
        try:
            conn.close()
        except Exception:
            pass
        conn.logout()


def _run_loop(config: MailboxConfig, stop_event: threading.Event) -> None:
    """حلقة السحب الدورية حتى يُطلب الإيقاف."""
    logger.info(
        "بوابة البريد مفعّلة: %s@%s كل %ss (mailbox=%s)",
        config.user, config.host, config.poll_interval, config.mailbox,
    )
    while not stop_event.is_set():
        try:
            count = _poll_once(config)
            if count:
                logger.info("بوابة البريد: عولجت %d رسالة جديدة", count)
        except Exception:
            # خطأ اتصال مؤقت لا يجب أن يُسقط الخيط — نسجّل ونعيد المحاولة
            logger.exception("بوابة البريد: خطأ أثناء جولة السحب، سيُعاد المحاولة")
        stop_event.wait(config.poll_interval)
    logger.info("بوابة البريد: تم الإيقاف")


# مقبض الخيط وحدث الإيقاف على مستوى الوحدة كي يديرهما main.py
_thread: threading.Thread | None = None
_stop_event = threading.Event()


def start_mailbox_gateway() -> bool:
    """
    يشغّل البوابة في خيط خلفي إن كانت مضبوطة. يعيد True عند التشغيل الفعلي،
    وFalse إن كانت معطّلة (بيانات دخول ناقصة) — عندها تبقى المنصة تعمل يدويًا.
    """
    global _thread
    config = MailboxConfig()
    if not config.enabled:
        logger.warning(
            "بوابة البريد معطّلة: لم تُضبط IMAP_HOST / IMAP_USER / IMAP_PASSWORD. "
            "المنصة تعمل بالإدخال اليدوي فقط."
        )
        return False

    _stop_event.clear()
    _thread = threading.Thread(
        target=_run_loop, args=(config, _stop_event), name="mailbox-gateway", daemon=True
    )
    _thread.start()
    return True


def stop_mailbox_gateway() -> None:
    """يوقف خيط البوابة بلطف عند إغلاق التطبيق."""
    _stop_event.set()
    if _thread and _thread.is_alive():
        _thread.join(timeout=5)
