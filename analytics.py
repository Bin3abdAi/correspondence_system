"""منطق مؤشرات الأداء — بدون Streamlit ليسهل اختباره.

وظيفة هذا الملف: كل الحسابات (معدل الإنجاز، الاتجاه، التوقع، أداء الأقسام والفرق).
لا يرسم شيئاً؛ views.py هو من يعرض هذه الأرقام.
"""
from dataclasses import dataclass  # لتعريف «حاوية» أرقام ثابتة بسهولة

import numpy as np   # حسابات رقمية (الانحدار الخطي للتوقع)
import pandas as pd  # جداول البيانات

from config import (RECENT_WEEKS, STATUS_DONE, TARGET_COMPLETION_RATE,  # الثوابت من الإعدادات
                    TREND_THRESHOLD_PTS)

MIN_PERIOD_ROWS = 30  # أقل عدد معاملات في كل فترة حتى لا يُبنى اتجاه على بيانات شحيحة


@dataclass(frozen=True)  # frozen = لا يمكن تعديل القيم بعد إنشائها (أمان)
class Indicator:
    rate: float              # معدل الإنجاز المعتمد للمؤشر (%)
    basis: str               # أساس الحساب: آخر N أسابيع أو الإجمالي
    prev_rate: float | None  # معدل الفترة السابقة (%)
    delta: float | None      # التغير بالنقاط المئوية
    trend: str               # up | down | flat | unknown
    above_target: bool       # هل المعدل فوق المستهدف؟
    positive: bool           # إنذار إيجابي أم سلبي
    title: str               # عنوان الإنذار المعروض
    message: str             # نص الإنذار
    total: int               # إجمالي المعاملات
    done: int                # المنجزة
    overdue: int             # المتأخرة عن موعدها


def _week_start(dates: pd.Series) -> pd.Series:  # بداية الأسبوع (الأحد) لكل تاريخ
    """بداية الأسبوع (الأحد) لكل تاريخ."""
    d = dates.dt.normalize()  # إلغاء الساعة (نبقي اليوم فقط)
    return d - pd.to_timedelta((d.dt.dayofweek + 1) % 7, unit="D")  # الرجوع لأقرب أحد


def weekly_series(df: pd.DataFrame) -> pd.DataFrame:  # معدل الإنجاز الأسبوعي حسب تاريخ الاستلام (الأسابيع المكتملة فقط)
    """معدل الإنجاز الأسبوعي حسب تاريخ الاستلام (الأسابيع المكتملة فقط)."""
    empty = pd.DataFrame(columns=["week", "total", "done", "rate"])  # نتيجة فارغة جاهزة
    if "تاريخ الاستلام" not in df or df.empty:
        return empty
    is_done = df["الحالة"] == STATUS_DONE  # True للمنجزة
    agg = is_done.groupby(_week_start(df["تاريخ الاستلام"])).agg(["size", "sum"])  # العدد والمنجز لكل أسبوع
    if agg.empty:
        return empty
    out = agg.rename(columns={"size": "total", "sum": "done"}).reset_index()  # أسماء أعمدة واضحة
    out.columns = ["week", "total", "done"]
    out["rate"] = out["done"] / out["total"] * 100  # النسبة المئوية
    today = pd.Timestamp.today().normalize()
    return out[out["week"] + pd.Timedelta(days=7) <= today].reset_index(drop=True)  # نستبعد الأسبوع الجاري


def forecast(weekly: pd.DataFrame, horizon: int = 4, window: int = 8):  # توقع خطي تقديري لمعدل الإنجاز
    """توقع خطي تقديري لمعدل الإنجاز. يُرجع (جدول التوقع, الميل بالنقطة/أسبوع)."""
    if len(weekly) < 4:  # بيانات قليلة = لا توقع
        return None, 0.0
    y = weekly["rate"].tail(window).to_numpy(dtype=float)  # آخر 8 أسابيع
    x = np.arange(len(y))  # 0,1,2,...
    slope, intercept = np.polyfit(x, y, 1)  # خط مستقيم يناسب النقاط (انحدار خطي)
    future = np.clip(intercept + slope * np.arange(len(y), len(y) + horizon), 0, 100)  # امتداد الخط بين 0 و100
    last = weekly["week"].iloc[-1]
    weeks = [last + pd.Timedelta(weeks=i + 1) for i in range(horizon)]  # الأسابيع القادمة
    return pd.DataFrame({"week": weeks, "rate": future}), float(slope)


