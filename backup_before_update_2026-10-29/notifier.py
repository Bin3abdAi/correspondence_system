"""إشعارات المستفيدين (SMS / بريد) — بوابة موحّدة قابلة للربط مع أي مزوّد.

الإعداد في .env (كله اختياري؛ ما لم يُضبط تظهر رسالة واضحة بدل الفشل الصامت):
  SMS_API_URL     رابط بوابة الرسائل (يستقبل POST بصيغة JSON)
  SMS_API_KEY     مفتاح البوابة (يُرسل في ترويسة Authorization: Bearer)
  SMS_SENDER      اسم المُرسِل (مثال: AmanatJeddah)
  SMS_TO_FIELD / SMS_TEXT_FIELD  أسماء الحقول إن اختلفت عند مزوّدك (الافتراضي: to / message)
البريد يستخدم إعدادات SMTP نفسها في exports.py.
"""
import json
import re
import urllib.request

from config import get_setting

_PHONE_RE = re.compile(r"^(?:\+?966|0)?5\d{8}$")  # جوال سعودي
_EMAIL_RE = re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$")


def normalize_phone(raw: str) -> str:  # يوحّد رقم الجوال السعودي بصيغة 966
    d = re.sub(r"[\s\-()]", "", raw or "")
    if not _PHONE_RE.match(d):
        return ""
    d = d.lstrip("+")
    return "966" + d[-9:]


def send_sms(phone: str, text: str) -> tuple[bool, str]:  # يرسل رسالة نصية عبر بوابة SMS المضبوطة
    url, key = get_setting("SMS_API_URL"), get_setting("SMS_API_KEY")
    if not (url and key):
        return False, "لم تُضبط بوابة الرسائل (SMS_API_URL / SMS_API_KEY) في ملف .env."
    num = normalize_phone(phone)
    if not num:
        return False, "رقم الجوال غير صحيح (مثال: 05XXXXXXXX)."
    body = {get_setting("SMS_TO_FIELD", "to"): num, get_setting("SMS_TEXT_FIELD", "message"): text[:480]}
    if get_setting("SMS_SENDER"):
        body["sender"] = get_setting("SMS_SENDER")
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return (200 <= r.status < 300), ("تم إرسال الرسالة." if r.status < 300 else f"رد البوابة {r.status}")
    except Exception as e:
        return False, f"تعذّر الإرسال: {e}"


def notify(contact: str, subject: str, text: str, ctx=None) -> tuple[bool, str]:  # يختار القناة تلقائياً: بريد إن كان العنوان بريداً، وإلا SMS
    """يختار القناة تلقائياً: بريد إن كان العنوان بريداً، وإلا SMS."""
    contact = (contact or "").strip()
    if _EMAIL_RE.match(contact):
        from exports import send_email
        from security import GUEST
        return send_email(contact, subject, "إشعار", ctx or GUEST, text, [])
    return send_sms(contact, f"{subject}\n{text}")


def status_message(trx: str, status: str, expected: str) -> str:  # نص جاهز لإشعار المستفيد بحالة معاملته (بلا بيانات شخصية أو سرية)
    """نص جاهز لإشعار المستفيد بحالة معاملته (بلا بيانات شخصية أو سرية)."""
    return (f"أمانة محافظة جدة: معاملتك {trx} حالتها «{status}»."
            + (f" الموعد المتوقع للإنجاز: {expected}." if expected else "") + " للتتبع: منصة الأمانة.")