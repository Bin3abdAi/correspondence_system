"""طبقة البيانات: تحميل السجلات، تجهيزها للتحليل، أدوات الاستيراد، وحفظ التكليفات والتقارير الميدانية.

وظيفة هذا الملف: هو «الجسر» بين قاعدة البيانات (database.py) وبين الواجهة (views.py / analytics.py).
لا يحتوي على أي كود رسم أو تصميم؛ فقط بيانات ومنطق.
"""
from __future__ import annotations  # يسمح بكتابة أنواع مثل dict | None في كل إصدارات بايثون

import datetime  # للتعامل مع التواريخ والأوقات
import json      # لقراءة/كتابة ملفات JSON (التكليفات والتقارير)
import os        # لاستبدال الملفات بشكل آمن
import re        # للتعابير النمطية (مطابقة الكلمات البلدية)
import uuid      # لتوليد أرقام فريدة قصيرة (أسماء الصور وأرقام المعاملات)
from pathlib import Path  # للتعامل مع المسارات بشكل مريح

import numpy as np   # عمليات رقمية سريعة (توليد البيانات التجريبية)
import pandas as pd  # جداول البيانات
import streamlit as st  # للكاش (حفظ نتيجة التحميل بين إعادات التشغيل)

import database as db  # قاعدة البيانات
from config import (CONFIDENTIALITY_LEVELS, DEPARTMENTS, DISTRICTS, MAX_LOAD_ROWS,  # الثوابت المركزية
                    PRIORITIES, STATUS_DONE, STATUS_FIELD, STATUS_PENDING)

TARGET_ROWS = MAX_LOAD_ROWS or 200_000  # العدد الذي يظهر في المنصة (من config / .env). إن نقصت القاعدة عنه تُكمَّل ببيانات تجريبية
MAX_IMPORT_ROWS = 20_000  # أقصى عدد صفوف يُحلَّل في الاستيراد الواحد (حماية من الملفات الضخمة)
MAX_AI_CLASSIFY = 500     # أقصى عدد معاملات تُرسل للتصنيف الذكي (GPT) في المرة الواحدة — كل معاملة تكلّف مالاً


# ======================================================
# 1) البيانات التجريبية (تُستخدم فقط عندما تكون القاعدة صغيرة)
# ======================================================
def _synthetic(n: int = 100_000) -> pd.DataFrame:  # يولّد n معاملة تجريبية بنفس أعمدة القاعدة، مع اتجاه تحسّن حقيقي في نسبة الإنجا
    """يولّد n معاملة تجريبية بنفس أعمدة القاعدة، مع اتجاه تحسّن حقيقي في نسبة الإنجاز."""
    rng = np.random.default_rng(42)  # بذرة ثابتة = نفس الأرقام في كل تشغيل (نتائج قابلة للتكرار)
    today = np.datetime64(datetime.date.today())  # تاريخ اليوم بصيغة numpy
    idx = np.arange(1, n + 1)  # أرقام تسلسلية 1..n
    age = rng.integers(0, 300, n)  # عمر المعاملة بالأيام (0 = وصلت اليوم)
    priority = rng.choice(PRIORITIES, n, p=[0.45, 0.30, 0.18, 0.07])  # توزيع الأهمية (الأغلب عادي)
    # احتمال الإنجاز يرتفع كلما كانت المعاملة أحدث ← يُظهر اتجاه «تحسّن» في الأسابيع الأخيرة
    p_done = 0.35 + 0.30 * (1 - age / 300)
    is_done = rng.random(n) < p_done  # قرار عشوائي لكل معاملة: منجزة أم لا
    other = rng.choice([STATUS_PENDING, STATUS_FIELD], n, p=[0.6, 0.4])  # حالة غير المنجزة
    status = np.where(is_done, STATUS_DONE, other)  # الحالة النهائية
    sla = np.vectorize({"عادي": 7, "هام": 5, "عاجل": 2, "حرج للغاية": 1}.get)(priority)  # مهلة الإنجاز بالأيام
    delivery = today - age.astype("timedelta64[D]")  # تاريخ الاستلام
    expected = delivery + sla.astype("timedelta64[D]")  # التاريخ المتوقع للإنجاز = الاستلام + المهلة
    return pd.DataFrame({
        "رقم المعاملة": [f"TRX-{900000 + i}" for i in idx],
        "موضوع المعاملة": [f"بلاغ عمليات ميدانية وتشغيلية رقم {i}" for i in idx],
        "الحي": rng.choice(DISTRICTS, n),
        "نوع الجهة": rng.choice(["توجيه رسمي", "بلاغ مواطن"], n),
        "اسم الجهة": [f"قطاع الخدمة الميدانية ({i % 50 + 1})" for i in idx],
        "درجة الأهمية": priority,
        "السرية": rng.choice(list(CONFIDENTIALITY_LEVELS), n, p=[0.6, 0.3, 0.1]),  # نص عادي وليس category
        "القسم المكلف": rng.choice(DEPARTMENTS, n),
        "الحالة": status,
        "تاريخ التسليم": delivery.astype(str),
        "التاريخ المتوقع للإنجاز": expected.astype(str),
        "سبب عدم الإنجاز": np.where(is_done, "منجزة ومكتملة", "قيد المتابعة الميدانية"),
    })