def compute_indicator(df: pd.DataFrame, weekly: pd.DataFrame) -> Indicator:  # يحسب المؤشر الرئيسي: المعدل، الاتجاه، المقارنة بالمستهدف، والمتأخر
    """يحسب المؤشر الرئيسي: المعدل، الاتجاه، المقارنة بالمستهدف، والمتأخر."""
    total = len(df)
    done = int((df["الحالة"] == STATUS_DONE).sum())
    overall = done / total * 100 if total else 0.0  # المعدل الإجمالي

    n = RECENT_WEEKS  # طول الفترة (4 أسابيع)
    rate, basis, prev_rate, delta, trend = overall, "الإجمالي", None, None, "unknown"
    rec, prv = weekly.tail(n), weekly.iloc[-2 * n:-n]  # الفترة الحالية والسابقة
    if len(weekly) >= 2 * n and min(rec["total"].sum(), prv["total"].sum()) >= MIN_PERIOD_ROWS:
        rate = rec["done"].sum() / rec["total"].sum() * 100  # معدل آخر 4 أسابيع
        prev_rate = prv["done"].sum() / prv["total"].sum() * 100  # معدل الأربعة قبلها
        delta = rate - prev_rate  # الفرق بالنقاط
        basis = f"آخر {n} أسابيع"
        trend = ("up" if delta >= TREND_THRESHOLD_PTS
                 else "down" if delta <= -TREND_THRESHOLD_PTS else "flat")  # تحسّن/تراجع/ثبات

    today = pd.Timestamp.today().normalize()
    overdue = 0
    if "تاريخ الإنجاز المتوقع" in df:  # المتأخر = غير منجز وموعده مضى
        overdue = int(((df["الحالة"] != STATUS_DONE) & (df["تاريخ الإنجاز المتوقع"] < today)).sum())

    target = TARGET_COMPLETION_RATE
    above = rate >= target
    gap = f"وما زال دون المستهدف ({target:.0f}%)" if not above else f"وهو فوق المستهدف ({target:.0f}%)"

    if trend == "up":  # صياغة الرسالة حسب الاتجاه
        positive, title = True, "إنذار إيجابي: تحسّن في الأداء"
        message = f"ارتفع معدل الإنجاز {delta:+.1f} نقطة عن الفترة السابقة، {gap}."
    elif trend == "down":
        positive, title = False, "إنذار سلبي: تراجع في الأداء"
        message = f"انخفض معدل الإنجاز {delta:+.1f} نقطة عن الفترة السابقة، {gap}."
    elif trend == "flat":
        positive = above
        title = ("مؤشر إيجابي: أداء مستقر فوق المستهدف" if above
                 else "إنذار سلبي: أداء متعثر")
        message = f"المعدل شبه ثابت (التغير {delta:+.1f} نقطة)، {gap}."
    else:
        positive = above
        title = "بيانات غير كافية لتحديد الاتجاه"
        message = f"معدل الإنجاز الإجمالي {rate:.1f}%، {gap}. يلزم {2 * n} أسابيع من البيانات الكافية لتحديد الاتجاه."
    if overdue:
        message += f" المعاملات المتأخرة عن موعدها: {overdue:,}."

    return Indicator(rate, basis, prev_rate, delta, trend, above, positive,
                     title, message, total, done, overdue)


def department_performance(df: pd.DataFrame) -> pd.DataFrame:  # أداء الأقسام مرتباً من الأضعف إلى الأقوى
    """أداء الأقسام مرتباً من الأضعف إلى الأقوى."""
    if df.empty:
        return pd.DataFrame(columns=["total", "done", "rate"])
    is_done = df["الحالة"] == STATUS_DONE
    g = is_done.groupby(df["القسم المكلف"], observed=True).agg(["size", "sum"])  # العدد والمنجز لكل قسم
    g.columns = ["total", "done"]
    g["rate"] = g["done"] / g["total"] * 100
    return g.sort_values("rate")  # الأضعف أولاً


# ======================================================
# الفرق الميدانية: توزيع المعاملات + نقاط الخريطة + اقتراح الفريق
# ======================================================
from config import DISTRICT_COORDS, STATUS_FIELD  # noqa: E402  (استيراد متأخر لأنه خاص بهذا القسم)

TEAMS_PER_DEPT = 4  # عدد الفرق في كل قسم
_BUCKET_COLORS = {"done": "#10b981", "progress": "#f59e0b", "open": "#f43f5e"}  # ألوان الخريطة: أخضر منجزة / أصفر تحت التنفيذ / أحمر غير منجزة
_URGENT_RANK = {"حرج للغاية": 0, "عاجل": 1}  # ترتيب الخطورة (الأصغر أخطر)
_LAT = {k: v[0] for k, v in DISTRICT_COORDS.items()}  # خط العرض لكل حي
_LON = {k: v[1] for k, v in DISTRICT_COORDS.items()}  # خط الطول لكل حي


def team_name(dept: str, number: int) -> str:  # اسم الفريق للعرض، مثل: النظافة والبيئة — فريق 2
    """اسم الفريق للعرض، مثل: النظافة والبيئة — فريق 2."""
    return f"{str(dept).replace('إدارة ', '')} — فريق {number}"


