from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ==============================================================================
# 1. القوائم والتصنيفات المعيارية (Enums)
# ==============================================================================

class ImportanceLevel(str, Enum):
    NORMAL = "عادي"
    IMPORTANT = "هام"
    VERY_IMPORTANT = "هام جداً"
    URGENT = "عاجل"

class ConfidentialityLevel(str, Enum):
    PUBLIC = "عام"
    RESTRICTED = "مقيّد"
    CONFIDENTIAL = "سري"
    TOP_SECRET = "سري للغاية"

class TransactionStatus(str, Enum):
    COMPLETED = "منجزة"
    IN_PROGRESS = "قيد المعالجة الميدانية"
    PENDING = "غير منجزة"

class SenderTypeEnum(str, Enum):
    OFFICIAL = "توجيه رسمي"
    PRIVATE = "توجيه خاص"
    CITIZEN = "بلاغ مواطن"


# ==============================================================================
# 2. مخطط استخراج البيانات البصرية والشاملة عبر الذكاء الاصطناعي (AI Extraction)
# ==============================================================================

class AITransactionExtractionSchema(BaseModel):
    transaction_number: str = Field(description="رقم المعاملة أو رقم القيد المطبوع على الخطاب")
    external_ref_number: Optional[str] = Field(default=None, description="رقم الخطاب المرجعي لدى الجهة المرسلة")
    sender_entity_name: str = Field(description="اسم الجهة المرسلة (أمانة جدة، وزارة النقل، المرور، شركة...)")
    sender_sub_department: Optional[str] = Field(default=None, description="الإدارة الفرعية أو الإدارة العامة المذكورة")
    suggested_department_name: str = Field(description="القسم الداخلي الأنسب للتعامل مع هذه المعاملة")
    
    subject: str = Field(description="عنوان أو موضوع المعاملة المستخلص")
    summary: str = Field(description="ملخص تنفيذي دقيق لمحتوى الخطاب في أسطر معدودة")
    extracted_full_text: str = Field(description="التفريغ النصي الكامل المكتوب بداخل صورة المعاملة")
    
    importance: ImportanceLevel = Field(default=ImportanceLevel.NORMAL, description="درجة الأهمية المذكورة أو المستنتجة")
    confidentiality: ConfidentialityLevel = Field(default=ConfidentialityLevel.PUBLIC, description="درجة السرية المطبوعة")
    ai_category: str = Field(description="تصنيف موضوع المعاملة (مثل: صيانة، حفريات، عقود، شكوى، تراخيص)")
    
    letter_date_hijri: Optional[str] = Field(default=None, description="تاريخ المعاملة الهجري المكتوب")
    letter_date_gregorian: Optional[str] = Field(default=None, description="تاريخ المعاملة الميلادي المكتوب")
    
    has_official_stamp: bool = Field(default=False, description="هل تحتوي الصورة على ختم رسمي للجهة؟ True أو False")
    has_signature: bool = Field(default=False, description="هل يحتوي المستند على توقيع رسمي؟ True أو False")
    detected_qr_or_barcode: Optional[str] = Field(default=None, description="قراءة نص الـ QR أو البار كود إن وجد")
    
    estimated_processing_days: int = Field(default=3, description="عدد الأيام المتوقعة لإنجاز المعاملة بناء على تعقيدها")


# ==============================================================================
# 3. مخططات نظم المعلومات الجغرافية والتعلم العميق (GIS & ML Models)
# ==============================================================================

class GISLocationSchema(BaseModel):
    district_name: str = Field(description="اسم الحي في محافظة جدة")
    latitude: float = Field(description="خط العرض الجغرافي")
    longitude: float = Field(description="خط الطول الجغرافي")

class MLPredictionInputSchema(BaseModel):
    district: str = Field(..., description="الحي الميداني")
    sender_type: SenderTypeEnum = Field(..., description="نوع الجهة الراسلة")
    priority: ImportanceLevel = Field(..., description="درجة الأهمية")
    confidentiality: ConfidentialityLevel = Field(..., description="مستوى السرية")
    dept: str = Field(..., description="القطاع المكلف")

