"""واجهة API مبسّطة للتكامل مع أنظمة أخرى (قراءة فقط، معاملات «عام» فقط).

التشغيل (نافذة cmd ثانية):  python api_server.py
في .env:  API_KEY=مفتاح-طويل-عشوائي     API_PORT=8502 (اختياري)

الاستدعاء:
  GET /api/transaction/TRX-900001     ترويسة: X-API-Key: <المفتاح>
  GET /api/health
لا تُعرض أبداً معاملات «سري» أو «سري للغاية»، ولا أي بيانات شخصية.
"""
import hmac
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from config import get_setting
from data_layer import load_all_transactions
from security import GUEST, audit, visible_transactions

_FIELDS = ["رقم المعاملة", "الحي", "القسم المكلف", "درجة الأهمية", "الحالة", "تاريخ التسليم", "التاريخ المتوقع للإنجاز"]
_DF = None


def _df():  # يحمّل المعاملات العامة مرة واحدة ويحتفظ بها للـAPI
    global _DF
    if _DF is None:
        _DF = visible_transactions(load_all_transactions(), GUEST)  # الزائر فقط = «عام»
    return _DF


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj: dict):  # يرسل رداً JSON بالحالة المطلوبة
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # يعالج طلبات GET: /api/health و /api/transaction/<رقم> بمفتاح API
        key = get_setting("API_KEY")
        if self.path == "/api/health":
            return self._send(200, {"ok": True})
        if not key or not hmac.compare_digest(self.headers.get("X-API-Key", ""), key):
            audit("api_denied", GUEST, path=self.path[:80])
            return self._send(401, {"error": "unauthorized"})
        if self.path.startswith("/api/transaction/"):
            trx = self.path.rsplit("/", 1)[-1].strip().upper()
            df = _df()
            hit = df[df["رقم المعاملة"].astype(str) == trx]
            audit("api_lookup", GUEST, trx=trx[:30])
            if hit.empty:
                return self._send(404, {"error": "not_found"})
            row = hit.iloc[0]
            return self._send(200, {k: str(row[k]) for k in _FIELDS if k in hit.columns})
        self._send(404, {"error": "not_found"})

    def log_message(self, *a):  # يوقف طباعة سجل الطلبات في الشاشة
        pass


if __name__ == "__main__":
    port = int(get_setting("API_PORT", "8502") or 8502)
    print(f"API يعمل على http://127.0.0.1:{port}  (اضغط Ctrl+C للإيقاف)")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()