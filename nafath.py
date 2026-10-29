"""دخول «نفاذ» — نسخة تجريبية (محاكاة) لتجربة الدخول الوطني الموحّد داخل المنصة.

مهم: هذه محاكاة لشكل التجربة فقط وليست ربطاً حقيقياً بخدمة نفاذ؛ لا تتحقق من هوية أحد.
الربط الفعلي يحتاج اعتماد الجهة لدى مشغّل الخدمة ومفاتيح ربط رسمية، ولم يُفعَّل في هذه النسخة (NAFATH_MODE=live يعرض تنبيهاً فقط).

الإعدادات في .env (كلها اختيارية):
  NAFATH_MODE         demo (الافتراضي) | off لإخفاء الزر | live (غير مفعّل: يعرض تنبيهاً)
  NAFATH_DEMO_USERS   ربط هويات تجريبية بحسابات موظفين موجودة أصلاً، بالصيغة: 1000000008:employee,1000000016:reviewer
                      بدونه ينتهي الطلب بـ «هوية موثّقة تجريبياً» بصلاحيات الزائر نفسها (لا تُمنح أي صلاحية إضافية).
                      حساب المدير admin لا يُربط أبداً (يبقى بكلمة المرور + التحقق الثنائي).
تحذير: ربط هوية بحساب في الوضع التجريبي يعني أن من يعرف الرقم يستطيع الدخول به. استعمله للتجربة المحلية فقط.

دوال هذا الملف نقية (بلا Streamlit) لتسهيل الاختبار؛ حالة الجلسة تديرها views_shell و auth.
"""
import hashlib
import re
import secrets
import time

from config import get_setting

REQUEST_TTL = 120  # صلاحية الطلب بالثواني
MAX_REQUESTS = 8  # أقصى عدد طلبات خلال النافذة (حماية من التجريب المتكرر)
WINDOW = 300
DEMO_ID = "1000000008"  # رقم تجريبي صالح الصيغة (ليس لشخص حقيقي)
NEVER_ROLES = {"admin"}  # أدوار لا تُمنح عبر المحاكاة أبداً


def mode() -> str:  # off أو demo أو live
    m = (get_setting("NAFATH_MODE", "demo") or "demo").strip().lower()
    return m if m in ("off", "demo", "live") else "demo"


def valid_id(nid: str) -> bool:
    """رقم هوية وطنية (1…) أو إقامة (2…) من 10 أرقام يجتاز فحص Luhn (الفحص المعتمد لأرقام الهوية السعودية)."""
    n = (nid or "").strip()
    if not re.fullmatch(r"[12]\d{9}", n):
        return False
    total = 0
    for i, ch in enumerate(n):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def mask(nid: str) -> str:  # 10••••••08 (لا نعرض الرقم كاملاً ولا نخزّنه)
    n = (nid or "").strip()
    return n[:2] + "•" * max(len(n) - 4, 0) + n[-2:] if len(n) >= 6 else "••••"


def demo_users() -> dict:
    """ربط الهويات التجريبية بحسابات موجودة: {رقم_الهوية: اسم_الحساب}. الصيغة 1000000008:employee,1000000016:reviewer."""
    out = {}
    for part in re.split(r"[,;\n]+", get_setting("NAFATH_DEMO_USERS", "") or ""):
        m = re.fullmatch(r"\s*(\d{10})\s*[:=]\s*(\S+)\s*", part)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def new_request(nid: str, now: float | None = None) -> dict:
    """طلب جديد: رقم عشوائي من خانتين يختاره المستخدم في تطبيق نفاذ (كما في التجربة الحقيقية). لا يُخزَّن الرقم الأصلي إلا مجزّأً."""
    t = time.time() if now is None else now
    return {"rid": secrets.token_hex(6), "random": f"{secrets.randbelow(90) + 10}", "mask": mask(nid),
            "nid_hash": hashlib.sha256(("naf|" + nid).encode()).hexdigest(), "created": t, "exp": t + REQUEST_TTL}


def expired(req: dict, now: float | None = None) -> bool:
    return (time.time() if now is None else now) > req.get("exp", 0)


def seconds_left(req: dict, now: float | None = None) -> int:
    return max(0, int(req.get("exp", 0) - (time.time() if now is None else now)))


def matches(req: dict, nid: str) -> bool:  # هل هذه الهوية هي صاحبة الطلب (مقارنة بالتجزئة)
    return secrets.compare_digest(req.get("nid_hash", ""), hashlib.sha256(("naf|" + nid).encode()).hexdigest())


def rate_ok(stamps: list, now: float | None = None) -> bool:  # عدد الطلبات خلال آخر 5 دقائق
    t = time.time() if now is None else now
    return len([s for s in stamps if t - s < WINDOW]) < MAX_REQUESTS


def account_for(nid: str, users: dict) -> tuple:
    """الحساب المرتبط بالهوية التجريبية: (اسم الحساب, معلوماته) أو (None, None).
    يُرفض المدير admin وأي حساب غير موجود أو بلا كلمة مرور مضبوطة (حساب غير مفعّل)."""
    name = demo_users().get(nid)
    info = users.get(name or "")
    if not info or info.get("role") in NEVER_ROLES or not info.get("hash"):
        return None, None
    return name, info
