"""المصادقة: تجزئة كلمات المرور، تسجيل الدخول/الخروج، وسياق المستخدم الحالي.

لتوليد hash لكلمة مرور:  python auth.py
ثم ضعه في ملف .env في ADMIN_PASSWORD_HASH أو EMPLOYEE_PASSWORD_HASH
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time

import streamlit as st

from config import get_setting
from security import GUEST, AuthContext, audit

_ITERATIONS = 200_000
_MAX_ATTEMPTS = 5
_LOCK_SECONDS = 60
_SESSION_KEY = "auth_user"
try:  # دقائق الخمول قبل إنهاء الجلسة (من .env: IDLE_TIMEOUT_MINUTES) والافتراضي 20
    _IDLE_MINUTES = int(get_setting("IDLE_TIMEOUT_MINUTES", "20") or 20)
except ValueError:
    _IDLE_MINUTES = 20


def hash_password(password: str) -> str:  # يحوّل كلمة المرور إلى تجزئة PBKDF2 مع ملح (للتخزين الآمن)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored: str) -> bool:  # يتحقق من كلمة المرور مقابل التجزئة المخزّنة
    try:
        salt_hex, digest_hex = stored.split(":")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), _ITERATIONS
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def _users() -> dict:  # قائمة الحسابات المعرّفة في .env (مدير، موظف، مدير إدارة، مراجع)
    users = {
        "admin": {"role": "admin", "hash": get_setting("ADMIN_PASSWORD_HASH")},
        "employee": {"role": "employee", "hash": get_setting("EMPLOYEE_PASSWORD_HASH")},
    }
    # مدير إدارة: يرى بيانات إدارته فقط (MANAGER_DEPT يطابق اسم القسم تماماً مثل «إدارة صيانة الطرق والإنارة»)
    if get_setting("MANAGER_PASSWORD_HASH"):
        users[get_setting("MANAGER_USER", "manager")] = {
            "role": "manager", "hash": get_setting("MANAGER_PASSWORD_HASH"),
            "department": get_setting("MANAGER_DEPT", "")}
    # مراجع: قراءة فقط (جهة رقابية أو مدقق)
    if get_setting("REVIEWER_PASSWORD_HASH"):
        users[get_setting("REVIEWER_USER", "reviewer")] = {
            "role": "reviewer", "hash": get_setting("REVIEWER_PASSWORD_HASH")}
    return users


# ---- التحقق الثنائي (2FA) للمدير: تطبيق مصادقة TOTP (أو رمز بالبريد) ----
_OTP_SECONDS = 300  # صلاحية رمز البريد
_PENDING_KEY = "pending_2fa"


def totp_code(secret_b32: str, at: float | None = None, step: int = 30) -> str:  # رمز TOTP قياسي (RFC 6238) يتوافق مع Google/Microsoft Authenticator بلا أي مكتب
    """رمز TOTP قياسي (RFC 6238) يتوافق مع Google/Microsoft Authenticator بلا أي مكتبة إضافية."""
    key = base64.b32decode(secret_b32.replace(" ", "").upper() + "=" * (-len(secret_b32.replace(" ", "")) % 8))
    counter = int((at if at is not None else time.time()) // step)
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    off = mac[-1] & 0x0F
    return f"{(struct.unpack('>I', mac[off:off + 4])[0] & 0x7FFFFFFF) % 1_000_000:06d}"


def verify_totp(secret_b32: str, code: str) -> bool:  # يتحقق من رمز التطبيق (نافذة ±30 ثانية)
    code = (code or "").strip().replace(" ", "")
    now = time.time()
    try:  # نسمح بفارق نافذة واحدة (±30 ثانية) لاختلاف الساعات
        return any(hmac.compare_digest(totp_code(secret_b32, now + d * 30), code) for d in (-1, 0, 1))
    except Exception:
        return False


def twofa_mode(role: str) -> str:  # totp أو email أو «» (غير مفعّل)
    """totp أو email أو «» (غير مفعّل). يُفرض على المدير فقط."""
    if role != "admin":
        return ""
    if get_setting("ADMIN_TOTP_SECRET"):
        return "totp"
    if get_setting("ADMIN_2FA_EMAIL"):
        return "email"
    return ""


def get_auth_context() -> AuthContext:  # المصدر الوحيد لمعرفة هل المستخدم مسجّل دخول وبأي صلاحية
    """المصدر الوحيد لمعرفة هل المستخدم مسجّل دخول وبأي صلاحية."""
    user = st.session_state.get(_SESSION_KEY)
    return AuthContext(True, user["username"], user["role"], user.get("department", "")) if user else GUEST


def _reset_conversation() -> None:  # يفرّغ المحادثة عند تغيّر الصلاحية حتى لا يتسرب سري
    # تفريغ المحادثة عند تغيّر الصلاحية حتى لا تبقى ردود سرية في السياق
    st.session_state["chat_history"] = []


def login(username: str, password: str) -> tuple[bool, str]:  # يسجّل الدخول ويطبّق القفل بعد المحاولات الفاشلة والتحقق الثنائي
    if time.time() < st.session_state.get("lock_until", 0):
        return False, "محاولات كثيرة. حاول مرة أخرى بعد دقيقة."

    user = _users().get((username or "").strip())
    if user and not user["hash"]:
        return False, "لم تُضبط كلمة المرور لهذا الحساب. شغّل: python auth.py"

    if user and verify_password(password or "", user["hash"]):
        name = username.strip()
        mode = twofa_mode(user["role"])
        if mode:  # كلمة المرور صحيحة لكن الدخول لا يكتمل قبل رمز التحقق
            st.session_state[_PENDING_KEY] = {"username": name, "role": user["role"], "mode": mode,
                                              "department": user.get("department", ""), "tries": 0}
            if mode == "email":
                _send_email_otp()
            audit("login_2fa_required", AuthContext(False, name, user["role"]))
            return False, "أدخل رمز التحقق لإكمال الدخول."
        _finish_login(name, user["role"], user.get("department", ""))
        return True, "تم تسجيل الدخول."

    attempts = st.session_state.get("failed_attempts", 0) + 1
    st.session_state["failed_attempts"] = attempts
    if attempts >= _MAX_ATTEMPTS:
        st.session_state["lock_until"] = time.time() + _LOCK_SECONDS
        st.session_state["failed_attempts"] = 0
    audit("login_failed", GUEST, attempted_user=(username or "")[:50])
    return False, "اسم المستخدم أو كلمة المرور غير صحيحة."


def _finish_login(name: str, role: str, department: str = "") -> None:  # يثبّت الجلسة بعد نجاح كلمة المرور (وبعد الرمز للمدير)
    st.session_state[_SESSION_KEY] = {"username": name, "role": role, "department": department}
    st.session_state["authenticated"] = True  # للتوافق مع الصفحات القديمة
    st.session_state["failed_attempts"] = 0
    st.session_state.pop(_PENDING_KEY, None)
    _reset_conversation()
    audit("login_ok", AuthContext(True, name, role, department))


def _send_email_otp() -> None:  # يرسل رمز تحقق بالبريد (بديل التطبيق)
    from exports import send_email  # استيراد متأخر لتفادي الدوران
    code = f"{secrets.randbelow(1_000_000):06d}"
    st.session_state["otp_hash"] = hashlib.sha256(code.encode()).hexdigest()
    st.session_state["otp_exp"] = time.time() + _OTP_SECONDS
    ok, msg = send_email(get_setting("ADMIN_2FA_EMAIL"), "رمز التحقق لدخول المدير", "OTP",
                         GUEST, f"رمز التحقق: {code}\nصالح لمدة 5 دقائق. إن لم تطلبه فتجاهل الرسالة.", [])
    st.session_state["otp_send_msg"] = "" if ok else msg


def pending_2fa() -> dict | None:  # يرجع حالة الدخول المعلّقة بانتظار رمز التحقق
    return st.session_state.get(_PENDING_KEY)


def cancel_2fa() -> None:  # يلغي عملية الدخول المعلّقة
    st.session_state.pop(_PENDING_KEY, None)


def verify_2fa(code: str) -> tuple[bool, str]:  # يكمل الدخول إن صحّ الرمز
    """يكمل الدخول إن صحّ الرمز. 5 محاولات خاطئة تُلغي العملية."""
    p = st.session_state.get(_PENDING_KEY)
    if not p:
        return False, "لا توجد عملية دخول معلّقة."
    ok = False
    if p["mode"] == "totp":
        ok = verify_totp(get_setting("ADMIN_TOTP_SECRET"), code)
    else:
        exp = st.session_state.get("otp_exp", 0)
        h = st.session_state.get("otp_hash", "")
        ok = time.time() < exp and hmac.compare_digest(hashlib.sha256((code or "").strip().encode()).hexdigest(), h)
    if ok:
        _finish_login(p["username"], p["role"], p.get("department", ""))
        return True, "تم تسجيل الدخول."
    p["tries"] = p.get("tries", 0) + 1
    audit("login_2fa_failed", GUEST, attempted_user=p["username"])
    if p["tries"] >= 5:
        st.session_state.pop(_PENDING_KEY, None)
        st.session_state["lock_until"] = time.time() + _LOCK_SECONDS
        return False, "محاولات كثيرة. أعد تسجيل الدخول بعد دقيقة."
    return False, "الرمز غير صحيح أو منتهي."


def logout(ctx: AuthContext) -> None:  # يسجّل الخروج ويمسح الجلسة والمحادثة
    audit("logout", ctx)
    st.session_state.pop(_SESSION_KEY, None)
    st.session_state["authenticated"] = False
    _reset_conversation()


def check_idle(ctx: AuthContext) -> bool:  # ينهي جلسة المستخدم المسجَّل إن مرّ عليه زمن خمول أطول من الحد
    """ينهي جلسة المستخدم المسجَّل إن مرّ عليه زمن خمول أطول من الحد. يرجع True إن أُنهيت الجلسة.
    (يُفحص عند كل تفاعل؛ المتصفح الخامل لا يرسل شيئاً فيُفحص عند أول حركة بعد الخمول.)"""
    now = time.time()
    last = st.session_state.get("last_active", now)
    st.session_state["last_active"] = now
    if ctx.logged_in and now - last > _IDLE_MINUTES * 60:
        logout(ctx)
        audit("session_idle_timeout", ctx)
        st.session_state["idle_notice"] = True
        return True
    return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "totp":  # python auth.py totp  ← يولّد مفتاح التحقق الثنائي
        sec = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
        print("ضع هذا السطر في .env:\nADMIN_TOTP_SECRET=" + sec)
        print("ثم في تطبيق Google Authenticator: إضافة حساب ← إدخال مفتاح الإعداد، واكتب المفتاح أعلاه (نوع: زمني).")
    else:
        import getpass

        print(hash_password(getpass.getpass("كلمة المرور: ")))