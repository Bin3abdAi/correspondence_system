"""قائمة الاجتماعات من Notion (قراءة فقط).

الإعداد في .env:
  NOTION_TOKEN=secret_xxx          مفتاح التكامل (Internal Integration) من notion.so/my-integrations
  NOTION_MEETINGS_DB_ID=xxxxxxxx   معرّف قاعدة بيانات الاجتماعات (32 خانة من رابط القاعدة)
مهم: في Notion افتح القاعدة ← ⋯ ← Connections ← أضف التكامل، وإلا ترجع القاعدة فارغة.
القاعدة يلزمها عمود عنوان (Title) وعمود تاريخ (Date)؛ وعمود مكان (نص أو اختيار) اختياري.
"""
import datetime
import json
import urllib.request

from config import get_setting

_API = "https://api.notion.com/v1"
_VERSION = "2022-06-28"


def configured() -> bool:  # هل ضُبط مفتاح Notion ومعرّف القاعدة؟
    return bool(get_setting("NOTION_TOKEN") and get_setting("NOTION_MEETINGS_DB_ID"))


def _plain(rich) -> str:  # يحوّل نص Notion المنسّق إلى نص عادي
    return "".join(t.get("plain_text", "") for t in (rich or []))


def parse_page(page: dict) -> dict | None:  # يستخرج (العنوان، البداية، النهاية، المكان) من أي صفحة بغض النظر عن أسماء الأعم
    """يستخرج (العنوان، البداية، النهاية، المكان) من أي صفحة بغض النظر عن أسماء الأعمدة."""
    title = start = end = place = ""
    for name, prop in (page.get("properties") or {}).items():
        t = prop.get("type")
        if t == "title" and not title:
            title = _plain(prop.get("title"))
        elif t == "date" and not start and prop.get("date"):
            start, end = prop["date"].get("start") or "", prop["date"].get("end") or ""
        elif not place and any(k in name.lower() for k in ("مكان", "موقع", "place", "location", "room")):
            if t == "select" and prop.get("select"):
                place = prop["select"].get("name", "")
            elif t == "rich_text":
                place = _plain(prop.get("rich_text"))
    if not (title and start):
        return None
    return {"title": title.strip()[:120], "start": start, "end": end, "place": place.strip()[:80], "url": page.get("url", "")}


def fetch_meetings(limit: int = 100) -> tuple[list, str]:  # يرجع (قائمة الاجتماعات مرتبة، رسالة خطأ إن وُجدت)
    """يرجع (قائمة الاجتماعات مرتبة، رسالة خطأ إن وُجدت). لا يرفع استثناءات."""
    if not configured():
        return [], "لم يُضبط NOTION_TOKEN / NOTION_MEETINGS_DB_ID في ملف .env."
    db = get_setting("NOTION_MEETINGS_DB_ID").replace("-", "").strip()
    req = urllib.request.Request(
        f"{_API}/databases/{db}/query", data=json.dumps({"page_size": limit}).encode(), method="POST",
        headers={"Authorization": f"Bearer {get_setting('NOTION_TOKEN')}", "Notion-Version": _VERSION,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        return [], f"تعذّر الاتصال بـ Notion: {e}"
    items = [m for m in (parse_page(p) for p in data.get("results", [])) if m]
    return sorted(items, key=lambda m: m["start"]), ""


def upcoming(meetings: list, days: int = 14, today: datetime.date | None = None) -> list:  # اجتماعات من اليوم حتى days يوماً قادمة
    """اجتماعات من اليوم حتى days يوماً قادمة."""
    today = today or datetime.date.today()
    out = []
    for m in meetings:
        try:
            d = datetime.date.fromisoformat(m["start"][:10])
        except ValueError:
            continue
        if today <= d <= today + datetime.timedelta(days=days):
            out.append({**m, "date": d})
    return sorted(out, key=lambda m: m["start"])