def status_bucket(status: pd.Series) -> pd.Series:  # ثلاث فئات: done منجزة، progress تحت التنفيذ، open غير منجزة
    """ثلاث فئات: done منجزة، progress تحت التنفيذ، open غير منجزة."""
    values = np.select([(status == STATUS_DONE).to_numpy(), (status == STATUS_FIELD).to_numpy()],
                       ["done", "progress"], "open")  # الشرط الأول ثم الثاني، وإلا open
    return pd.Series(values, index=status.index)


def _hash(ids: pd.Series) -> np.ndarray:  # رقم ثابت لكل معاملة (نفس الرقم دائماً) — نستخدمه للتوزيع التجريبي على الفرق
    """رقم ثابت لكل معاملة (نفس الرقم دائماً) — نستخدمه للتوزيع التجريبي على الفرق."""
    return pd.util.hash_pandas_object(ids.astype(str), index=False).to_numpy()


def assign_teams(df: pd.DataFrame, assignments: dict = None) -> pd.Series:  # رقم الفريق (1..N) لكل معاملة داخل قسمها
    """رقم الفريق (1..N) لكل معاملة داخل قسمها. الافتراضي توزيع تجريبي ثابت بالتجزئة،
    وتُطبَّق فوقه التكليفات المحفوظة."""
    team = pd.Series((_hash(df["رقم المعاملة"]) % TEAMS_PER_DEPT + 1).astype(int), index=df.index)
    if assignments:  # التكليف اليدوي يتغلب على التوزيع التلقائي
        mapping = {trx: a["team"] for trx, a in assignments.items()}
        over = df["رقم المعاملة"].astype(str).map(mapping)
        team = over.fillna(team).astype(int)
    return team


