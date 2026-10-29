"""طبقة قاعدة البيانات (SQLite) — مهيّأة لمئات الآلاف إلى مليون سجل.

ما الجديد:
  1) فهارس على الأعمدة المستخدمة في البحث والفلترة، وإعدادات WAL لسرعة القراءة والكتابة.
  2) get_all_transactions() مخزّنة مؤقتاً حسب «نسخة البيانات»، فلا تُقرأ القاعدة كلها عند كل نقرة.
  3) دوال تجميع واستعلام بصفحات تعمل داخل القاعدة (summary_stats / query_transactions).
  4) توليد بيانات تجريبية كبيرة بأمر واحد:   python database.py --seed 1000000
  5) add_new_transaction (الاسم الذي تستدعيه الواجهة) + add_transaction للتوافق مع الملفات القديمة.

أوامر مفيدة (من مجلد المشروع، والبيئة venv مفعّلة):
  python database.py --seed 1000000    # يستبدل البيانات التجريبية فقط (TRX-JED-*) ولا يمسّ معاملاتك الحقيقية
  python database.py --stats           # يعرض عدد السجلات والفهارس
"""
import datetime
import os
import sqlite3
import sys
import time
from contextlib import contextmanager

import numpy as np
import pandas as pd

from config import (CONFIDENTIALITY_LEVELS, DEPARTMENTS as CFG_DEPARTMENTS,
                    DISTRICT_COORDS, DISTRICTS, PRIORITIES, STATUS_DONE, STATUSES)

try:
    import streamlit as st
    _cache = st.cache_data
except Exception:  # للتشغيل من سطر الأوامر بدون Streamlit
    def _cache(**_kw):  # بديل مؤقت للتخزين عند غياب streamlit
        return lambda f: f