class MLPredictionOutputSchema(BaseModel):
    delay_probability_percentage: float = Field(description="احتمالية التعثر/التأخير المئوية من الشبكة العصبية (0-100)")
    risk_category: str = Field(description="تصنيف الخطورة التنبؤي (حرج جداً / عالي / منخفض)")
    cluster_id: int = Field(description="معرف التكتل الجغرافي والإداري K-Means Cluster ID")
    model_accuracy: float = Field(description="دقة النموذج الحالية")


# ==============================================================================
# 4. مخططات المعاملات وإدارتها في قاعدة البيانات (FastAPI & Database Models)
# ==============================================================================

class TransactionCreate(BaseModel):
    transaction_number: str = Field(..., alias="رقم المعاملة")
    subject: str = Field(..., alias="موضوع المعاملة")
    district: str = Field(..., alias="الحي")
    sender_type: str = Field(..., alias="نوع الجهة")
    sender_name: str = Field(..., alias="اسم الجهة")
    importance: str = Field(..., alias="درجة الأهمية")
    confidentiality: str = Field(..., alias="السرية")
    department_name: str = Field(..., alias="القسم المكلف")
    delivery_date: str = Field(..., alias="تاريخ التسليم")
    
    model_config = ConfigDict(populate_by_name=True)

class TransactionResponse(BaseModel):
    id: int
    transaction_number: str = Field(..., alias="رقم المعاملة")
    subject: str = Field(..., alias="موضوع المعاملة")
    district: str = Field(..., alias="الحي")
    latitude: Optional[float] = Field(default=None, alias="lat")
    longitude: Optional[float] = Field(default=None, alias="lon")
    sender_type: str = Field(..., alias="نوع الجهة")
    sender_name: str = Field(..., alias="اسم الجهة")
    importance: str = Field(..., alias="درجة الأهمية")
    confidentiality: str = Field(..., alias="السرية")
    department_name: str = Field(..., alias="القسم المكلف")
    status: str = Field(..., alias="الحالة")
    delivery_date: str = Field(..., alias="تاريخ التسليم")
    expected_date: str = Field(..., alias="التاريخ المتوقع للإنجاز")
    delay_reason: Optional[str] = Field(default=None, alias="سبب عدم الإنجاز")
    risk_score: Optional[float] = Field(default=0.0, alias="مؤشر الخطورة")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==============================================================================
# 5. مخططات المعالجة الصوتية وتحويل النص إلى كلام (Audio, Whisper & TTS)
# ==============================================================================

class AudioTranscriptionResponse(BaseModel):
    file_name: str = Field(description="اسم ملف الصوت المرفوع")
    transcribed_text: str = Field(description="النص المفرغ بدقة عبر OpenAI Whisper")
    language: str = Field(default="ar", description="لغة التفريغ الصوتي")
    duration_seconds: Optional[float] = Field(default=None, description="مدة التسجيل بالسواني")

class TTSGenerateRequest(BaseModel):
    text_content: str = Field(..., description="النص المراد تحويله إلى صوت بشري")
    voice_model: str = Field(default="nova", description="اسم نبرة الصوت البشرية (nova, onyx, alloy)")
    speed: float = Field(default=1.0, description="سرعة النطق الصوتي")


# ==============================================================================
# 6. مخططات الرقابة والحوكمة والتدقيق (Governance & Audit Log)
# ==============================================================================

class AuditLogSchema(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now, description="تاريخ ووقت الإجراء")
    username: str = Field(description="اسم الموظف أو النظام المتخذ للإجراء")
    action_taken: str = Field(description="تفاصيل الإجراء الإداري أو البرمجي")
    compliance_status: str = Field(default="معتمد", description="حالة الامتثال لمعايير الأمانة")
    ip_address: Optional[str] = Field(default="127.0.0.1", description="عنوان IP لتوثيق الجلسة")

class SystemHealthSchema(BaseModel):
    status: str = Field(default="Online")
    total_transactions_count: int = Field(description="إجمالي السجلات المفهرسة (مثلاً 2500 معاملة)")
    database_connected: bool = Field(default=True)
    ml_model_accuracy: float = Field(description="نسبة دقة التعلم العميق")
    developer_identity: str = Field(default="محمد عابد السهلي (Bin3abdAi) | 0507093594 | alsehlii.m7md@gmail.com")