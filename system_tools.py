"""أدوات النظام (منطق فقط، بلا واجهة): نسخ احتياطي تلقائي، قراءة سجل التدقيق، وفحص تحديثات المكتبات.

الواجهة التي تستخدمها هي render_system في views.py.
"""
import datetime
import importlib.metadata as md
import json
import re
import sqlite3
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from database import DB_FILE  # مسار قاعدة البيانات

BACKUP_DIR = Path("backups")  # مجلد النسخ الاحتياطية
KEEP_BACKUPS = 10             # نحتفظ بآخر 10 نسخ ونحذف الأقدم
_DATA_FILES = ["projects.json", "issues.json", "field_assignments.json", "ratings.json",
               "outgoing_counter.json", "audit.log"]  # ملفات البيانات (لا نضيف .env حتى لا تتسرب الأسرار)
_DATA_DIRS = ["project_images", "field_reports"]       # مجلدات الصور


def list_backups() -> list:  # النسخ الاحتياطية من الأحدث للأقدم
    """النسخ الاحتياطية من الأحدث للأقدم."""
    return sorted(BACKUP_DIR.glob("backup_*.zip"), reverse=True) if BACKUP_DIR.exists() else []


def make_backup() -> Path:  # ينشئ نسخة zip: قاعدة البيانات (بنسخ آمن أثناء التشغيل) + ملفات JSON + الصور + 
    """ينشئ نسخة zip: قاعدة البيانات (بنسخ آمن أثناء التشغيل) + ملفات JSON + الصور + سجل التدقيق."""
    BACKUP_DIR.mkdir(exist_ok=True)
    target = BACKUP_DIR / f"backup_{datetime.datetime.now():%Y%m%d_%H%M%S}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        if Path(DB_FILE).exists():
            with tempfile.TemporaryDirectory() as tmp:  # sqlite backup API يضمن نسخة سليمة والقاعدة تعمل
                tmp_db = Path(tmp) / "correspondence.db"
                src, dst = sqlite3.connect(DB_FILE), sqlite3.connect(tmp_db)
                try:
                    src.backup(dst)
                finally:
                    dst.close()
                    src.close()
                zf.write(tmp_db, "correspondence.db")
        for name in _DATA_FILES:
            if Path(name).exists():
                zf.write(name, name)
        for folder in _DATA_DIRS:
            for f in Path(folder).glob("*") if Path(folder).exists() else []:
                if f.is_file():
                    zf.write(f, f"{folder}/{f.name}")
    for old in list_backups()[KEEP_BACKUPS:]:  # تدوير النسخ القديمة
        old.unlink(missing_ok=True)
    return target


def maybe_auto_backup(hours: int = 24):  # نسخة تلقائية إن مضى أكثر من hours ساعة على آخر نسخة
    """نسخة تلقائية إن مضى أكثر من hours ساعة على آخر نسخة. يرجع مسار النسخة الجديدة أو None."""
    last = list_backups()
    if last and (datetime.datetime.now() - datetime.datetime.fromtimestamp(last[0].stat().st_mtime)) < datetime.timedelta(hours=hours):
        return None
    return make_backup()


_AUDIT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \| (\S+) \| user=(\S+) role=(\S+)\s*(.*)$")


def parse_audit(path: str = "audit.log") -> pd.DataFrame:  # يحوّل سجل التدقيق إلى جدول: الوقت، الحدث، المستخدم، الدور، التفاصيل (الأحدث أو
    """يحوّل سجل التدقيق إلى جدول: الوقت، الحدث، المستخدم، الدور، التفاصيل (الأحدث أولاً)."""
    rows = []
    p = Path(path)
    for line in (p.read_text(encoding="utf-8", errors="replace").splitlines() if p.exists() else []):
        m = _AUDIT_RE.match(line)
        if m:
            rows.append({"الوقت": m[1], "الحدث": m[2], "المستخدم": m[3], "الدور": m[4], "التفاصيل": m[5]})
    df = pd.DataFrame(rows, columns=["الوقت", "الحدث", "المستخدم", "الدور", "التفاصيل"])
    return df.iloc[::-1].reset_index(drop=True)


PACKAGES = ["streamlit", "pandas", "numpy", "plotly", "pydeck", "openai", "fpdf2", "python-dotenv", "pillow"]


def _ver(v: str):  # يحوّل رقم الإصدار إلى أرقام للمقارنة
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def check_updates(timeout: float = 6.0) -> list:  # يقارن إصدارات المكتبات المثبّتة بآخر إصدار على PyPI (يحتاج إنترنت)
    """يقارن إصدارات المكتبات المثبّتة بآخر إصدار على PyPI (يحتاج إنترنت). لا يفحص الثغرات نفسها، يكشف التقادم فقط."""
    out = []
    for pkg in PACKAGES:
        try:
            cur = md.version(pkg)
        except md.PackageNotFoundError:
            continue
        try:
            with urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json", timeout=timeout) as r:
                latest = json.load(r)["info"]["version"]
            status = "محدّثة" if _ver(cur) >= _ver(latest) else ("تحديث رئيسي متاح" if _ver(cur)[0] < _ver(latest)[0] else "تحديث متاح")
        except Exception:
            latest, status = "—", "تعذّر الفحص"
        out.append({"المكتبة": pkg, "المثبّت": cur, "الأحدث": latest, "الحالة": status})
    return out