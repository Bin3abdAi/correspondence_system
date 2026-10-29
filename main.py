import logging
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Dict, List, Optional

from ai_service import (
    ADMINISTRATIVE_EXPERT_SYSTEM_INSTRUCTION,
    generate_human_speech_tts,
    transcribe_audio_whisper,
)
import database as db
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# تهيئة تطبيق FastAPI
app = FastAPI(
    title="منظومة أمانة محافظة جدة الذكية - API Gateway",
    description=(
        "خدمات الخلفية الذكية المتقدمة لنظام إدارة المراسلات والتحليلات"
        " التنبؤية (Bin3abdAi Platform)"
    ),
    version="3.5.0",
)

# إعدادات CORS للسماح بالربط
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تهيئة قاعدة البيانات الحقيقية
db.init_db()


# نماذج البيانات الهيكلية
class TransactionCreateSchema(BaseModel):
  trx_id: str = Field(..., example="TRX-JED-2026-1090")
  subject: str = Field(..., example="بلاغ صيانة طريق عاجل")
  district: str = Field(..., example="حي الصفا")
  sender_type: str = Field(..., example="توجيه رسمي")
  sender_name: str = Field(..., example="بلدية الصفا الفرعية")
  priority: str = Field(..., example="عاجل")
  confidentiality: str = Field(..., example="عام")
  assigned_dept: str = Field(..., example="إدارة صيانة الطرق والجسور")


@app.get("/", tags=["النظام الرئيسية"])
def read_root():
  return {
      "system": "Bin3abdAi Smart Municipality Platform",
      "status": "Online",
      "version": "3.5.0",
      "municipality": "أمانة محافظة جدة",
  }


@app.get("/api/transactions", tags=["المعاملات والتسجيل"])
def get_all_transactions():
  """استرجاع كافة المعاملات السريّة والعامة المسجلة بقاعدة البيانات"""
  df = db.get_all_transactions()
  return JSONResponse(content=df.to_dict(orient="records"))


@app.post("/api/transactions", tags=["المعاملات والتسجيل"])
def create_new_transaction(data: TransactionCreateSchema):
  """إضافة معاملة جديدة مباشرة إلى قاعدة بيانات الأمانة"""
  try:
    rec = {
        "رقم المعاملة": data.trx_id,
        "موضوع المعاملة": data.subject,
        "الحي": data.district,
        "نوع الجهة": data.sender_type,
        "اسم الجهة": data.sender_name,
        "درجة الأهمية": data.priority,
        "السرية": data.confidentiality,
        "القسم المكلف": data.assigned_dept,
        "الحالة": "غير منجزة",
        "تاريخ التسليم": str(db.datetime.date.today()),
        "التاريخ المتوقع للإنجاز": str(
            db.datetime.date.today() + db.datetime.timedelta(days=3)
        ),
        "سبب عدم الإنجاز": "معاملة جديدة - مسجلة عبر API Gateway",
    }
    db.add_transaction(rec)
    return {
        "status": "success",
        "message": "تمت إضافة المعاملة بنجاح بقاعدة البيانات",
    }
  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
    )


@app.post("/api/ai/transcribe", tags=["الذكاء الاصطناعي والصوت"])
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
  """تفريغ التسجيلات الصوتية والبلاغات الميدانية عبر Whisper"""
  try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
      shutil.copyfileobj(file.file, tmp)
      tmp_path = Path(tmp.name)

    text_result = transcribe_audio_whisper(tmp_path)
    if os.path.exists(tmp_path):
      os.remove(tmp_path)

    return {"status": "success", "transcribed_text": text_result}
  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
    )


@app.post("/api/ai/tts", tags=["الذكاء الاصطناعي والصوت"])
def tts_endpoint(text: str = Form(...)):
  """تحويل النصوص والتوجيهات إلى صوت بشري باستخدام TTS"""
  try:
    audio_path = generate_human_speech_tts(text)
    return {
        "status": "success",
        "audio_file": audio_path if audio_path else "فشل توليد الصوت",
    }
  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
    )


if __name__ == "__main__":
 uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
 from ai_service import render_global_ai_copilot_widget
render_global_ai_copilot_widget("اسم الصفحة الحالية")