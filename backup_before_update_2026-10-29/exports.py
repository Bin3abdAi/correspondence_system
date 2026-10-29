"""شريط التصدير الرسمي: طباعة / PDF / CSV / بريد — يُستدعى سطراً واحداً في كل صفحة.

الاستخدام داخل أي صفحة:
    from exports import export_bar
    export_bar("dashboard", "تقرير لوحة القيادة", ctx, df=df_visible, text=summary_text)

المتطلبات:  pip install fpdf2 arabic-reshaper python-bidi
إعدادات البريد في .env:  SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD SMTP_FROM
"""
import base64
import datetime
import hashlib
import html
import io
import os
import re
import smtplib
import ssl
from email.message import EmailMessage

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from config import get_setting
from security import audit

ORG = "أمانة محافظة جدة"
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\tahoma.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
_FONT_BOLD_CANDIDATES = [
    r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\tahomabd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
_EMAIL_RE = re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$")
_MAX_CSV_ROWS = 50_000


# ---------------- أدوات مساعدة ----------------
def _ref_number(page: str, ctx) -> str:  # يولّد رقماً مرجعياً فريداً للتقرير المصدّر
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    sig = hashlib.sha1(f"{page}{ctx.username}{stamp}".encode()).hexdigest()[:6].upper()
    return f"BIN-{stamp[:8]}-{sig}"


def _safe_cell(v):  # حماية CSV Injection: أي خلية تبدأ برمز معادلة تُسبق بفاصلة عليا
    """حماية CSV Injection: أي خلية تبدأ برمز معادلة تُسبق بفاصلة عليا."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


def csv_bytes(df: pd.DataFrame) -> bytes:  # يحوّل جدولاً إلى ملف CSV (يفتح في Excel بالعربية)
    out = df.head(_MAX_CSV_ROWS).copy()
    for c in out.select_dtypes(include=["object", "string", "category"]).columns:
        out[c] = out[c].astype(object).map(_safe_cell)
    return out.to_csv(index=False).encode("utf-8-sig")  # utf-8-sig ليفتح العربي في Excel


def _first_existing(paths):  # أول مسار موجود من قائمة (للخطوط)
    return next((p for p in paths if os.path.exists(p)), None)


def _ar(text: str) -> str:  # تشكيل الحروف العربية واتجاه الكتابة لـ PDF
    """تشكيل الحروف العربية واتجاه الكتابة لـ PDF."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


def pdf_bytes(title: str, ref: str, ctx, text: str = "", df: pd.DataFrame = None,
              classification: str = "داخلي") -> bytes:  # يبني ملف PDF عربي رسمي من عنوان ونص وجدول
    from fpdf import FPDF

    regular = _first_existing(_FONT_CANDIDATES)
    bold = _first_existing(_FONT_BOLD_CANDIDATES) or regular
    if not regular:
        raise RuntimeError("لم يُعثر على خط يدعم العربية (Arial/Tahoma).")

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(True, 18)
    pdf.add_font("AR", "", regular)
    pdf.add_font("AR", "B", bold)
    pdf.add_page()
    W = pdf.w - pdf.l_margin - pdf.r_margin

    def line(txt, size=11, style="", align="R", h=7):  # يكتب سطراً عربياً في PDF
        pdf.set_font("AR", style, size)
        pdf.multi_cell(W, h, _ar(txt), align=align, new_x="LMARGIN", new_y="NEXT")

    pdf.set_fill_color(14, 28, 48)
    pdf.rect(0, 0, pdf.w, 32, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(8)
    line("المملكة العربية السعودية", 10, align="C", h=5)
    line(ORG, 16, "B", "C", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(38)
    line(title, 15, "B", "R", 9)
    line(f"الرقم المرجعي: {ref}    |    التاريخ: {datetime.date.today()}", 10)
    who = ctx.username if ctx.logged_in else "زائر"
    line(f"أُعدّ بواسطة: {who}    |    التصنيف: {classification}", 10)
    pdf.ln(2)
    pdf.set_draw_color(0, 150, 180)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    for para in (text or "").replace("**", "").replace("#", "").split("\n"):
        if para.strip():
            line(para.strip(), 11)

    if df is not None and not df.empty:
        pdf.ln(3)
        line(f"جدول البيانات (أول {min(len(df), 40)} صفاً من {len(df)})", 11, "B")
        cols = list(df.columns)[:6]
        cw = W / len(cols)
        pdf.set_font("AR", "B", 8)
        pdf.set_fill_color(225, 240, 245)
        for c in reversed(cols):
            pdf.cell(cw, 7, _ar(str(c))[:22], border=1, align="C", fill=True)
        pdf.ln()
        pdf.set_font("AR", "", 8)
        for _, row in df[cols].head(40).iterrows():
            for c in reversed(cols):
                pdf.cell(cw, 6, _ar(str(row[c]))[:22], border=1, align="C")
            pdf.ln()

    pdf.ln(10)
    line("الاعتماد:  ______________________        التوقيع:  ______________________", 10)
    pdf.set_y(-14)
    pdf.set_font("AR", "", 8)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 6, _ar(f"وثيقة صادرة آلياً من منصة {ORG} — {ref} — تحتاج إلى اعتماد رسمي"),
             align="C")
    return bytes(pdf.output())


def _email_html(title, ref, ctx, text):  # يبني نص رسالة البريد الرسمي بصيغة HTML
    body = "<br>".join(html.escape(p) for p in (text or "").replace("**", "").split("\n"))
    who = html.escape(ctx.username or "زائر")
    return (f"<div dir='rtl' style='font-family:Tahoma,Arial;line-height:1.9'>"
            f"<h2 style='color:#0e3a5a'>{ORG}</h2><h3>{html.escape(title)}</h3>"
            f"<p>الرقم المرجعي: <b>{ref}</b> — {datetime.date.today()}</p><hr>{body}<hr>"
            f"<p style='color:#777;font-size:12px'>أُرسل من المنصة بواسطة {who}. "
            f"المرفقات تحتاج إلى اعتماد رسمي.</p></div>")


def send_email(to: str, title: str, ref: str, ctx, text: str, attachments: list) -> tuple:  # يرسل التقرير بالبريد عبر SMTP
    host = get_setting("SMTP_HOST")
    user = get_setting("SMTP_USER")
    pwd = get_setting("SMTP_PASSWORD")
    port = int(get_setting("SMTP_PORT", "587") or 587)
    sender = get_setting("SMTP_FROM", user)
    if not (host and user and pwd):
        return False, "لم تُضبط إعدادات البريد (SMTP_HOST / SMTP_USER / SMTP_PASSWORD) في ملف .env."
    to = (to or "").strip()
    if not _EMAIL_RE.match(to):
        return False, "عنوان البريد غير صحيح."
    msg = EmailMessage()
    msg["Subject"] = re.sub(r"[\r\n]+", " ", f"{title} — {ref}")[:200]  # منع حقن الترويسات
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(f"{title}\nالرقم المرجعي: {ref}\n\n{text}")
    msg.add_alternative(_email_html(title, ref, ctx, text), subtype="html")
    for name, data, mime in attachments:
        main, sub = mime.split("/")
        msg.add_attachment(data, maintype=main, subtype=sub, filename=name)
    try:
        ctxt = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=ctxt, timeout=20) as s:
                s.login(user, pwd)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.starttls(context=ctxt)
                s.login(user, pwd)
                s.send_message(msg)
        return True, f"تم إرسال التقرير إلى {to}."
    except Exception as e:
        return False, f"تعذّر الإرسال: {e}"


def _print_button(key: str):  # زر طباعة الصفحة
    components.html(f"""
    <button onclick="window.parent.print()" style="width:100%;padding:9px;border-radius:10px;
      border:1px solid #00d4ff;background:rgba(0,212,255,.08);color:#00d4ff;
      font-family:Tahoma;font-size:14px;cursor:pointer">🖨️ طباعة الصفحة</button>
    """, height=48)


_PRINT_CSS = """<style>@media print{[data-testid=stSidebar],header,[data-testid=stToolbar],
.stButton,iframe{display:none!important}body,.stApp{background:#fff!important;color:#000!important}
*{color:#000!important}}</style>"""


# ---------------- الواجهة ----------------
def export_bar(page_key: str, title: str, ctx, df: pd.DataFrame = None, text: str = "",
               classification: str = "داخلي"):  # شريط موحّد: طباعة | PDF | CSV | بريد
    """شريط موحّد: طباعة | PDF | CSV | بريد. التوليد كسول (عند الضغط فقط)."""
    st.markdown(_PRINT_CSS, unsafe_allow_html=True)
    st.markdown("##### 🧾 إصدار رسمي")
    k = f"exp:{page_key}"
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        _print_button(k)

    # --- PDF: خطوتان (تجهيز ثم تنزيل) لتفادي بطء التوليد في كل إعادة تشغيل ---
    with c2:
        if st.button("📄 تجهيز PDF", key=f"{k}:mkpdf", use_container_width=True):
            try:
                ref = _ref_number(page_key, ctx)
                st.session_state[f"{k}:pdf"] = (ref, pdf_bytes(title, ref, ctx, text, df, classification))
                audit("export_pdf", ctx, page=page_key, ref=ref)
            except Exception as e:
                st.session_state.pop(f"{k}:pdf", None)
                st.error(f"تعذّر إنشاء PDF: {e}\nتأكد من: pip install fpdf2 arabic-reshaper python-bidi")
        if f"{k}:pdf" in st.session_state:
            ref, data = st.session_state[f"{k}:pdf"]
            st.download_button("⬇️ تنزيل PDF", data, f"{ref}.pdf", "application/pdf",
                               key=f"{k}:dlpdf", use_container_width=True)

    with c3:
        if df is not None and not df.empty:
            if st.button("📊 تجهيز CSV", key=f"{k}:mkcsv", use_container_width=True):
                ref = _ref_number(page_key, ctx)
                st.session_state[f"{k}:csv"] = (ref, csv_bytes(df))
                audit("export_csv", ctx, page=page_key, rows=len(df))
            if f"{k}:csv" in st.session_state:
                ref, data = st.session_state[f"{k}:csv"]
                st.download_button("⬇️ تنزيل CSV", data, f"{ref}.csv", "text/csv",
                                   key=f"{k}:dlcsv", use_container_width=True)
        else:
            st.button("📊 CSV (لا بيانات)", key=f"{k}:nocsv", disabled=True, use_container_width=True)

    with c4:
        open_mail = st.toggle("✉️ إرسال بالبريد", key=f"{k}:mailtoggle")

    if open_mail:
        if not ctx.logged_in:
            st.warning("الإرسال بالبريد متاح للمستخدمين المسجّلين فقط.")
            return
        to = st.text_input("البريد المستلم", key=f"{k}:to", placeholder="name@example.gov.sa")
        att_pdf = st.checkbox("إرفاق PDF", value=True, key=f"{k}:attpdf")
        att_csv = st.checkbox("إرفاق CSV", value=False, key=f"{k}:attcsv",
                              disabled=df is None or df.empty)
        ok = st.checkbox("أؤكد مراجعة المحتوى واعتماده للإرسال الرسمي", key=f"{k}:confirm")
        if st.button("إرسال الآن", key=f"{k}:send", disabled=not ok, type="primary"):
            ref = _ref_number(page_key, ctx)
            atts = []
            try:
                if att_pdf:
                    atts.append((f"{ref}.pdf", pdf_bytes(title, ref, ctx, text, df, classification),
                                 "application/pdf"))
                if att_csv and df is not None:
                    atts.append((f"{ref}.csv", csv_bytes(df), "text/csv"))
            except Exception as e:
                st.error(f"تعذّر تجهيز المرفقات: {e}")
                return
            good, msg = send_email(to, title, ref, ctx, text, atts)
            audit("export_email", ctx, page=page_key, ok=good, to_domain=to.split("@")[-1][:60])
            (st.success if good else st.error)(msg)


def voice_toggle():  # مفتاح «الرد الصوتي» — ضعه مرة واحدة في render_sidebar
    """مفتاح «الرد الصوتي» — ضعه مرة واحدة في render_sidebar. يعمل على كل الصفحات."""
    return st.toggle("🔊 الرد الصوتي التلقائي", key="speak_replies", value=True,
                     help="عند التفعيل يُقرأ كل رد من المساعد بصوت عربي.")


def play_audio(audio: bytes, autoplay: bool = True, label: str = "") -> None:  # يشغّل الصوت بلا شريط تشغيل ولا مؤقّت: ينطق تلقائياً مثل الترحيب، وفيه زر 🔊 صغير لإعادة الاستماع
    """يشغّل الصوت بلا شريط تشغيل ولا مؤقّت: ينطق تلقائياً مثل الترحيب (إن سمح المتصفح)، ومعه زر 🔊 صغير لإعادة الاستماع."""
    if not audio:
        return
    try:
        from ui import theme_palette  # استيراد متأخر لتفادي الدوران
        a, _, t = theme_palette()
    except Exception:
        a, t = "#1f9d62", "#f4fff8"
    b64 = base64.b64encode(audio).decode()
    lab = html.escape(label)
    page = f"""<!doctype html><meta charset="utf-8"><style>*{{box-sizing:border-box}}body{{margin:0;direction:rtl;font-family:Tahoma,Arial,sans-serif}}
button{{cursor:pointer;display:inline-flex;align-items:center;gap:6px;border:1px solid {a};background:{a}22;color:{t};border-radius:999px;
padding:4px 12px;font:600 13px Tahoma,Arial,sans-serif;transition:.2s}}button:hover{{background:{a}55}}
button.on{{box-shadow:0 0 0 0 {a}aa;animation:p 1.1s infinite}}@keyframes p{{70%{{box-shadow:0 0 0 9px {a}00}}100%{{box-shadow:0 0 0 0 {a}00}}}}</style>
<audio id="a" src="data:audio/mpeg;base64,{b64}" {"autoplay" if autoplay else ""}></audio>
<button id="b" title="إعادة الاستماع">🔊 {lab or "استمع"}</button>
<script>var a=document.getElementById('a'),b=document.getElementById('b');
a.onplay=function(){{b.classList.add('on')}};a.onended=a.onpause=function(){{b.classList.remove('on')}};
b.onclick=function(){{if(!a.paused){{a.pause();a.currentTime=0;}}else{{a.currentTime=0;a.play();}}}};
{"a.play().catch(function(){});" if autoplay else ""}</script>"""
    components.html(page, height=40)


def _tts(text: str):  # يولّد الصوت مرة واحدة لكل نص ويخزنه في الجلسة (لا إعادة فوترة عند كل تحديث)
    """يولّد الصوت مرة واحدة لكل نص ويخزنه في الجلسة (لا إعادة فوترة عند كل تحديث)."""
    cache = st.session_state.setdefault("_tts_cache", {})
    h = hashlib.sha1((st.session_state.get("persona", "nabras") + "|" + text).encode()).hexdigest()  # الصوت يتبع الشخصية
    if h not in cache:
        from ai_service import spoken_version, synthesize_speech
        audio = synthesize_speech(spoken_version(text))
        if isinstance(audio, tuple):  # بعض النسخ ترجع (bytes, mime)
            audio = audio[0]
        cache[h] = audio
        if len(cache) > 20:
            cache.pop(next(iter(cache)))
    return h, cache[h]


def show_reply(text: str, key: str, kind: str = "ai"):  # اعرض أي رد نصي من المساعد + الصوت
    """اعرض أي رد نصي من المساعد + الصوت. استبدل به st.markdown(reply) في كل مكان."""
    if not text:
        return
    st.markdown(text)
    if not st.session_state.get("speak_replies", True):
        speak_button(text, key)
        return
    try:
        h, audio = _tts(text)
    except Exception as e:
        st.caption(f"الصوت غير متاح: {e}")
        return
    if not audio:
        st.caption("تعذّر توليد الصوت (تحقق من مفتاح OpenAI).")
        return
    played = st.session_state.setdefault("_tts_played", set())
    first = (key, h) not in played  # التشغيل التلقائي مرة واحدة فقط لكل رد
    played.add((key, h))
    play_audio(audio, autoplay=first)


def speak_button(text: str, key: str):  # زر «استمع» لأي نص: يولّد الصوت عند الضغط فقط (يعتمد على synthesize_speech في a
    """زر «استمع» لأي نص: يولّد الصوت عند الضغط فقط (يعتمد على synthesize_speech في ai_service)."""
    if not text:
        return
    if st.button("🔊 استمع", key=f"spk:{key}"):
        try:
            _, audio = _tts(text)
            if audio:
                play_audio(audio, autoplay=True)
            else:
                st.warning("تعذّر توليد الصوت (تحقق من مفتاح OpenAI).")
        except Exception as e:
            st.warning(f"الصوت غير متاح: {e}")