# ======================================================
# 2) تجهيز الجدول للتحليل
# ======================================================
_CATEGORY_COLS = ["الحي", "القسم المكلف", "الحالة", "درجة الأهمية", "نوع الجهة", "اسم الجهة"]  # تقلّل الذاكرة
# ملاحظة: «السرية» تبقى نصاً عادياً عمداً؛ لأن security.visible_transactions يقارن قيمها بعد تحويلها لأرقام.


def _prepare(df: pd.DataFrame) -> pd.DataFrame:  # يضيف أعمدة التاريخ التي يحتاجها analytics.py ويضبط أنواع الأعمدة
    """يضيف أعمدة التاريخ التي يحتاجها analytics.py ويضبط أنواع الأعمدة."""
    df = df.copy()  # لا نعدّل الأصل
    if "السرية" not in df.columns:
        df["السرية"] = "سري للغاية"  # عمود ناقص = أعلى سرية (الأمان أولاً)
    df["السرية"] = df["السرية"].astype(str).replace({"nan": "سري للغاية", "None": "سري للغاية"})
    # تاريخ الاستلام = تاريخ التسليم المسجّل؛ errors=coerce يحوّل أي تاريخ تالف إلى فراغ بدل الانهيار
    df["تاريخ الاستلام"] = pd.to_datetime(df["تاريخ التسليم"], errors="coerce")
    df["تاريخ الإنجاز المتوقع"] = pd.to_datetime(df["التاريخ المتوقع للإنجاز"], errors="coerce")
    for col in _CATEGORY_COLS:
        if col in df.columns:
            df[col] = df[col].astype("category")  # نوع مضغوط: أسرع وأخف مع مئات الآلاف من الصفوف
    return df


# ======================================================
# 3) تحميل كل السجلات (مرة واحدة ثم من الذاكرة)
# ======================================================
@st.cache_resource(max_entries=2, show_spinner="جاري تحميل السجلات...")  # cache_resource لا ينسخ الجدول في كل مرة (أسرع بكثير)
def _load_cached(version: tuple, max_rows: int) -> pd.DataFrame:  # يحمّل المعاملات من القاعدة مع تخزين مؤقت
    """version = بصمة القاعدة؛ إذا تغيّرت (أُضيفت معاملة) يُعاد التحميل تلقائياً، وإلا نستخدم الذاكرة."""
    real = db.get_all_transactions()  # السجلات الحقيقية من القاعدة
    if real is None or real.empty:
        base = _synthetic(TARGET_ROWS)  # قاعدة فارغة ← بيانات تجريبية بالحجم المستهدف
    elif len(real) < TARGET_ROWS:
        # القاعدة أصغر من المستهدف: نكمّلها ببيانات تجريبية حتى نصل للعدد المطلوب (مثلاً 200 ألف)
        real = real.drop(columns=["id"], errors="ignore")
        for col in real.select_dtypes("category").columns:
            real[col] = real[col].astype(object)  # نفك التصنيف قبل الدمج لتفادي مشاكل الأنواع
        base = pd.concat([_synthetic(TARGET_ROWS - len(real)), real], ignore_index=True)
        base = base.drop_duplicates(subset=["رقم المعاملة"], keep="last")
    else:
        base = real.drop(columns=["id"], errors="ignore")  # القاعدة كافية: نعتمد عليها وحدها
    if max_rows and len(base) > max_rows:
        base = base.tail(max_rows)  # سقف الأداء: آخر N سجل فقط
    return _prepare(base).reset_index(drop=True)


def load_all_transactions() -> pd.DataFrame:  # كل السجلات قبل فلترة الصلاحيات
    """كل السجلات قبل فلترة الصلاحيات. لا تعرضها مباشرة — مرّرها عبر security.visible_transactions."""
    try:
        version = db.data_version()  # بصمة رخيصة (عدد السجلات + آخر رقم)
    except Exception:
        version = (0, 0)  # القاعدة غير متاحة: نكمل بالتجريبي
    return _load_cached(tuple(version), MAX_LOAD_ROWS)