def team_stats(df: pd.DataFrame, team: pd.Series) -> pd.DataFrame:  # أداء كل فريق مرتباً من الأضعف إلى الأقوى
    """أداء كل فريق مرتباً من الأضعف إلى الأقوى."""
    cols = ["اسم الفريق", "القسم المكلف", "الفريق", "الإجمالي", "منجزة",
            "قيد التنفيذ", "غير المنجزة", "مفتوحة", "نسبة الإنجاز"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    g = pd.crosstab([df["القسم المكلف"].astype(str), team.rename("الفريق")], status_bucket(df["الحالة"]))  # جدول تقاطعي
    g = g.reindex(columns=["done", "progress", "open"], fill_value=0)  # نضمن وجود الأعمدة الثلاثة
    g.columns = ["منجزة", "قيد التنفيذ", "غير المنجزة"]
    g["الإجمالي"] = g.sum(axis=1)
    g["مفتوحة"] = g["قيد التنفيذ"] + g["غير المنجزة"]
    g["نسبة الإنجاز"] = g["منجزة"] / g["الإجمالي"] * 100
    g = g.reset_index()
    g.insert(0, "اسم الفريق", [team_name(d, n) for d, n in zip(g["القسم المكلف"], g["الفريق"])])
    return g[cols].sort_values("نسبة الإنجاز").reset_index(drop=True)


def map_points(df: pd.DataFrame, team: pd.Series = None, dept: str = None, team_no: int = None,
               limit: int = 3000, focus_urgent: bool = False) -> pd.DataFrame:  # نقاط الخريطة: موقع تقريبي داخل الحي + لون الحالة + بيانات المعاملة للتلميح (to
    """نقاط الخريطة: موقع تقريبي داخل الحي + لون الحالة + بيانات المعاملة للتلميح (tooltip).
    focus_urgent=True يضمن ظهور العاجل/الحرج المفتوح أولاً عند الكثرة. تُؤخذ عينة ثابتة إن زادت عن الحد."""
    cols = ["lat", "lon", "color", "size", "bucket", "trx", "subject", "district", "dept", "status", "priority"]
    empty = pd.DataFrame(columns=cols)
    if df.empty:
        return empty
    mask = pd.Series(True, index=df.index)
    if dept:
        mask &= df["القسم المكلف"] == dept  # فلترة بالقسم
    if team_no and team is not None:
        mask &= team == team_no  # فلترة بالفريق
    d = df[mask]
    if d.empty:
        return empty
    if len(d) > limit:
        if focus_urgent:  # نبدأ بالعاجل/الحرج المفتوح ثم نكمّل بعينة من الباقي
            hot = d[(d["الحالة"] != STATUS_DONE) & d["درجة الأهمية"].isin(list(_URGENT_RANK))]
            hot = hot.sample(min(len(hot), limit // 2), random_state=7)
            rest = d.drop(hot.index).sample(limit - len(hot), random_state=7)
            d = pd.concat([hot, rest])
        else:
            d = d.sample(limit, random_state=7)  # عينة ثابتة حتى لا تثقل الخريطة
    h = _hash(d["رقم المعاملة"])
    jitter_a = ((h % 2001).astype(float) - 1000) / 1000 * 0.011  # إزاحة صغيرة لتفريق النقاط داخل الحي
    jitter_b = (((h // 2001) % 2001).astype(float) - 1000) / 1000 * 0.011
    district = d["الحي"].astype(str)
    out = pd.DataFrame({"lat": district.map(_LAT).to_numpy() + jitter_a,
                        "lon": district.map(_LON).to_numpy() + jitter_b,
                        "bucket": status_bucket(d["الحالة"]).to_numpy(),
                        "trx": d["رقم المعاملة"].astype(str).to_numpy(),
                        "subject": d["موضوع المعاملة"].astype(str).str.slice(0, 80).to_numpy(),
                        "district": district.to_numpy(),
                        "dept": d["القسم المكلف"].astype(str).to_numpy(),
                        "status": d["الحالة"].astype(str).to_numpy(),
                        "priority": d["درجة الأهمية"].astype(str).to_numpy()})
    out["color"] = out["bucket"].map(_BUCKET_COLORS)  # لون كل نقطة
    out["size"] = 110
    return out.dropna(subset=["lat", "lon"]).reset_index(drop=True)


def suggest_team(stats: pd.DataFrame, dept: str):  # أنسب فريق في القسم = الأقل مهاماً مفتوحة (ثم الأعلى إنجازاً)
    """أنسب فريق في القسم = الأقل مهاماً مفتوحة (ثم الأعلى إنجازاً). يُرجع (رقم الفريق, مفتوحة) أو None."""
    s = stats[stats["القسم المكلف"] == dept]
    if s.empty:
        return None
    best = s.sort_values(["مفتوحة", "نسبة الإنجاز"], ascending=[True, False]).iloc[0]
    return int(best["الفريق"]), int(best["مفتوحة"])


def urgent_open(df: pd.DataFrame, limit: int = 25) -> pd.DataFrame:  # المعاملات العاجلة/الحرجة غير المنجزة، الأخطر ثم الأقرب موعداً
    """المعاملات العاجلة/الحرجة غير المنجزة، الأخطر ثم الأقرب موعداً."""
    cols = ["رقم المعاملة", "موضوع المعاملة", "الحي", "القسم المكلف", "درجة الأهمية", "تاريخ الإنجاز المتوقع"]
    mask = (df["الحالة"] != STATUS_DONE) & df["درجة الأهمية"].isin(list(_URGENT_RANK))
    sub = df.loc[mask, [c for c in cols if c in df.columns]].copy()
    if sub.empty:
        return sub
    sub["_r"] = sub["درجة الأهمية"].astype(str).map(_URGENT_RANK)  # رتبة الخطورة
    by = ["_r"] + (["تاريخ الإنجاز المتوقع"] if "تاريخ الإنجاز المتوقع" in sub else [])
    return sub.sort_values(by).head(limit).drop(columns="_r").reset_index(drop=True)


# ---- اتفاقية مستوى الخدمة (SLA) والتنبيهات المبكرة ----
def sla_summary(df: pd.DataFrame, today=None, soon_days: int = 1) -> dict:  # يحسب المتأخر (تجاوز الموعد) والمستحق قريباً (خلال soon_days) لكل إدارة، للمعام
    """يحسب المتأخر (تجاوز الموعد) والمستحق قريباً (خلال soon_days) لكل إدارة، للمعاملات غير المنجزة فقط."""
    today = pd.Timestamp(today or pd.Timestamp.today()).normalize()
    empty = {"overdue": 0, "soon": 0, "by_dept": pd.DataFrame(columns=["القسم المكلف", "متأخرة", "تستحق قريباً"]),
             "worst": df.head(0)}
    if df.empty or "تاريخ الإنجاز المتوقع" not in df.columns:
        return empty
    open_ = df[df["الحالة"] != STATUS_DONE]
    due = open_["تاريخ الإنجاز المتوقع"]
    late = open_[due < today]
    soon = open_[(due >= today) & (due <= today + pd.Timedelta(days=soon_days))]
    dept = pd.DataFrame({
        "متأخرة": late.groupby("القسم المكلف", observed=True).size(),
        "تستحق قريباً": soon.groupby("القسم المكلف", observed=True).size(),
    }).fillna(0).astype(int).reset_index()
    dept = dept.rename(columns={dept.columns[0]: "القسم المكلف"}).sort_values("متأخرة", ascending=False)
    cols = [c for c in ["رقم المعاملة", "الحي", "القسم المكلف", "درجة الأهمية", "تاريخ الإنجاز المتوقع"] if c in late.columns]
    worst = late.sort_values("تاريخ الإنجاز المتوقع")[cols].head(10)
    return {"overdue": len(late), "soon": len(soon), "by_dept": dept, "worst": worst}