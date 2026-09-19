#!/usr/bin/env python3
"""
حقن عيّنات إيميلات الدِيمو مباشرة في صندوق البريد المُراقَب عبر IMAP APPEND.

لماذا APPEND وليس إرسال SMTP؟
    إرسال عبر Gmail SMTP يعيد كتابة ترويسة From إلى حساب المرسل الحقيقي،
    فتضيع عناوين الانتحال (spoofing) وينهار الدِيمو. APPEND يضع الرسالة الخام
    كما هي في الصندوق مع ترويساتها الأصلية، فتظهر للبوابة كرسالة واردة جديدة.

الاستخدام (من مجلد المشروع، بعد تعبئة .env):
    python3 demo/inject_samples.py
"""
import glob
import imaplib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
SAMPLES_DIR = os.path.join(HERE, "samples")


def load_env(path):
    """قارئ .env بسيط (KEY=VALUE) دون الاعتماد على حزم خارجية."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def main():
    load_env(os.path.join(PROJECT_ROOT, ".env"))

    host = os.getenv("IMAP_HOST", "").strip()
    port = int(os.getenv("IMAP_PORT", "993"))
    user = os.getenv("IMAP_USER", "").strip()
    password = os.getenv("IMAP_PASSWORD", "").strip()
    mailbox = os.getenv("IMAP_MAILBOX", "INBOX").strip()

    if not (host and user and password):
        sys.exit("خطأ: IMAP_HOST / IMAP_USER / IMAP_PASSWORD غير مضبوطة. عبّئ ملف .env أولًا.")

    sample_files = sorted(glob.glob(os.path.join(SAMPLES_DIR, "*.eml")))
    if not sample_files:
        sys.exit(f"لم يُعثر على عيّنات في {SAMPLES_DIR}")

    print(f"الاتصال بـ {user}@{host} ...")
    conn = imaplib.IMAP4_SSL(host, port)
    try:
        conn.login(user, password)
        for path in sample_files:
            with open(path, "rb") as f:
                raw = f.read()
            # IMAP يتطلب نهايات أسطر CRLF
            raw = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            # بدون علامة \Seen كي تظهر للبوابة كرسالة غير مقروءة
            conn.append(mailbox, None, None, raw)
            print(f"  ✓ حُقنت: {os.path.basename(path)}")
    finally:
        conn.logout()

    print("\nتم. راقب اللوحة على http://localhost:8081 — ستظهر النتائج خلال ثوانٍ.")


if __name__ == "__main__":
    main()