# ======================================================
# 4) أدوات الاستيراد (قراءة الملفات والتحقق منها)
# ======================================================
_ALIASES = {  # كل اسم عمود محتمل (عربي/إنجليزي) ← الاسم الرسمي في المنصة
    "رقم المعاملة": ["رقم المعاملة", "رقم", "المعاملة", "trx", "trx_num", "id", "transaction id", "ref"],
    "موضوع المعاملة": ["موضوع المعاملة", "الموضوع", "الوصف", "وصف", "subject", "description", "title", "التفاصيل"],
    "الحي": ["الحي", "district", "المنطقة", "الموقع"],
    "القسم المكلف": ["القسم المكلف", "القسم", "الإدارة", "الادارة", "department", "dept"],
    "درجة الأهمية": ["درجة الأهمية", "الأهمية", "الاهمية", "الأولوية", "الاولوية", "priority"],
    "السرية": ["السرية", "درجة السرية", "التصنيف", "confidentiality", "classification"],
}
_ALIAS_LOOKUP = {a.lower(): official for official, names in _ALIASES.items() for a in names}  # بحث سريع


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:  # يوحّد أسماء الأعمدة المرفوعة (أي اسم مقبول ← الاسم الرسمي)
    """يوحّد أسماء الأعمدة المرفوعة (أي اسم مقبول ← الاسم الرسمي)."""
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower()  # نتجاهل الفراغات وحالة الأحرف
        if key in _ALIAS_LOOKUP and _ALIAS_LOOKUP[key] not in rename.values():
            rename[col] = _ALIAS_LOOKUP[key]
    return df.rename(columns=rename)


# كلمات تدل بوضوح على عمل بلدي، وكل مجموعة مرتبطة بالإدارة المناسبة
_DEPT_KEYWORDS = {
    "إدارة صيانة الطرق والإنارة": ["حفرة", "حفر", "إنارة", "انارة", "عمود", "طريق", "رصف", "أسفلت", "اسفلت", "إشارة", "جسر", "نفق"],
    "إدارة النظافة والبيئة": ["نظافة", "نفايات", "قمامة", "حاوية", "صرف", "مياه", "تجمع", "حشرات", "رش", "بيئة"],
    "إدارة التراخيص البلدية": ["ترخيص", "رخصة", "تراخيص", "لوحة", "محل", "نشاط تجاري", "بسطة", "مخالفة"],
    "إدارة الأراضي والأملاك": ["أرض", "ارض", "تعدي", "صك", "ملكية", "مخطط", "تسوير", "أملاك", "املاك"],
}
_MUNICIPAL_RE = re.compile("|".join(re.escape(w) for ws in _DEPT_KEYWORDS.values() for w in ws)
                           + "|بلدية|الأمانة|الامانة|حديقة|رصيف|سفلتة|مبنى|بناء")  # تعبير واحد يلتقط أي كلمة بلدية


def rule_municipal(text: str) -> bool:  # قاعدة سريعة ومجانية: هل يحتوي النص على كلمة بلدية واضحة؟
    """قاعدة سريعة ومجانية: هل يحتوي النص على كلمة بلدية واضحة؟ (تغني عن استدعاء الذكاء الاصطناعي غالباً)."""
    return bool(_MUNICIPAL_RE.search(str(text or "")))


def _guess_dept(text: str):  # يخمّن الإدارة من كلمات الموضوع؛ يرجع None إن لم يجد
    """يخمّن الإدارة من كلمات الموضوع؛ يرجع None إن لم يجد."""
    for dept, words in _DEPT_KEYWORDS.items():
        if any(w in text for w in words):
            return dept
    return None


def _guess_district(text: str):  # يبحث عن اسم حي معروف داخل الموضوع
    """يبحث عن اسم حي معروف داخل الموضوع."""
    for d in DISTRICTS:
        if d in text or d.replace("حي ", "") in text:
            return d
    return None


