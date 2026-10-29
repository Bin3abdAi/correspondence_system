"""التحية الواعية بالوقت والمستخدم (بلا Streamlit): صباح/مساء بتوقيت جدة، وأسلوب مناسب لنوع الدخول.

وظيفة هذا الملف: مصدر واحد لنص الترحيب الصوتي والمكتوب وقاعدة أسلوب المساعد، حتى يتطابق ما يُقال مع ما يُعرض.
  • الزائر: ترحيب دافئ وإرشاد.   • الموظف: عملي ودود.   • مدير الإدارة / مدير النظام: جاد ومختصر («وقت الجد جد»).
  • الفترة: صباح الخير (4–11) · مساء الخير (12–17) · مساء النور (18–3) — ويوم الجمعة تُضاف «وجمعة مباركة».
"""
from __future__ import annotations

import datetime
import re

RIYADH = datetime.timezone(datetime.timedelta(hours=3))  # توقيت جدة/الرياض (UTC+3) ثابت بلا توقيت صيفي
_AR_NAME = re.compile(r"[؀-ۿ ]+")  # اسم عربي صرف فقط (الأسماء اللاتينية تُنطق خطأً)


def riyadh_now(now: datetime.datetime | None = None) -> datetime.datetime:  # الوقت الآن بتوقيت جدة
    if now is None:
        return datetime.datetime.now(RIYADH)
    return now.astimezone(RIYADH) if now.tzinfo else now.replace(tzinfo=RIYADH)


def day_part(hour: int) -> str:  # التحية حسب الساعة؛ ما بعد منتصف الليل حتى الفجر «مساء النور» لا «صباح الخير»
    if 4 <= hour < 12:
        return "صباح الخير"
    if 12 <= hour < 18:
        return "مساء الخير"
    return "مساء النور"


def is_friday(now: datetime.datetime | None = None) -> bool:
    return riyadh_now(now).weekday() == 4


def salutation(now: datetime.datetime | None = None) -> str:  # «صباح الخير» أو «مساء النور»... (+ وجمعة مباركة يوم الجمعة)
    n = riyadh_now(now)
    base = day_part(n.hour)
    return base + " وجمعة مباركة" if n.weekday() == 4 else base


def arabic_name(username: str | None) -> str:  # الاسم إن كان عربياً صرفاً وإلا فراغ
    u = str(username or "").strip()
    return u if u and _AR_NAME.fullmatch(u) else ""


def address(role: str, username: str | None = None, logged_in: bool = False) -> str:  # كيف يُخاطَب المستخدم
    name = arabic_name(username)
    if not logged_in or role == "guest":
        return "يا ضيفنا الكريم"
    if role == "admin":
        return "يا طويل العمر"
    if role == "manager":
        return f"يا {name}" if name else "يا مدير الإدارة"
    if role == "reviewer":
        return f"يا {name}" if name else "أيها المراجع الكريم"
    return f"يا {name}" if name else "يا زميلنا الكريم"


_HERO_ROLE = {"admin": "مدير النظام", "manager": "مدير الإدارة", "reviewer": "المراجع الكريم", "employee": "زميلنا الكريم"}


def hero_user(role: str, username: str | None = None, logged_in: bool = False) -> str:
    """ما يظهر بعد التحية في الواجهة الرئيسية: «ضيفنا الكريم» للزائر، وللمسجّل صفته (مع اسمه إن كان عربياً)."""
    if not logged_in or role == "guest":
        return "ضيفنا الكريم"
    base = _HERO_ROLE.get(role, "زميلنا الكريم")
    name = arabic_name(username)
    return f"{base} {name}" if name and role in ("admin", "manager") else (name or base)


def welcome_speech(role: str, username: str | None = None, logged_in: bool = False,
                   now: datetime.datetime | None = None) -> str:
    """نص الترحيب الصوتي: يعرّف المستخدم ويضبط الأسلوب حسب نوع الدخول. جمل قصيرة تناسب النطق، بلا أرقام ولا رموز."""
    sal = salutation(now)
    who = address(role, username, logged_in)
    if not logged_in or role == "guest":
        return (f"{sal} {who}، حيّاك الله في منصة أمانة محافظة جدة الذكية. أنا مساعدك: أتابع لك معاملتك، "
                "وأعرّفك على مشاريع الأمانة، وأجاوب أسئلتك. تفضّل، أنا بخدمتك.")
    if role == "admin":
        return (f"{sal} {who}. الأرقام جاهزة بين يديك: المتأخرات، ومؤشرات الأداء، والتوقعات. تأمر بشيء؟")
    if role == "manager":
        return (f"{sal} {who}. إدارتك أمامك: المعاملات المتأخرة، والفرق الميدانية، ومهل الإنجاز. من وين نبدأ؟")
    if role == "reviewer":
        return (f"{sal} {who}. وضع المراجعة مفعّل: كل شيء متاح للاطلاع والتدقيق. اسألني عمّا تحتاج.")
    return (f"{sal} {who}. المعاملات الجديدة بانتظارك، وأنا جاهز أحلّل وأصيغ الخطابات. من وين نبدأ؟")


# قاعدة أسلوب المساعد حسب نوع الدخول (تُضاف لتعليمات النظام): «وقت الجد جد»
STYLE_BY_ROLE = {
    "admin": "المستخدم مدير النظام: وقت الجد جد. ابدأ بالخلاصة والأرقام ثم التوصية، بجمل قصيرة ورسمية محترمة (طال عمرك)، بلا مزاح أثناء العمل إلا إن بدأه هو.",
    "manager": "المستخدم مدير إدارة: نبرة جادة ومحترمة ومختصرة؛ ركّز على إدارته (المتأخر والمهل والفرق الميدانية) وقدّم توصية عملية.",
    "employee": "المستخدم موظف: نبرة مهنية ودودة وعملية بخطوات واضحة قصيرة، ومزاح خفيف جداً فقط إن بدأه هو.",
    "reviewer": "المستخدم مراجع (قراءة فقط): دقة وتوثيق؛ اذكر الأرقام ومصدرها ولا تقترح تعديل أي بيان.",
    "guest": "المستخدم زائر: ترحيب دافئ وبسيط بلا مصطلحات تقنية؛ أرشده لخدمات المنصة (تتبّع المعاملة، المشاريع، البيانات المفتوحة، الدعم) وذكّره أن الأرقام المعروضة عامة.",
}


def style_rule(role: str) -> str:
    return STYLE_BY_ROLE.get(role, STYLE_BY_ROLE["guest"])


def time_line(now: datetime.datetime | None = None) -> str:  # سطر للمساعد: الوقت الآن بجدة وفترة اليوم (ليردّ التحية بما يناسب)
    n = riyadh_now(now)
    return f"الوقت الآن في جدة: {n:%H:%M}، والتحية المناسبة: «{salutation(n)}»."