DB_FILE = os.environ.get(
    "JEDDAH_DB_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "correspondence.db"))
DEMO_PREFIX = "TRX-JED-"

# ---- ثوابت قديمة تستخدمها ملفات أخرى (تُركت كما هي للتوافق) ----
DISTRICTS_GIS = {
    "حي الصفا": (21.5786, 39.2023), "حي أبحر الشمالية": (21.7583, 39.1350),
    "حي الشاطئ / الكورنيش": (21.5644, 39.1102), "حي الحمراء": (21.5233, 39.1601),
    "حي الجامعة": (21.4921, 39.2312), "حي الحمدانية": (21.7850, 39.2150),
    "حي النسيم": (21.5120, 39.2210), "حي البلد التاريخي": (21.4858, 39.1878),
    "حي الروضة": (21.5601, 39.1550), "حي المروة": (21.6021, 39.2110),
}
DEPARTMENTS = [
    "إدارة صيانة الطرق والجسور", "إدارة التراخيص والبناء", "إدارة النظافة والبيئة",
    "إدارة الأراضي والأملاك", "بلدية الصفا الفرعية", "بلدية أبحر الفرعية",
    "قسم المعلومات والحاسب الآلي", "إدارة الرقابة والسلامة الميدانية",
]
SUBJECT_TEMPLATES = [
    "بلاغ عن هبوط آسفلتي وتجمع مياه أمطار في شارع رئيسي",
    "طلب ترخيص بناء برج سكني وتجاري جديد",
    "شكوى من مخلفات بناء وتلوث بصري في قسيمة مجاورة",
    "معاملة تعديل منسوب أرض وتدقيق ملكية عقارية",
    "طلب صيانة وإعادة إنارة الشوارع الداخلية",
    "إزالة صبات خرسانية وعوائق مشاة أمام محلات تجارية",
    "بلاغ طارئ عن انسداد مصبات السيول والكورنيش",
    "طلب تصريح إشغال رصيف وفعالية موسمية",
]
SENDER_TYPES = ["توجيه رسمي", "توجيه خاص", "بلاغ مواطن"]
CONFIDENTIALITY_LIST = list(CONFIDENTIALITY_LEVELS)

# اسم العمود في القاعدة -> الاسم المعروض في المنصة
COLUMN_MAP = {
    "trx_num": "رقم المعاملة", "subject": "موضوع المعاملة", "district": "الحي",
    "latitude": "lat", "longitude": "lon", "sender_type": "نوع الجهة", "sender_name": "اسم الجهة",
    "priority": "درجة الأهمية", "confidentiality": "السرية", "dept": "القسم المكلف",
    "status": "الحالة", "delivery_date": "تاريخ التسليم", "expected_date": "التاريخ المتوقع للإنجاز",
    "delay_reason": "سبب عدم الإنجاز", "risk_score": "مؤشر الخطورة",
}
_DB_COLS = list(COLUMN_MAP)
_CATEGORY_COLS = ["الحي", "نوع الجهة", "درجة الأهمية", "القسم المكلف", "الحالة", "سبب عدم الإنجاز", "اسم الجهة"]

_INDEXES = {
    "idx_trx_status": "status", "idx_trx_district": "district", "idx_trx_dept": "dept",
    "idx_trx_priority": "priority", "idx_trx_delivery": "delivery_date",
    "idx_trx_conf_status": "confidentiality, status",
    "idx_trx_agg": "confidentiality, status, priority, dept",  # فهرس يغطي استعلام الإحصائيات
}


@contextmanager
def _conn():  # يفتح اتصال SQLite بوضع WAL للأداء
    conn = sqlite3.connect(DB_FILE, timeout=30)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-65536")  # 64MB
        conn.execute("PRAGMA temp_store=MEMORY")
        yield conn
        conn.commit()
    finally:
        conn.close()


def _create_indexes(conn) -> None:  # ينشئ فهارس القاعدة لتسريع البحث
    for name, cols in _INDEXES.items():
        conn.execute(f"CREATE INDEX IF NOT EXISTS {name} ON transactions({cols})")


# ======================================================
# التهيئة
# ======================================================
def _ensure_schema() -> bool:  # ينشئ الجدول والفهارس إن لم تكن موجودة
    """ينشئ الجدول والفهارس إن لم تكن موجودة. يُرجع True إذا كان الجدول فارغاً."""
    with _conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trx_num TEXT UNIQUE,
                subject TEXT, district TEXT, latitude REAL, longitude REAL,
                sender_type TEXT, sender_name TEXT, priority TEXT, confidentiality TEXT,
                dept TEXT, status TEXT, delivery_date TEXT, expected_date TEXT,
                delay_reason TEXT, risk_score REAL
            )''')
        _create_indexes(conn)
        return conn.execute("SELECT 1 FROM transactions LIMIT 1").fetchone() is None


def init_db() -> None:  # يهيّئ القاعدة والجداول عند بدء التشغيل
    if _ensure_schema():  # بيانات صغيرة للتجربة عند أول تشغيل فقط؛ لا نحذف شيئاً من بيانات موجودة
        seed_demo(2500, replace_demo=False)


# ======================================================
# التوليد التجريبي (حتى ملايين السجلات)
# ======================================================
def seed_demo(n: int = 1_000_000, replace_demo: bool = True, chunk: int = 100_000, say=print) -> int:  # يولّد n معاملة تجريبية بسرعة
    """يولّد n معاملة تجريبية بسرعة. replace_demo=True يحذف المعاملات التجريبية القديمة (TRX-JED-*) فقط."""
    t0 = time.time()
    rng = np.random.default_rng(42)
    today = np.datetime64(datetime.date.today())
    coords = np.array([DISTRICT_COORDS[d] for d in DISTRICTS])
    sender_names = np.array([f"قطاع الخدمة الميدانية ({i})" for i in range(1, 51)])
    reasons = np.array(["تأخر استيفاء الوثائق الهندسية من المكتب الاستشاري", "نقص المعدات الثقيلة في موقع الميدان",
                        "تداخل الاختصاص مع هيئة الكهرماء والاتصالات", "قيد المراجعة في جدول المساءلة الإدارية"])
    sla_days = {"عادي": 7, "هام": 5, "عاجل": 2, "حرج للغاية": 1}

    _ensure_schema()
    with _conn() as conn:
        if replace_demo:
            conn.execute("DELETE FROM transactions WHERE trx_num LIKE ?", (DEMO_PREFIX + "%",))
        for name in _INDEXES:  # الإدراج أسرع بدون فهارس، ثم نعيد بناءها
            conn.execute(f"DROP INDEX IF EXISTS {name}")
        start = (conn.execute("SELECT COALESCE(MAX(id), 0) FROM transactions").fetchone()[0]) + 1

        done = 0
        while done < n:
            m = min(chunk, n - done)
            d_idx = rng.integers(0, len(DISTRICTS), m)
            lat = coords[d_idx, 0] + rng.uniform(-0.01, 0.01, m)
            lon = coords[d_idx, 1] + rng.uniform(-0.01, 0.01, m)
            priority = rng.choice(PRIORITIES, m, p=[0.45, 0.30, 0.18, 0.07])
            conf = rng.choice(CONFIDENTIALITY_LIST, m, p=[0.6, 0.3, 0.1])
            status = rng.choice(STATUSES, m, p=[0.60, 0.25, 0.15])
            dept = rng.choice(CFG_DEPARTMENTS, m)
            ages = rng.integers(0, 300, m)
            delivery = today - ages.astype("timedelta64[D]")
            exp_days = np.vectorize(sla_days.get)(priority).astype("timedelta64[D]")
            expected = delivery + exp_days
            delay = np.where(status == STATUS_DONE, "تم الإنجاز طبقاً لمعايير SLA", rng.choice(reasons, m))
            subj_idx = rng.integers(0, len(SUBJECT_TEMPLATES), m)
            rows = zip(
                (f"{DEMO_PREFIX}{done + i + start:07d}" for i in range(m)),
                (f"{SUBJECT_TEMPLATES[j]} — {DISTRICTS[k]}" for j, k in zip(subj_idx, d_idx)),
                (DISTRICTS[k] for k in d_idx), lat.round(5).tolist(), lon.round(5).tolist(),
                rng.choice(SENDER_TYPES, m).tolist(), sender_names[rng.integers(0, 50, m)].tolist(),
                priority.tolist(), conf.tolist(), dept.tolist(), status.tolist(),
                delivery.astype(str).tolist(), expected.astype(str).tolist(), delay.tolist(),
                rng.uniform(0.1, 0.99, m).round(2).tolist())
            conn.executemany(
                "INSERT INTO transactions (trx_num, subject, district, latitude, longitude, sender_type, "
                "sender_name, priority, confidentiality, dept, status, delivery_date, expected_date, "
                "delay_reason, risk_score) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            done += m
            say(f"  أُدرج {done:,} / {n:,}")
        say("  بناء الفهارس ...")
        _create_indexes(conn)
    say(f"تم توليد {n:,} سجل في {time.time() - t0:.1f} ثانية.")
    return n


# ======================================================
# القراءة
# ======================================================
def data_version() -> tuple:  # بصمة رخيصة للبيانات: عند إضافة سجل تتغير فيُعاد التحميل تلقائياً
    """بصمة رخيصة للبيانات: عند إضافة سجل تتغير فيُعاد التحميل تلقائياً."""
    with _conn() as conn:
        count, max_id = conn.execute("SELECT COUNT(*), COALESCE(MAX(id), 0) FROM transactions").fetchone()
        edits = conn.execute("PRAGMA user_version").fetchone()[0]  # عدّاد التعديلات (يرتفع عند تغيير حالة معاملة)
        return (count, max_id, edits)


def _shape(df: pd.DataFrame) -> pd.DataFrame:  # يعيد تسمية الأعمدة وتهيئة الأنواع بشكل موحّد
    df = df.rename(columns=COLUMN_MAP)
    for col in _CATEGORY_COLS:
        if col in df.columns:
            df[col] = df[col].astype("category")  # يقلّل الذاكرة كثيراً مع ملايين الصفوف
    return df


def _max_rows() -> int:  # سقف اختياري لعدد السجلات المحمّلة للواجهة (آخر N سجل)
    """سقف اختياري لعدد السجلات المحمّلة للواجهة (آخر N سجل). ضعه في .env:  MAX_LOAD_ROWS=250000
    0 أو غير موجود = تحميل الكل."""
    from config import MAX_LOAD_ROWS  # المصدر الوحيد للرقم هو config.py (الذي يقرأ .env)
    return max(0, int(MAX_LOAD_ROWS))


@_cache(ttl=900, max_entries=2, show_spinner="جاري تحميل السجلات...")
def _load_cached(version: tuple, max_rows: int) -> pd.DataFrame:  # يحمّل المعاملات من القاعدة مع تخزين مؤقت
    cols = f"id, {', '.join(_DB_COLS)}"
    sql = (f"SELECT {cols} FROM transactions ORDER BY id DESC LIMIT {int(max_rows)}" if max_rows
           else f"SELECT {cols} FROM transactions")
    parts = []
    with _conn() as conn:  # قراءة على دفعات + تحويل مضغوط لكل دفعة = ذروة ذاكرة أقل
        for chunk in pd.read_sql_query(sql, conn, chunksize=200_000):
            parts.append(_shape(chunk))
    if not parts:
        return pd.DataFrame(columns=["id", *COLUMN_MAP.values()])
    df = pd.concat(parts, ignore_index=True)
    for col in _CATEGORY_COLS:  # توحيد التصنيفات بعد الدمج
        if col in df.columns:
            df[col] = df[col].astype("category")
    return df.sort_values("id").reset_index(drop=True) if max_rows else df


def get_all_transactions() -> pd.DataFrame:  # كل السجلات (أو آخر MAX_LOAD_ROWS) مخزّنة حسب نسخة البيانات
    """كل السجلات (أو آخر MAX_LOAD_ROWS) مخزّنة حسب نسخة البيانات.
    لا تعرضها للمستخدم قبل visible_transactions."""
    try:
        return _load_cached(data_version(), _max_rows())
    except sqlite3.Error:
        return pd.DataFrame()


def load_enterprise_transactions() -> pd.DataFrame:  # للتوافق مع الملفات القديمة
    """للتوافق مع الملفات القديمة."""
    return get_all_transactions().tail(100_000)


def count_transactions() -> int:  # عدد المعاملات في القاعدة
    return int(data_version()[0])


def _levels_clause(levels):  # يجهّز شرط SQL لمستويات السرية المسموحة
    levels = list(levels or [])
    return ",".join("?" * len(levels)), levels


@_cache(ttl=900, max_entries=2)
def _grouped_counts(version: tuple) -> list:  # تمريرة واحدة على الجدول: (سرية، حالة، أهمية، قسم، عدد)
    """تمريرة واحدة على الجدول: (سرية، حالة، أهمية، قسم، عدد). النتيجة صغيرة جداً."""
    with _conn() as conn:
        return conn.execute(
            "SELECT confidentiality, status, priority, dept, COUNT(*) FROM transactions "
            "GROUP BY confidentiality, status, priority, dept").fetchall()


def summary_stats(levels) -> dict:  # إحصائيات داخل القاعدة (بدون تحميل السجلات) ضمن مستويات السرية المسموحة فقط
    """إحصائيات داخل القاعدة (بدون تحميل السجلات) ضمن مستويات السرية المسموحة فقط."""
    allowed = set(levels or [])
    out = {"total": 0, "done": 0, "by_status": {}, "by_priority": {}, "by_department": {}}
    for conf, status, priority, dept, n in _grouped_counts(data_version()):
        if conf not in allowed:  # مستوى غير مسموح أو غير معروف = يُستبعد
            continue
        out["total"] += n
        for key, val in (("by_status", status), ("by_priority", priority), ("by_department", dept)):
            out[key][val] = out[key].get(val, 0) + n
    out["done"] = out["by_status"].get(STATUS_DONE, 0)
    return out


def _like_escape(text: str) -> str:  # يهرّب رموز LIKE لمنع تلاعب البحث
    return text.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


def query_transactions(levels, text: str = "", district: str = "", priority: str = "", status: str = "",
                       limit: int = 50, offset: int = 0) -> pd.DataFrame:  # بحث بصفحات داخل القاعدة (الفلترة بالصلاحية تتم هنا في SQL)
    """بحث بصفحات داخل القاعدة (الفلترة بالصلاحية تتم هنا في SQL). limit حتى 1000."""
    marks, params = _levels_clause(levels)
    if not params:
        return pd.DataFrame()
    where, args = [f"confidentiality IN ({marks})"], list(params)
    if text.strip():
        like = f"%{_like_escape(text.strip())}%"
        where.append("(trx_num LIKE ? ESCAPE '\\' OR subject LIKE ? ESCAPE '\\')")
        args += [like, like]
    for col, val in (("district", district), ("priority", priority), ("status", status)):
        if val:
            where.append(f"{col} = ?")
            args.append(val)
    sql = (f"SELECT id, {', '.join(_DB_COLS)} FROM transactions WHERE {' AND '.join(where)} "
           "ORDER BY id DESC LIMIT ? OFFSET ?")
    args += [max(1, min(int(limit), 1000)), max(0, int(offset))]
    with _conn() as conn:
        return _shape(pd.read_sql_query(sql, conn, params=args))


# ======================================================
# الكتابة
# ======================================================
def _pick(d: dict, *keys, default=None):  # يختار أول قيمة غير فارغة من عدة مفاتيح
    for k in keys:
        if d.get(k) not in (None, ""):
            return d[k]
    return default


def add_new_transaction(data: dict) -> None:  # يقبل مفاتيح الواجهة الحالية والقديمة (تاريخ التسجيل / تاريخ التسليم
    """يقبل مفاتيح الواجهة الحالية والقديمة (تاريخ التسجيل / تاريخ التسليم ... إلخ)."""
    district = data.get("الحي") or DISTRICTS[0]
    lat, lon = DISTRICT_COORDS.get(district) or DISTRICTS_GIS.get(district, (21.5786, 39.2023))
    lat += float(np.random.uniform(-0.004, 0.004))
    lon += float(np.random.uniform(-0.004, 0.004))
    with _conn() as conn:
        conn.execute(
            "INSERT INTO transactions (trx_num, subject, district, latitude, longitude, sender_type, "
            "sender_name, priority, confidentiality, dept, status, delivery_date, expected_date, "
            "delay_reason, risk_score) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (data.get("رقم المعاملة"), data.get("موضوع المعاملة"), district, lat, lon,
             data.get("نوع الجهة"), data.get("اسم الجهة"), data.get("درجة الأهمية"),
             data.get("السرية") or "عام", data.get("القسم المكلف"), data.get("الحالة") or "غير منجزة",
             _pick(data, "تاريخ التسليم", "تاريخ التسجيل"),
             _pick(data, "التاريخ المتوقع للإنجاز", "تاريخ الإغلاق المتوقع"),
             _pick(data, "سبب عدم الإنجاز", "سبب عدم الإغلاق"), 0.5))


add_transaction = add_new_transaction  # الاسم القديم


def update_transaction_status(trx_num: str, new_status: str) -> int:  # يغيّر حالة معاملة واحدة ويرجع عدد الصفوف المتأثرة (0 = المعاملة غير موجودة في 
    """يغيّر حالة معاملة واحدة ويرجع عدد الصفوف المتأثرة (0 = المعاملة غير موجودة في القاعدة)."""
    if new_status not in STATUSES:  # لا نقبل حالة خارج القائمة المعتمدة
        raise ValueError("حالة غير معتمدة")
    with _conn() as conn:
        cur = conn.execute("UPDATE transactions SET status = ? WHERE trx_num = ?", (new_status, str(trx_num)))
        if cur.rowcount:  # نرفع عدّاد التعديلات ليُعاد تحميل الكاش تلقائياً
            ver = conn.execute("PRAGMA user_version").fetchone()[0]
            conn.execute(f"PRAGMA user_version = {int(ver) + 1}")
        return cur.rowcount


# ======================================================
# سطر الأوامر
# ======================================================
if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--seed"]:
        count = int(args[1]) if len(args) > 1 else 1_000_000
        init_db()
        seed_demo(count)
    elif args[:1] == ["--stats"]:
        init_db()
        with _conn() as c:
            print("السجلات:", c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0])
            print("الفهارس:", [r[0] for r in c.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")])
    else:
        print(__doc__)