def validate_import(raw: pd.DataFrame, visible_levels, existing_ids: set) -> pd.DataFrame:  # يتحقق من كل صف ويضيف عمود «حالة التحقق»: صالحة / تحتاج مراجعة / مرفوضة، مع سبب
    """يتحقق من كل صف ويضيف عمود «حالة التحقق»: صالحة / تحتاج مراجعة / مرفوضة، مع سبب لكل صف."""
    rows, seen = [], set(existing_ids)  # seen = الأرقام الموجودة + ما مرّ في هذا الملف (لكشف التكرار)
    levels = set(visible_levels)        # السرية المسموح للمستخدم برفعها (لا يرفع أعلى من صلاحيته)
    for rec in raw.to_dict("records"):
        notes, status = [], "صالحة"  # نبدأ متفائلين ثم نخفّض الحالة عند أي ملاحظة
        subject = str(rec.get("موضوع المعاملة") or "").strip()
        if subject.lower() == "nan":
            subject = ""
        trx = str(rec.get("رقم المعاملة") or "").strip()
        if not trx or trx.lower() == "nan":  # لا رقم؟ نولّد رقماً فريداً
            trx = f"TRX-IMP-{uuid.uuid4().hex[:8].upper()}"
            notes.append("رقم مولّد تلقائياً")
        dept = str(rec.get("القسم المكلف") or "").strip()
        if dept not in DEPARTMENTS:
            guess = _guess_dept(subject)  # نحاول التخمين من نص الموضوع
            dept, status = (guess or DEPARTMENTS[0]), "تحتاج مراجعة"
            notes.append("القسم غير معروف" + (" (مُخمَّن)" if guess else " (افتراضي)"))
        district = str(rec.get("الحي") or "").strip()
        if district not in DISTRICTS:
            guess = _guess_district(subject)
            district, status = (guess or DISTRICTS[0]), "تحتاج مراجعة"
            notes.append("الحي غير معروف" + (" (مُخمَّن)" if guess else " (افتراضي)"))
        priority = str(rec.get("درجة الأهمية") or "").strip()
        if priority not in PRIORITIES:
            priority, status = "عادي", "تحتاج مراجعة"
            notes.append("الأهمية افتراضية")
        level = str(rec.get("السرية") or "عام").strip()
        if level not in CONFIDENTIALITY_LEVELS:
            level, status = "عام", "تحتاج مراجعة"  # غير معروف ← أقل مستوى ثم مراجعة
            notes.append("السرية غير معروفة")
        # ---- أسباب الرفض (تتغلب على أي حالة سابقة) ----
        if len(subject) < 5:
            status = "مرفوضة"
            notes.append("الموضوع قصير أو فارغ")
        if trx in seen:
            status = "مرفوضة"
            notes.append("رقم مكرر")
        if level not in levels:
            status = "مرفوضة"
            notes.append("سرية أعلى من صلاحيتك")
        seen.add(trx)
        out = {"رقم المعاملة": trx, "موضوع المعاملة": subject, "الحي": district, "القسم المكلف": dept,
               "درجة الأهمية": priority, "السرية": level, "المصدر": rec.get("المصدر", ""),
               "حالة التحقق": status, "ملاحظات التحقق": "، ".join(notes)}
        for hidden in ("_municipal", "_reason"):  # أعمدة يضعها استخراج الذكاء الاصطناعي من PDF
            if hidden in rec:
                out[hidden] = rec[hidden]
        rows.append(out)
    return pd.DataFrame(rows)


def apply_municipal_flags(clean: pd.DataFrame, classify_fn) -> pd.DataFrame:  # يضيف عمود «تخص البلدية» (نعم/لا/غير مصنف) بثلاث طبقات: ما استخرجه الذكاء ← قاع
    """يضيف عمود «تخص البلدية» (نعم/لا/غير مصنف) بثلاث طبقات: ما استخرجه الذكاء ← قاعدة الكلمات ← تصنيف GPT."""
    df = clean.copy()
    if df.empty:
        df["تخص البلدية"] = pd.Series(dtype=object)
        return df
    flag = pd.Series("غير مصنف", index=df.index, dtype=object)  # الافتراضي
    reason = pd.Series("", index=df.index, dtype=object)
    if "_municipal" not in df:
        df["_municipal"] = None  # لا قرار مسبق
    if "_reason" not in df:
        df["_reason"] = ""
    todo = []  # الصفوف التي تحتاج قراراً من GPT
    for ix, rec in df.iterrows():
        if rec["حالة التحقق"] == "مرفوضة":
            continue  # لا نصرف تكلفة على مرفوض
        pre = rec["_municipal"]
        if isinstance(pre, (bool, np.bool_)):  # الذكاء الاصطناعي حسم الأمر أثناء الاستخراج
            flag[ix], reason[ix] = ("نعم" if pre else "لا"), str(rec["_reason"] or "")
        elif rule_municipal(rec["موضوع المعاملة"]):  # كلمة بلدية واضحة
            flag[ix], reason[ix] = "نعم", "كلمة بلدية واضحة"
        else:
            todo.append(ix)
    todo_limited = todo[:MAX_AI_CLASSIFY]  # سقف التكلفة؛ الباقي يبقى «غير مصنف»
    if todo_limited:
        try:
            results = classify_fn([df.at[ix, "موضوع المعاملة"] for ix in todo_limited])
        except Exception:
            results = []  # تعذّر الاتصال: نترك «غير مصنف» بدل الانهيار
        for ix, res in zip(todo_limited, results):
            verdict, why = res
            flag[ix] = "نعم" if verdict is True else "لا" if verdict is False else "غير مصنف"
            reason[ix] = why or ""
    df["تخص البلدية"], df["_reason"] = flag, reason
    df["_municipal"] = flag.map({"نعم": True, "لا": False})
    return df


# ======================================================
# 5) حفظ التكليفات والتقارير الميدانية (ملفات JSON بسيطة)
# ======================================================
_ASSIGN_FILE = Path("field_assignments.json")  # ملف التكليفات
_REPORT_DIR = Path("field_reports")            # مجلد صور التقارير
_REPORT_INDEX = _REPORT_DIR / "index.json"     # فهرس التقارير


