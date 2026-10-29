import datetime
from enum import Enum as PyEnum
from typing import Dict, Any

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship, declarative_base

# ==============================================================================
# 0. القاعدة الأساسية لنماذج البيانات (Base Declarative)
# ==============================================================================

Base = declarative_base()

# ==============================================================================
# 1. القوائم والتصنيفات المعيارية (Python Enums)
# ==============================================================================

class ImportanceEnum(str, PyEnum):
    URGENT = "عاجل"
    VERY_IMPORTANT = "هام جداً"
    IMPORTANT = "هام"
    NORMAL = "عادي"

class ConfidentialityEnum(str, PyEnum):
    TOP_SECRET = "سري للغاية"
    SECRET = "سري"
    RESTRICTED = "مقيّد"
    PUBLIC = "عام"

class TransactionStatusEnum(str, PyEnum):
    COMPLETED = "منجزة"
    IN_PROGRESS = "قيد المعالجة الميدانية"
    PENDING = "غير منجزة"
    ESCALATED = "متعثرة ومصعدة"

class SenderTypeEnum(str, PyEnum):
    OFFICIAL = "توجيه رسمي"
    PRIVATE = "توجيه خاص"
    CITIZEN = "بلاغ مواطن"
    MUNICIPAL = "توجيه داخلي"


# ==============================================================================
# 2. نموذج جدول المعاملات الإدارية والميدانية الرئيسي (Transactions Table)
# ==============================================================================

class TransactionModel(Base):
    """
    نموذج المعاملات الرئيسي لأمانة محافظة جدة (SQLAlchemy ORM)
    يدعم الفهرسة السريعة للمليون سجل والتتبع الجغرافي والتحليل التنبؤي.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    trx_num = Column(String(100), unique=True, index=True, nullable=False)
    external_ref_number = Column(String(100), nullable=True, index=True)
    
    subject = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    extracted_full_text = Column(Text, nullable=True)
    
    district = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    sender_type = Column(String(50), nullable=False, default="توجيه رسمي")
    sender_name = Column(String(200), nullable=False)
    sender_sub_dept = Column(String(150), nullable=True)
    
    importance = Column(String(50), nullable=False, default="عادي", index=True)
    confidentiality = Column(String(50), nullable=False, default="عام", index=True)
    dept = Column(String(150), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="غير منجزة", index=True)
    
    has_official_stamp = Column(Boolean, default=False)
    has_signature = Column(Boolean, default=False)
    detected_qr_barcode = Column(String(255), nullable=True)
    
    delivery_date = Column(String(50), nullable=False)
    expected_date = Column(String(50), nullable=False)
    sla_hours = Column(Integer, default=72)
    delay_reason = Column(Text, nullable=True)
    
    risk_score = Column(Float, default=0.5)
    ai_category = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # العلاقات المباشرة مع الجداول المكملة
    predictions = relationship("PredictionLogModel", back_populates="transaction", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogModel", back_populates="transaction")
    notifications = relationship("NotificationModel", back_populates="transaction")

    def to_dict(self) -> Dict[str, Any]:
        """تحويل الكائن إلى قاموس Python لسهولة العرض بـ Pandas أو FastAPI"""
        return {
            "id": self.id,
            "رقم المعاملة": self.trx_num,
            "الرقم المرجعي": self.external_ref_number,
            "موضوع المعاملة": self.subject,
            "ملخص المعاملة": self.summary,
            "الحي": self.district,
            "lat": self.latitude,
            "lon": self.longitude,
            "نوع الجهة": self.sender_type,
            "اسم الجهة": self.sender_name,
            "درجة الأهمية": self.importance,
            "السرية": self.confidentiality,
            "القسم المكلف": self.dept,
            "الحالة": self.status,
            "تاريخ التسليم": self.delivery_date,
            "التاريخ المتوقع للإنجاز": self.expected_date,
            "سبب عدم الإنجاز": self.delay_reason,
            "مؤشر الخطورة": self.risk_score,
            "التصنيف الميداني": self.ai_category,
            "ختم رسمي": self.has_official_stamp,
            "توقيع معتمد": self.has_signature
        }


# ==============================================================================
# 3. نموذج الأقسام والجهات والضباط الميدانيين (Departments & Officers)
# ==============================================================================

class DepartmentModel(Base):
    """جدول الهيكل التنظيمي لأقسام وبلديات أمانة جدة الفرعية"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    manager_email = Column(String(150), nullable=False)
    building_location = Column(String(150), nullable=True)
    target_sla_percentage = Column(Float, default=95.0)
    
    officers = relationship("OfficerModel", back_populates="department")


class OfficerModel(Base):
    """جدول الموظفين والفرق الميدانية المكلفة"""
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    badge_number = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    email = Column(String(150), nullable=False)
    role = Column(String(100), default="مفتش ميداني")
    dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True)

    department = relationship("DepartmentModel", back_populates="officers")


# ==============================================================================
# 4. نموذج سجلات الذكاء الاصطناعي والتعلم العميق (AI Predictions Log)
# ==============================================================================

class PredictionLogModel(Base):
    """جدول حفظ تحليلات ونتائج شبكة التعلم العميق لكل معاملة"""
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    trx_num = Column(String(100), index=True, nullable=False)
    
    model_version = Column(String(50), default="Bin3abdAi-MLP-v4.0")
    predicted_delay_probability = Column(Float, nullable=False)
    predicted_risk_level = Column(String(50), nullable=False)
    cluster_id = Column(Integer, default=0)
    feature_vector_json = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.now)

    transaction = relationship("TransactionModel", back_populates="predictions")


# ==============================================================================
# 5. نموذج حوكمة البيانات وسجلات التدقيق والأمان (Audit Logs - NCA Standards)
# ==============================================================================

class AuditLogModel(Base):
    """جدول حوكمة الأمان والرقابة الذاتية لتوثيق كافة العمليات والنفاذ"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.now, index=True)
    username = Column(String(100), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    action_details = Column(Text, nullable=False)
    compliance_status = Column(String(50), default="معتمد")
    ip_address = Column(String(50), default="127.0.0.1")
    user_agent = Column(String(255), nullable=True)
    
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    transaction = relationship("TransactionModel", back_populates="audit_logs")


# ==============================================================================
# 6. نموذج إشعارات الطوارئ وبث التنبيهات (Emergency Notifications)
# ==============================================================================

class NotificationModel(Base):
    """جدول حفظ وسجل الإشعارات والتنبيهات الموجهة عبر Gmail أو شاشة GIS"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    channel = Column(String(50), default="EMAIL") # EMAIL, GIS_DASHBOARD, SMS
    recipient = Column(String(200), nullable=False)
    alert_title = Column(String(200), nullable=False)
    alert_body = Column(Text, nullable=False)
    severity_level = Column(String(50), default="عالي")
    
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)

    transaction = relationship("TransactionModel", back_populates="notifications")


# ==============================================================================
# 7. نموذج سجل المعالجة الصوتية متعددة الوسائط (Multimodal Audio Logs)
# ==============================================================================

class AudioLogModel(Base):
    """جدول توثيق تفريغ الملاحظات الصوتية بـ Whisper والردود الناطقة بـ TTS"""
    __tablename__ = "audio_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audio_filename = Column(String(255), nullable=False)
    transcribed_text = Column(Text, nullable=True)
    voice_model_used = Column(String(50), default="nova")
    generated_tts_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    