"""محرّك استعلام الجدول (بلا Streamlit) — بحث متعدد القيم + قيم يدوية + نطاقات تاريخ، ويعمل على مئات الآلاف من الصفوف.

وظيفة هذا الملف: منطق الاستعلام فقط (على طريقة لوحات المطار: كل خانة تقبل الاختيار أو البحث أو كتابة أي قيمة بنفسك).
القواعد:
  • عدة قيم في الخانة الواحدة = «أو». وعدة خانات = «و».
  • القوائم المحدودة (الحي، القسم، الحالة...): تطابق تام إن وُجد، وإلا بحث جزئي في أسماء الخيارات (مثلاً «صفا» تجلب «حي الصفا»).
  • النصوص الحرة (رقم المعاملة، الموضوع): بحث جزئي بلا حساسية لحالة الأحرف.
  • النتيجة مصفوفة مواضع مرتّبة (positions) بدل جدول منسوخ؛ فلا تُنسخ مئات الآلاف من الصفوف في الذاكرة.
"""
from __future__ import annotations

import datetime as _dt

import numpy as np
import pandas as pd

MAX_TERMS = 25                                   # أقصى عدد قيم في الخانة الواحدة (حماية من الإدخال المفرط)
PRIORITY_RANK = {"حرج للغاية": 0, "عاجل": 1, "هام": 2, "عادي": 3}   # الأصغر = الأخطر
ORDERS = ["الأعلى أهمية", "الأحدث استلاماً", "الأقرب موعداً", "الأقدم استلاماً"]

# الخانة في الاستعلام ← (عمود البيانات، نوعها): choice = قائمة محدودة، text = نص حر
FIELDS = {
    "trx": ("رقم المعاملة", "text"),
    "subject": ("موضوع المعاملة", "text"),
    "district": ("الحي", "choice"),
    "dept": ("القسم المكلف", "choice"),
    "priority": ("درجة الأهمية", "choice"),
    "status": ("الحالة", "choice"),
    "level": ("السرية", "choice"),
    "sender": ("نوع الجهة", "choice"),
}


def clean_terms(values) -> list:  # ينظّف قيم الخانة: يحذف الفراغ والمكرر (بلا حساسية للحالة) ويضع سقفاً لعددها
    out, seen = [], set()
    for v in (values or []):
        t = str(v).strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out[:MAX_TERMS]


def match_vocab(vocab, terms) -> list:  # يحوّل ما كتبه المستخدم إلى قيم فعلية من القائمة: تطابق تام أولاً ثم احتواء جزئي
    pairs = [(v, str(v).lower()) for v in vocab]
    keep = []
    for t in clean_terms(terms):
        tl = t.lower()
        exact = [v for v, low in pairs if low == tl]
        keep += exact or [v for v, low in pairs if tl in low]
    return keep


def _vocab_of(s: pd.Series, vocab=None) -> list:  # القيم الممكنة للعمود (التصنيفات إن وُجدت وإلا القيم الفريدة)
    if vocab is not None:
        return list(vocab)
    if isinstance(s.dtype, pd.CategoricalDtype):
        return list(s.cat.categories)
    return list(pd.unique(s.dropna()))


def choice_mask(s: pd.Series, terms, vocab=None) -> np.ndarray:  # قناع منطقي لعمود «قائمة محدودة»
    keep = match_vocab(_vocab_of(s, vocab), terms)
    if not keep:
        return np.zeros(len(s), dtype=bool)
    return s.isin(keep).to_numpy()


def text_mask(s: pd.Series, terms) -> np.ndarray:  # قناع منطقي لعمود نص حر: أي قيمة من القيم تكفي (بحث جزئي)
    base = s if s.dtype == object else s.astype(str)
    out = np.zeros(len(s), dtype=bool)
    for t in clean_terms(terms):
        out |= base.str.contains(t, case=False, regex=False, na=False).to_numpy()
    return out


def date_mask(s: pd.Series, start=None, end=None) -> np.ndarray:  # قناع نطاق تاريخ (أحد الطرفين اختياري)
    m = np.ones(len(s), dtype=bool)
    if start:
        m &= (s >= pd.Timestamp(start)).to_numpy()
    if end:
        m &= (s <= pd.Timestamp(end)).to_numpy()
    return m


def filter_mask(df: pd.DataFrame, q: dict, vocabs: dict | None = None, done_label: str = "منجزة") -> np.ndarray:
    """قناع منطقي واحد لكل شروط الاستعلام q (مفاتيحه: trx, subject, district, dept, priority, status, level, sender،
    recv_from, recv_to, due_from, due_to, overdue). الخانات الفارغة تُتجاهل."""
    vocabs = vocabs or {}
    m = np.ones(len(df), dtype=bool)
    for key, (col, kind) in FIELDS.items():
        terms = clean_terms(q.get(key))
        if not terms or col not in df.columns:
            continue
        m &= text_mask(df[col], terms) if kind == "text" else choice_mask(df[col], terms, vocabs.get(key))
        if not m.any():
            return m
    if "تاريخ الاستلام" in df.columns and (q.get("recv_from") or q.get("recv_to")):
        m &= date_mask(df["تاريخ الاستلام"], q.get("recv_from"), q.get("recv_to"))
    if "تاريخ الإنجاز المتوقع" in df.columns and (q.get("due_from") or q.get("due_to")):
        m &= date_mask(df["تاريخ الإنجاز المتوقع"], q.get("due_from"), q.get("due_to"))
    if q.get("overdue") and "تاريخ الإنجاز المتوقع" in df.columns:
        today = pd.Timestamp.today().normalize()
        m &= ((df["الحالة"] != done_label) & (df["تاريخ الإنجاز المتوقع"] < today)).to_numpy()
    return m