def _read_json(path: Path, default):  # قراءة آمنة: ملف مفقود أو تالف يرجع القيمة الافتراضية بدل إسقاط المنصة
    """قراءة آمنة: ملف مفقود أو تالف يرجع القيمة الافتراضية بدل إسقاط المنصة."""
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (ValueError, OSError):
        return default


def _write_json(path: Path, data) -> None:  # كتابة ذرّية: نكتب في ملف مؤقت ثم نستبدل الأصل، فلا يتلف الملف لو انقطع التشغيل
    """كتابة ذرّية: نكتب في ملف مؤقت ثم نستبدل الأصل، فلا يتلف الملف لو انقطع التشغيل في المنتصف."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def load_assignments() -> dict:  # كل التكليفات: {رقم المعاملة: {team, dept, note, by, at}} بترتيب زمني (الأقدم أ
    """كل التكليفات: {رقم المعاملة: {team, dept, note, by, at}} بترتيب زمني (الأقدم أولاً)."""
    data = _read_json(_ASSIGN_FILE, {})
    return data if isinstance(data, dict) else {}


def save_assignment(trx: str, team: int, dept: str, note: str, by: str) -> None:  # يحفظ تكليف فريق بمعاملة؛ إعادة التكليف تنقلها لآخر القائمة
    """يحفظ تكليف فريق بمعاملة؛ إعادة التكليف تنقلها لآخر القائمة."""
    data = load_assignments()
    data.pop(trx, None)  # حذف القديم ليعود المفتاح في النهاية (ترتيب زمني)
    data[trx] = {"team": int(team), "dept": dept, "note": (note or "").strip()[:300], "by": by,
                 "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    _write_json(_ASSIGN_FILE, data)


def save_field_report(data_bytes: bytes, ext: str, meta: dict) -> str:  # يحفظ صورة التقرير الميداني + بياناتها في الفهرس، ويرجع اسم الملف
    """يحفظ صورة التقرير الميداني + بياناتها في الفهرس، ويرجع اسم الملف."""
    ext = "png" if str(ext).lower() == "png" else "jpg"  # نسمح بصيغتين فقط (أمان)
    name = f"rep_{datetime.datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}.{ext}"  # اسم فريد
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (_REPORT_DIR / name).write_bytes(data_bytes)  # حفظ الصورة
    index = _read_json(_REPORT_INDEX, [])
    index.append({**meta, "file": name, "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")})
    _write_json(_REPORT_INDEX, index)
    return name


def load_field_reports() -> list:  # التقارير الميدانية، الأحدث أولاً
    """التقارير الميدانية، الأحدث أولاً."""
    index = _read_json(_REPORT_INDEX, [])
    return list(reversed(index)) if isinstance(index, list) else []


# ======================================================
# 6) مشاريع الأمانة + تقييمات رضا المستفيدين (ملفات JSON + مجلد صور)
# ======================================================
_PROJ_FILE = Path("projects.json")        # ملف المشاريع (منفّذة / قيد التنفيذ / مقترحة)
_PROJ_IMG_DIR = Path("project_images")    # مجلد صور المشاريع (الحقيقية والتصورات الذكية)
_RATING_FILE = Path("ratings.json")       # تقييمات المستفيدين {رقم المعاملة: {stars, at}}


def _demo_projects() -> list:  # أمثلة تجريبية موسومة demo=True حتى لا تُفهم أنها مشاريع حقيقية
    """أمثلة تجريبية موسومة demo=True حتى لا تُفهم أنها مشاريع حقيقية. يحذفها المدير بضغطة زر."""
    today = datetime.date.today()

    def d(days_ago: int) -> str:  # تاريخ نسبي بصيغة ISO
        return (today - datetime.timedelta(days=days_ago)).isoformat()

    rows = [  # الاسم، الحي، التصنيف، الميزانية، المصروف، بدأ قبل (يوم)، المدة المخططة، المدة الفعلية، الحالة، رضا، شكاوى قبل، بعد
        ("تطوير وتوسعة طريق رئيسي (نموذج)", "حي الصفا", "طرق", 12_000_000, 11_400_000, 330, 180, 195, "منفّذ", 82, 120, 45),
        ("مشروع تصريف مياه الأمطار (نموذج)", "حي النسيم", "تصريف مياه", 8_500_000, 9_900_000, 300, 150, 230, "منفّذ", 64, 210, 120),
        ("إنارة الشوارع بتقنية LED (نموذج)", "حي الروضة", "إنارة", 3_200_000, 3_000_000, 280, 120, 125, "منفّذ", 88, 90, 20),
        ("حديقة حي ومسار مشاة (نموذج)", "حي الشاطئ", "حدائق", 5_000_000, 5_200_000, 250, 100, 98, "منفّذ", 91, 30, 25),
        ("تأهيل الواجهة البحرية (نموذج)", "حي الشاطئ", "تجميل", 15_000_000, 9_000_000, 200, 330, None, "قيد التنفيذ", None, 60, None),
        ("سفلتة وإعادة تأهيل شوارع داخلية (نموذج)", "حي البساتين", "طرق", 6_800_000, 6_500_000, 180, 100, 105, "منفّذ", 77, 150, 70),
        ("مركز نقل نفايات ذكي (نموذج)", "حي أبحر الشمالية", "نظافة", 4_400_000, 2_100_000, 160, 120, None, "قيد التنفيذ", None, 95, None),
        ("تحسين تقاطع مروري مزدحم (نموذج)", "حي النزهة", "طرق", 2_900_000, 2_800_000, 340, 150, 180, "منفّذ", 70, 80, 55),
    ]
    out = []
    for name, dist, cat, bud, sp, start_ago, plen, alen, st_, sat, cb, ca in rows:
        start = today - datetime.timedelta(days=start_ago)  # تاريخ البدء
        out.append({"id": uuid.uuid4().hex[:8], "name": name, "district": dist, "category": cat, "budget": bud,
                    "spent": sp, "start": start.isoformat(),
                    "planned_end": (start + datetime.timedelta(days=plen)).isoformat(),
                    "actual_end": (start + datetime.timedelta(days=alen)).isoformat() if alen else None,
                    "status": st_, "satisfaction": sat, "complaints_before": cb, "complaints_after": ca,
                    "description": "مشروع تجريبي لعرض شكل الصفحة وطريقة حساب نسبة النجاح، ويُستبدل بمشاريع حقيقية.",
                    "images": [], "demo": True, "ai": None})
    return out


def load_projects() -> list:  # كل المشاريع
    """كل المشاريع. أول مرة (لا ملف) نكتب الأمثلة التجريبية الموسومة."""
    if not _PROJ_FILE.exists():
        _write_json(_PROJ_FILE, _demo_projects())
    data = _read_json(_PROJ_FILE, [])
    return data if isinstance(data, list) else []


def save_project(proj: dict) -> str:  # إضافة مشروع جديد أو تحديث موجود (حسب id)
    """إضافة مشروع جديد أو تحديث موجود (حسب id). يرجع id."""
    data = load_projects()
    proj.setdefault("id", uuid.uuid4().hex[:8])
    data = [p for p in data if p.get("id") != proj["id"]] + [proj]
    _write_json(_PROJ_FILE, data)
    return proj["id"]


def delete_projects(ids=None, demo_only: bool = False) -> int:  # يحذف مشاريع محددة أو كل التجريبية
    """يحذف مشاريع محددة أو كل التجريبية. يرجع عدد المحذوف."""
    data = load_projects()
    keep = [p for p in data if not ((demo_only and p.get("demo")) or (ids and p.get("id") in ids))]
    _write_json(_PROJ_FILE, keep)
    return len(data) - len(keep)


def save_project_image(data_bytes: bytes, ext: str = "jpg") -> str:  # يحفظ صورة مشروع (png/jpg فقط) ويرجع اسم الملف
    """يحفظ صورة مشروع (png/jpg فقط) ويرجع اسم الملف."""
    ext = "png" if str(ext).lower() == "png" else "jpg"
    name = f"prj_{datetime.datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}.{ext}"
    _PROJ_IMG_DIR.mkdir(parents=True, exist_ok=True)
    (_PROJ_IMG_DIR / name).write_bytes(data_bytes)
    return name


def project_image_path(name: str) -> Path:  # مسار صورة مشروع (اسم الملف فقط، لمنع الخروج من المجلد)
    """مسار صورة مشروع (اسم الملف فقط، لمنع الخروج من المجلد)."""
    return _PROJ_IMG_DIR / Path(name).name


def save_rating(trx: str, stars: int) -> None:  # يحفظ تقييم المستفيد (1-5 نجوم) لمعاملته المنجزة
    """يحفظ تقييم المستفيد (1-5 نجوم) لمعاملته المنجزة."""
    data = _read_json(_RATING_FILE, {})
    data[str(trx)] = {"stars": int(stars), "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    _write_json(_RATING_FILE, data)


def load_rating(trx: str):  # تقييم سابق لمعاملة (أو None)
    """تقييم سابق لمعاملة (أو None)."""
    return _read_json(_RATING_FILE, {}).get(str(trx))


# ---- نسخ ومراجعات المشاريع (Agile: كل تعديل يُسجَّل ويمكن الرجوع له) ----
_TRACKED = ("name", "district", "category", "description", "status", "budget", "spent", "start", "planned_end",
            "actual_end", "satisfaction", "complaints_before", "complaints_after", "approval", "review_note", "estimate")
_MAX_HISTORY = 20  # أقصى عدد نسخ محفوظة لكل مشروع


def save_project_versioned(new: dict, by: str, role: str, note: str = "") -> str:  # يحفظ المشروع ويضيف سجلاً: من عدّل ومتى وماذا تغيّر، مع لقطة من الحالة السابقة 
    """يحفظ المشروع ويضيف سجلاً: من عدّل ومتى وماذا تغيّر، مع لقطة من الحالة السابقة للرجوع إليها."""
    old = next((p for p in load_projects() if p.get("id") == new.get("id")), None)
    hist = list((old or {}).get("history", []))
    diff = {k: [str(old.get(k))[:80], str(new.get(k))[:80]] for k in _TRACKED if old and old.get(k) != new.get(k)}
    hist.append({"v": (hist[-1]["v"] + 1) if hist else 1, "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "by": by, "role": role, "note": (note or "")[:200] if old else (note or "إنشاء المشروع")[:200],
                 "changes": diff, "snap": {k: old.get(k) for k in _TRACKED} if old else None})
    new["history"] = hist[-_MAX_HISTORY:]
    return save_project(new)


def revert_project(pid: str, version: int, by: str, role: str) -> bool:  # يعيد المشروع إلى حالته قبل التعديل رقم version (ويسجّل ذلك كنسخة جديدة)
    """يعيد المشروع إلى حالته قبل التعديل رقم version (ويسجّل ذلك كنسخة جديدة)."""
    p = next((x for x in load_projects() if x.get("id") == pid), None)
    entry = next((h for h in (p or {}).get("history", []) if h.get("v") == version), None)
    if not p or not entry or not entry.get("snap"):
        return False
    save_project_versioned({**p, **entry["snap"]}, by, role, f"استرجاع الحالة قبل التعديل رقم {version}")
    return True


# ======================================================
# 7) التاريخ الهجري + ترقيم الصادر + بلاغات المشاكل (ملفات JSON)
# ======================================================
_OUT_FILE = Path("outgoing_counter.json")   # عدّاد رقم الصادر لكل سنة هجرية
_ISSUE_FILE = Path("issues.json")           # بلاغات المستخدمين عن مشاكل المنصة
HIJRI_MONTHS = ["محرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
                "رمضان", "شوال", "ذو القعدة", "ذو الحجة"]


def to_hijri(d: datetime.date):  # يحوّل تاريخاً ميلادياً إلى هجري (حساب جدولي تقريبي، قد يختلف يوماً عن أم القرى
    """يحوّل تاريخاً ميلادياً إلى هجري (حساب جدولي تقريبي، قد يختلف يوماً عن أم القرى). يرجع (سنة, شهر, يوم)."""
    jd = d.toordinal() + 1721425
    l = jd - 1948440 + 10632
    n = (l - 1) // 10631
    l = l - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    m = (24 * l) // 709
    return 30 * n + j - 30, m, l - (709 * m) // 24


def hijri_text(d: datetime.date) -> str:  # نص التاريخ الهجري: 8 جمادى الأولى 1448هـ (تقريبي)
    """نص التاريخ الهجري: 8 جمادى الأولى 1448هـ (تقريبي)."""
    y, m, day = to_hijri(d)
    return f"{day} {HIJRI_MONTHS[m - 1]} {y}هـ"


def next_outgoing_no() -> str:  # رقم صادر متسلسل لكل سنة هجرية، مثل: ص/1448/0007
    """رقم صادر متسلسل لكل سنة هجرية، مثل: ص/1448/0007."""
    year = str(to_hijri(datetime.date.today())[0])
    data = _read_json(_OUT_FILE, {})
    data[year] = int(data.get(year, 0)) + 1
    _write_json(_OUT_FILE, data)
    return f"ص/{year}/{data[year]:04d}"


def save_issue(category: str, text: str, by: str, role: str) -> None:  # يسجّل بلاغ مشكلة من مستخدم
    """يسجّل بلاغ مشكلة من مستخدم."""
    data = _read_json(_ISSUE_FILE, [])
    data.append({"category": category, "text": text.strip()[:1000], "by": by, "role": role,
                 "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "جديد"})
    _write_json(_ISSUE_FILE, data)


def load_issues() -> list:  # بلاغات المشاكل، الأحدث أولاً
    """بلاغات المشاكل، الأحدث أولاً."""
    data = _read_json(_ISSUE_FILE, [])
    return list(reversed(data)) if isinstance(data, list) else []


# ======================================================
# آراء المستخدمين + تذاكر الدعم/الخصوصية + تقدّم الأكاديمية
# ======================================================
_FB_FILE = Path("feedback.json")      # آراء المستخدمين
_TICKET_FILE = Path("tickets.json")   # تذاكر الدعم وطلبات الخصوصية
_ACAD_FILE = Path("academy.json")     # تقدّم التدريب لكل مستخدم


def _next_ref(prefix: str, items: list) -> str:  # رقم مرجعي متسلسل لكل سنة، مثل FB-2026-0007
    """رقم مرجعي متسلسل لكل سنة، مثل FB-2026-0007."""
    year = datetime.date.today().year
    used = [int(str(i.get("ref", "")).rsplit("-", 1)[-1]) for i in items
            if str(i.get("ref", "")).startswith(f"{prefix}-{year}-") and str(i["ref"]).rsplit("-", 1)[-1].isdigit()]
    return f"{prefix}-{year}-{(max(used) + 1) if used else 1:04d}"


def save_feedback(entry: dict) -> str:  # يحفظ رأياً ويُرجع رقمه المرجعي (للمتابعة لاحقاً)
    """يحفظ رأياً ويُرجع رقمه المرجعي (للمتابعة لاحقاً)."""
    items = _read_json(_FB_FILE, [])
    if not isinstance(items, list):
        items = []
    entry = dict(entry)
    entry["ref"] = _next_ref("FB", items)  # رقم الرأي
    entry["at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry["status"] = "جديد"
    entry["comment"] = str(entry.get("comment", "")).strip()[:1500]  # حدّ طول التعليق
    items.append(entry)
    _write_json(_FB_FILE, items)
    return entry["ref"]


def load_feedback() -> list:  # كل الآراء، الأحدث أولاً
    """كل الآراء، الأحدث أولاً."""
    items = _read_json(_FB_FILE, [])
    return list(reversed(items)) if isinstance(items, list) else []


def update_feedback(ref: str, status: str, note: str = "") -> bool:  # يغيّر حالة رأي (جديد / قيد الدراسة / نُفّذ / مغلق) مع ملاحظة المدير
    """يغيّر حالة رأي (جديد / قيد الدراسة / نُفّذ / مغلق) مع ملاحظة المدير."""
    items = _read_json(_FB_FILE, [])
    for it in items:
        if it.get("ref") == ref:
            it["status"], it["admin_note"] = status, note.strip()[:500]
            _write_json(_FB_FILE, items)
            return True
    return False


def find_feedback(ref: str):  # رأي برقمه المرجعي (للمتابعة)، أو None
    """رأي برقمه المرجعي (للمتابعة)، أو None."""
    ref = (ref or "").strip().upper()
    return next((i for i in _read_json(_FB_FILE, []) if str(i.get("ref", "")).upper() == ref), None)


def save_ticket(kind: str, subject: str, text: str, by: str, role: str, contact: str = "") -> str:  # تذكرة دعم أو طلب خصوصية
    """تذكرة دعم أو طلب خصوصية. kind: دعم | خصوصية."""
    items = _read_json(_TICKET_FILE, [])
    if not isinstance(items, list):
        items = []
    ref = _next_ref("SUP" if kind == "دعم" else "PRV", items)
    items.append({"ref": ref, "kind": kind, "subject": subject[:120], "text": text.strip()[:2000],
                  "by": by, "role": role, "contact": contact.strip()[:120],
                  "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "جديدة", "reply": ""})
    _write_json(_TICKET_FILE, items)
    return ref


def load_tickets() -> list:  # يقرأ كل تذاكر الدعم والخصوصية
    items = _read_json(_TICKET_FILE, [])
    return list(reversed(items)) if isinstance(items, list) else []


def find_ticket(ref: str):  # يبحث عن تذكرة برقمها المرجعي
    ref = (ref or "").strip().upper()
    return next((i for i in _read_json(_TICKET_FILE, []) if str(i.get("ref", "")).upper() == ref), None)


def update_ticket(ref: str, status: str, reply: str = "") -> bool:  # يغيّر حالة تذكرة ويضيف رد الإدارة
    items = _read_json(_TICKET_FILE, [])
    for it in items:
        if it.get("ref") == ref:
            it["status"], it["reply"] = status, reply.strip()[:800]
            _write_json(_TICKET_FILE, items)
            return True
    return False


def load_academy(user: str) -> dict:  # تقدّم مستخدم مسجّل: {track: {"lessons": [...], "score": int|None, "passed_at":
    """تقدّم مستخدم مسجّل: {track: {"lessons": [...], "score": int|None, "passed_at": str|None}}."""
    return _read_json(_ACAD_FILE, {}).get(user, {})


def save_academy(user: str, track: str, lessons: list, score=None) -> None:  # يحفظ تقدّم مستخدم في مركز التدريب (قديمة)
    data = _read_json(_ACAD_FILE, {})
    cur = data.setdefault(user, {}).setdefault(track, {"lessons": [], "score": None, "passed_at": None})
    cur["lessons"] = sorted(set(lessons))
    if score is not None:
        cur["score"] = int(score)
        if score >= 70 and not cur.get("passed_at"):
            cur["passed_at"] = datetime.date.today().isoformat()
    _write_json(_ACAD_FILE, data)