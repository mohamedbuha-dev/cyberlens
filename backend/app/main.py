"""
نقطة انطلاق تطبيق CyberLens - FastAPI.
هذه الحاوية مسؤولة عن الـ API وبوابة البريد (IMAP)؛ الواجهة تُقدَّم من حاوية
Nginx منفصلة (انظر frontend/) وتتواصل مع هذه الخدمة عبر شبكة Docker الداخلية.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import analyze, history
from app.mailbox.poller import start_mailbox_gateway, stop_mailbox_gateway

logging.basicConfig(level=logging.INFO)

# إنشاء جداول قاعدة البيانات عند الإقلاع (إن لم تكن موجودة)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """يشغّل بوابة البريد عند الإقلاع ويوقفها بلطف عند الإغلاق."""
    start_mailbox_gateway()
    yield
    stop_mailbox_gateway()


app = FastAPI(
    title="CyberLens API",
    description="منصة ذكية لتحليل رسائل التصيد الإلكتروني والتوعية الأمنية",
    version="0.3.0",
    lifespan=lifespan,
)

# السماح لحاوية الواجهة (Nginx) بالوصول للـ API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(history.router)


@app.get("/api/health")
def health_check():
    """فحص سريع للتأكد من أن الخدمة تعمل."""
    return {"status": "ok", "service": "CyberLens API"}