def _dates_i8(s: pd.Series, missing_last: bool = True) -> np.ndarray:  # تواريخ كأعداد صحيحة للفرز (الفراغ يذهب للنهاية)
    a = s.to_numpy(dtype="datetime64[ns]").astype("int64")
    bad = a == np.iinfo("int64").min
    if bad.any():
        a = a.copy()
        a[bad] = np.iinfo("int64").max if missing_last else np.iinfo("int64").min + 1
    return a


def _priority_rank(s: pd.Series) -> np.ndarray:  # رتبة الأهمية لكل صف (0 = الأخطر) بسرعة عبر رموز التصنيف
    if isinstance(s.dtype, pd.CategoricalDtype):
        lut = np.array([PRIORITY_RANK.get(str(c), 9) for c in s.cat.categories] or [9])
        codes = s.cat.codes.to_numpy()
        return np.where(codes < 0, 9, lut[np.clip(codes, 0, None)])
    return s.astype(str).map(PRIORITY_RANK).fillna(9).to_numpy()


def query_positions(df: pd.DataFrame, q: dict, order: str = ORDERS[0], vocabs: dict | None = None,
                    done_label: str = "منجزة") -> np.ndarray:
    """مواضع الصفوف المطابقة (iloc) مرتّبة حسب order. لا تنسخ الجدول؛ استعمل df.iloc[pos[a:b]] لعرض صفحة."""
    pos = np.flatnonzero(filter_mask(df, q, vocabs, done_label))
    if len(pos) <= 1:
        return pos
    if order == "الأحدث استلاماً" and "تاريخ الاستلام" in df.columns:
        key = _dates_i8(df["تاريخ الاستلام"], missing_last=False)[pos]
        return pos[np.argsort(-key, kind="stable")]
    if order == "الأقدم استلاماً" and "تاريخ الاستلام" in df.columns:
        key = _dates_i8(df["تاريخ الاستلام"])[pos]
        return pos[np.argsort(key, kind="stable")]
    if order == "الأقرب موعداً" and "تاريخ الإنجاز المتوقع" in df.columns:
        key = _dates_i8(df["تاريخ الإنجاز المتوقع"])[pos]
        return pos[np.argsort(key, kind="stable")]
    rank = _priority_rank(df["درجة الأهمية"])[pos]  # الافتراضي: الأعلى أهمية ثم الأقرب موعداً
    due = _dates_i8(df["تاريخ الإنجاز المتوقع"])[pos] if "تاريخ الإنجاز المتوقع" in df.columns else np.zeros(len(pos), "int64")
    return pos[np.lexsort((due, rank))]


def describe_query(q: dict) -> str:  # وصف مقروء للاستعلام الحالي (يظهر فوق النتائج حتى يفهم المستخدم ما طُبّق)
    names = {"trx": "الرقم", "subject": "الموضوع", "district": "الحي", "dept": "القسم", "priority": "الأهمية",
             "status": "الحالة", "level": "السرية", "sender": "الجهة"}
    parts = [f"{names[k]}: {' أو '.join(clean_terms(q.get(k)))}" for k in names if clean_terms(q.get(k))]
    if q.get("recv_from") or q.get("recv_to"):
        parts.append(f"الاستلام: {_fmt(q.get('recv_from')) or '…'} → {_fmt(q.get('recv_to')) or '…'}")
    if q.get("due_from") or q.get("due_to"):
        parts.append(f"الموعد: {_fmt(q.get('due_from')) or '…'} → {_fmt(q.get('due_to')) or '…'}")
    if q.get("overdue"):
        parts.append("المتأخرة فقط")
    return " — ".join(parts)


def _fmt(d) -> str:  # تاريخ بصيغة YYYY-MM-DD (أو فراغ)
    if isinstance(d, (_dt.date, _dt.datetime, pd.Timestamp)):
        return d.strftime("%Y-%m-%d")
    return str(d or "")


def signature(q: dict, order: str) -> tuple:  # بصمة ثابتة للاستعلام (لتخزين النتيجة مؤقتاً وتصفير الصفحة عند تغييره)
    items = []
    for k in sorted(q):
        v = q[k]
        if isinstance(v, (list, tuple, set)):
            v = tuple(clean_terms(v))
        elif isinstance(v, (_dt.date, _dt.datetime, pd.Timestamp)):
            v = _fmt(v)
        items.append((k, v))
    return (tuple(items), order)
