"""هيكل الصفحة: الشريط الجانبي وتسجيل الدخول وتنبيهات SLA والفلاتر وزر إمكانية الوصول."""
import time

import nafath
import notion_meetings
import table_engine as te
from config import CONFIDENTIALITY_LEVELS  # ترتيب مستويات السرية في الفلتر
from fields import combo_multi
from greeting import riyadh_now
from views_common import *  # noqa: F401,F403  (الأسماء العامة + الاستيرادات)


_DAYS_AR = {"Sunday": "الأحد", "Monday": "الإثنين", "Tuesday": "الثلاثاء",
            "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت"}


_MEETINGS = {
    "Sunday": "🚨 **الأحد:** تسليم المهام ومناقشة SLA (09:00 ص)",
    "Tuesday": "🚨 **الثلاثاء:** الاجتماع الدوري (11:00 ص)",
    "Thursday": "🚨 **الخميس:** الاجتماع الأسبوعي (02:00 م)",
}


_FILTER_COLUMNS = {"الحي": "تصفية حسب الحي:", "القسم المكلف": "تصفية حسب القطاع:",
                   "درجة الأهمية": "درجة الأهمية:", "السرية": "درجة السرية:"}  # عمود البيانات ← عنوان الفلتر

_PRIORITY_ORDER = ["حرج للغاية", "عاجل", "هام", "عادي"]  # ترتيب منطقي لدرجة الأهمية بدل الترتيب الأبجدي


# ======================================================
# الشريط الجانبي
# ======================================================
def render_sidebar(ctx: AuthContext, df_visible: pd.DataFrame) -> dict:  # الشريط الجانبي: المساعد الصوتي والدخول وSLA والفلاتر
    with st.sidebar:
        st.markdown("### 🎙️ المساعد الصوتي السيادي")
        render_voice_assistant_widget()  # يُستدعى مرة واحدة فقط
        st.session_state.setdefault("speak_replies", True)  # الرد الصوتي مفعّل دائماً (أُزيل المفتاح من الواجهة بطلب المستخدم)
        st.divider()
        _auth_panel(ctx)
        st.divider()
        if ctx.logged_in:
            _sla_panel(ctx, df_visible)  # تنبيهات مهلة الإنجاز (SLA) للمسجّلين
            st.divider()
        if ctx.role in ("admin", "manager"):
            _schedule_panel()  # مواعيد داخلية: للمدير فقط
            st.divider()
        st.toggle("🟢 الوضع المبسّط", key="simple_mode", help="يُظهر الصفحات الأساسية فقط")
        filters = _filters_panel(df_visible)
        st.divider()
        st.markdown(
            '<div style="text-align:center;color:#38bdf8;font-size:.85rem;font-weight:bold;padding:10px;">'
            f"{html.escape(APP_NAME)}<br>{html.escape(APP_TAGLINE)} · {APP_VERSION}<br>"
            f'<span style="color:#94a3b8;font-weight:500">✍️ تطوير {html.escape(DEVELOPER_SIGNATURE)}</span></div>',
            unsafe_allow_html=True,
        )
    return filters


def _auth_panel(ctx: AuthContext) -> None:  # لوحة تسجيل الدخول والتحقق الثنائي
    st.markdown("### 🔒 توثيق الجلسة والصلاحيات الأمنية")
    if ctx.logged_in:
        st.success(f"🟢 {ctx.username} — {ctx.role_label} — المستويات المتاحة: {'، '.join(ctx.visible_levels)}")
        if ctx.role == "manager" and ctx.department:
            st.caption(f"🏢 نطاق عملك: {ctx.department}")
        if ctx.role == "reviewer":
            st.caption("👁️ حساب مراجعة: قراءة فقط، لا يمكنه التعديل أو التكليف.")
        if st.button("تسجيل الخروج 🚪", width="stretch"):
            logout(ctx)
            st.rerun()
        return
    p2 = pending_2fa()
    if p2:  # الخطوة الثانية: رمز التحقق الثنائي
        st.info("🔐 التحقق الثنائي: " + ("افتح تطبيق المصادقة وأدخل الرمز المكوّن من 6 أرقام."
                                         if p2["mode"] == "totp" else "أرسلنا رمزاً إلى بريد المدير (صالح 5 دقائق)."))
        if st.session_state.get("otp_send_msg"):
            st.error(st.session_state["otp_send_msg"])
        with st.form("twofa_form"):
            code = st.text_input("رمز التحقق", max_chars=6)
            ok_btn = st.form_submit_button("تأكيد ✅", width="stretch")
        if ok_btn:
            ok, message = verify_2fa(code)
            if ok:
                st.rerun()
            st.error(message)
        if st.button("إلغاء", key="twofa_cancel", width="stretch"):
            cancel_2fa()
            st.rerun()
        return
    with st.form("login_form"):
        user = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("تسجيل الدخول 🔑", width="stretch")
    if submitted:
        ok, message = login(user, password)
        if ok or pending_2fa():
            st.rerun()
        st.error(message)
    _nafath_box()


def _naf_cancel() -> None:  # callback: يلغي طلب نفاذ الجاري
    st.session_state.pop("naf_req", None)


def _naf_clear_verified() -> None:
    st.session_state.pop("naf_verified", None)


def _nafath_box() -> None:  # الدخول عبر نفاذ: محاكاة تجريبية واضحة (ليست ربطاً حقيقياً) — انظر nafath.py
    mode = nafath.mode()
    if mode == "off":
        return
    with st.expander("🪪 الدخول عبر نفاذ (تجريبي)"):
        if mode == "live":
            st.info("الربط الفعلي مع نفاذ يحتاج اعتماد الجهة ومفاتيح ربط رسمية، ولم يُفعَّل في هذه النسخة. استعمل اسم المستخدم وكلمة المرور.")
            return
        st.caption("⚠️ محاكاة تجريبية لشكل تجربة الدخول عبر نفاذ، وليست خدمة نفاذ الحقيقية ولا تتحقق من هويتك. "
                   f"لا تُدخل رقم هويتك الحقيقي؛ جرّب الرقم التجريبي {nafath.DEMO_ID}.")
        done = st.session_state.get("naf_verified")
        if done:
            st.success(f"🟢 هوية موثّقة تجريبياً ({done}). لا يوجد حساب موظف مرتبط بها، فتبقى بصلاحيات الزائر نفسها.")
            st.button("إنهاء التوثيق التجريبي", key="naf_end", on_click=_naf_clear_verified, width="stretch")
            return
        req = st.session_state.get("naf_req")
        if req and nafath.expired(req):
            st.session_state.pop("naf_req", None)
            req = None
            st.warning("انتهت صلاحية الطلب (دقيقتان). أرسل طلباً جديداً.")
        if not req:
            nid = st.text_input("رقم الهوية الوطنية / الإقامة (10 أرقام)", key="naf_id", max_chars=10, placeholder=nafath.DEMO_ID).strip()
            if st.button("إرسال طلب نفاذ 📲", key="naf_send", width="stretch"):
                stamps = st.session_state.setdefault("naf_stamps", [])
                if not nafath.valid_id(nid):
                    st.error("رقم الهوية غير صحيح: 10 أرقام تبدأ بـ 1 أو 2.")
                elif not nafath.rate_ok(stamps):
                    st.error("طلبات كثيرة خلال وقت قصير، حاول بعد دقائق.")
                else:
                    stamps.append(time.time())
                    r = nafath.new_request(nid)
                    r["account"] = nafath_account(nid)  # يُحسم الحساب الآن؛ ولا نخزّن الرقم الأصلي
                    st.session_state["naf_req"] = r
                    st.rerun()
            return
        st.markdown('<style>/*nofix*/</style><div style="text-align:center;padding:10px;border-radius:14px;border:1px solid rgba(255,255,255,.35);'
                    'background:rgba(255,255,255,.08);color:#f4fff8">افتح تطبيق نفاذ واختر الرقم'
                    f'<div style="font-size:2.4rem;font-weight:800;letter-spacing:4px;color:#f3d77a">{req["random"]}</div></div>',
                    unsafe_allow_html=True)
        st.caption(f"الهوية {req['mask']} · ينتهي الطلب خلال {nafath.seconds_left(req)} ثانية")
        c1, c2 = st.columns(2)
        if c1.button("✅ محاكاة الموافقة", key="naf_ok", width="stretch"):
            st.session_state.pop("naf_req", None)
            if req.get("account") and login_nafath_demo(req["account"], req["mask"]):
                st.rerun()
            st.session_state["naf_verified"] = req["mask"]
            st.rerun()
        c2.button("إلغاء", key="naf_no", on_click=_naf_cancel, width="stretch")


_SLA_CSS = """<style>/*nofix*/
.sla-wrap{direction:rtl}
.sla-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:4px 0 8px}
.sla-c{border-radius:14px;padding:9px 11px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08)}
.sla-c span{display:block;font-size:.78rem;color:#e6eefc;font-weight:600}
.sla-c b{display:block;font-size:1.65rem;line-height:1.3;color:#ffffff;font-variant-numeric:tabular-nums}
.sla-c small{display:block;font-size:.7rem;color:#d3dff1}
.sla-c.red{border-color:rgba(251,113,133,.8);background:rgba(225,29,72,.22)}.sla-c.red b{color:#ffd5db}
.sla-c.amb{border-color:rgba(251,191,36,.8);background:rgba(217,119,6,.24)}.sla-c.amb b{color:#ffeab0}
.sla-sub{font-size:.76rem;color:#d3dff1;margin:6px 2px 2px;font-weight:600}
.sla-row{margin:5px 2px}
.sla-row .n{display:flex;justify-content:space-between;gap:8px;font-size:.78rem;color:#f1f6ff;line-height:1.5}
.sla-row .n b{color:#ffd5db;white-space:nowrap}.sla-row .n small{color:#d3dff1;font-weight:400}
.sla-row .bar{height:6px;border-radius:99px;background:rgba(255,255,255,.16);overflow:hidden;margin-top:2px}
.sla-row .bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#fb7185,#f59e0b)}
.sla-ok{border-radius:12px;padding:10px 12px;background:rgba(16,185,129,.2);border:1px solid rgba(52,211,153,.7);color:#d1fae5;font-size:.85rem;line-height:1.8}
</style>"""


def _sla_cards(sla: dict, open_n: int) -> str:  # بطاقتا «متأخرة / خلال 24 ساعة» + أكثر الإدارات تأخراً (ألوان ثابتة تُقرأ في كل الأنماط لأن الشريط الجانبي داكن دائماً)
    od, sn = int(sla["overdue"]), int(sla["soon"])
    pct = f"{od / open_n * 100:.1f}% من المفتوحة" if open_n else "—"
    by = sla["by_dept"].head(4)
    mx = max([int(v) for v in by["متأخرة"]] + [1]) if len(by) else 1
    rows = ""
    for _, r in by.iterrows():
        late = int(r["متأخرة"])
        w = max(4, round(late / mx * 100)) if late else 0
        rows += (f'<div class="sla-row"><div class="n"><span>{html.escape(str(r["القسم المكلف"]))}</span>'
                 f'<b>{late:,} <small>متأخرة</small></b></div><div class="bar"><i style="width:{w}%"></i></div></div>')
    return (_SLA_CSS + '<div class="sla-wrap"><div class="sla-grid">'
            f'<div class="sla-c red"><span>🔴 متأخرة</span><b>{od:,}</b><small>{pct}</small></div>'
            f'<div class="sla-c amb"><span>🟠 خلال 24 ساعة</span><b>{sn:,}</b><small>تحتاج متابعة اليوم</small></div></div>'
            + (f'<div class="sla-sub">أكثر الإدارات تأخراً</div>{rows}' if rows else "") + "</div>")


def _sla_text(ctx: AuthContext, sla: dict) -> str:  # نص التنبيه الجاهز للإرسال (أرقام مجمّعة بلا بيانات أفراد)
    lines = ["⏰ تنبيه مهلة الإنجاز (SLA) — أمانة محافظة جدة", f"التاريخ: {riyadh_now():%Y-%m-%d %H:%M}",
             f"النطاق: {ctx.department or 'كل الإدارات'}",
             f"🔴 المعاملات المتأخرة: {int(sla['overdue']):,}", f"🟠 تستحق خلال 24 ساعة: {int(sla['soon']):,}"]
    top = sla["by_dept"].head(5)
    if len(top):
        lines.append("أكثر الإدارات تأخراً:")
        lines += [f"• {r['القسم المكلف']}: {int(r['متأخرة']):,} متأخرة، {int(r['تستحق قريباً']):,} قريبة" for _, r in top.iterrows()]
    return "\n".join(lines)


def _sla_refresh() -> None:  # زر التحديث: يلغي المخزّن فيُحسب من جديد
    st.session_state.pop("_sla_cache2", None)


def _sla_panel(ctx: AuthContext, df: pd.DataFrame) -> None:  # تنبيه مبكر: المعاملات المتأخرة والمستحقة خلال 24 ساعة ضمن نطاق صلاحية المستخدم
    """تنبيه مبكر: المعاملات المتأخرة والمستحقة خلال 24 ساعة ضمن نطاق صلاحية المستخدم، مع إرسال بالبريد أو الجوال (واتساب/رسالة)."""
    st.markdown("### ⏰ تنبيهات مهلة الإنجاز (SLA)")
    ck = (ctx.role, ctx.department, len(df))
    cache = st.session_state.get("_sla_cache2")
    if not cache or cache[0] != ck or time.time() - cache[1] > 120:  # نعيد الحساب كل دقيقتين أو عند تغيّر البيانات أو بزر التحديث
        open_n = int((df["الحالة"] != STATUS_DONE).sum()) if len(df) and "الحالة" in df.columns else 0
        cache = (ck, time.time(), an.sla_summary(df), open_n)
        st.session_state["_sla_cache2"] = cache
    sla, open_n = cache[2], cache[3]
    if sla["overdue"] == 0 and sla["soon"] == 0:
        st.markdown(_SLA_CSS + '<div class="sla-ok">✅ لا توجد معاملات متأخرة أو قريبة الاستحقاق ضمن نطاقك.</div>', unsafe_allow_html=True)
        return
    st.markdown(_sla_cards(sla, open_n), unsafe_allow_html=True)
    st.caption(f"آخر تحديث {time.strftime('%H:%M', time.localtime(cache[1]))} · يتجدد تلقائياً كل دقيقتين")
    st.button("🔄 حدّث الآن", key="sla_refresh", on_click=_sla_refresh, width="stretch")
    with st.expander("📋 التفاصيل حسب الإدارة"):
        st.dataframe(sla["by_dept"], hide_index=True, width="stretch")
        if not sla["worst"].empty:
            st.caption("أقدم المتأخرات:")
            st.dataframe(sla["worst"], hide_index=True, width="stretch")
    with st.expander("📤 إرسال التنبيه (بريد • واتساب • رسالة)"):
        txt = _sla_text(ctx, sla)
        to = st.text_input("إلى: بريد أو جوال (05XXXXXXXX)", value=get_setting("SLA_ALERT_EMAIL") or get_setting("ADMIN_2FA_EMAIL") or "",
                           key="sla_to", placeholder="name@example.com أو 05XXXXXXXX").strip()
        st.code(txt, language=None)  # معاينة النص (وفيها زر نسخ)
        lk = notifier.share_links(txt, "تنبيه مهلة الإنجاز SLA", to)
        b1, b2, b3 = st.columns(3)
        with b1:
            link_btn("💬 واتساب", lk["whatsapp"])
        with b2:
            link_btn("📱 رسالة", lk["sms"])
        with b3:
            link_btn("✉️ بريد", lk["mailto"])
        st.caption("الأزرار الثلاثة تفتح تطبيقك والنص جاهز، ولا تحتاج أي إعداد.")
        if ctx.role in ("admin", "manager"):  # الإرسال المباشر من المنصة (SMTP أو بوابة SMS) للمدراء فقط
            valid = bool(notifier.valid_email(to) or notifier.normalize_phone(to))
            if st.button("📨 أرسل من المنصة مباشرة", key="sla_send", width="stretch", disabled=not valid,
                         help="يستخدم SMTP للبريد أو بوابة الرسائل المضبوطة في ملف .env"):
                ok, msg = notifier.notify(to, "تنبيه مهلة الإنجاز SLA", txt, ctx)
                (st.success if ok else st.error)(msg)
                audit("sla_alert_sent", ctx, ok=ok)
            if not valid:
                st.caption("اكتب بريداً صحيحاً أو جوالاً سعودياً لتفعيل زر الإرسال المباشر.")


@st.cache_data(ttl=300, show_spinner=False)
def _notion_cached() -> tuple:  # يجلب اجتماعات Notion ويخزنها 5 دقائق
    return notion_meetings.fetch_meetings()  # تحديث كل 5 دقائق


def _schedule_panel() -> None:  # جدول الاجتماعات (Notion أو الاحتياطي)
    st.markdown("### 📅 جدول المواعيد والاجتماعات")
    now = datetime.datetime.now()
    day = now.strftime("%A")
    st.info(f"📍 **اليوم:** {_DAYS_AR.get(day, day)} | {now.strftime('%I:%M %p')}")
    if notion_meetings.configured():  # الاجتماعات من Notion
        items, err = _notion_cached()
        if err:
            st.warning(err)
        else:
            up = notion_meetings.upcoming(items, 14)
            if not up:
                st.caption("لا اجتماعات خلال 14 يوماً قادمة في Notion.")
            for m in up:
                tm = m["start"][11:16] if len(m["start"]) > 10 else ""
                line = f"**{_DAYS_AR.get(m['date'].strftime('%A'), '')} {m['date']}** {tm} — {m['title']}" + (f" 📍{m['place']}" if m["place"] else "")
                (st.warning if m["date"] == now.date() else st.write)(line)
            if st.button("🔄 تحديث من Notion", key="notion_refresh", width="stretch"):
                _notion_cached.clear()
                st.rerun()
            return
    if day in _MEETINGS:  # احتياطي عند عدم ضبط Notion
        st.warning(_MEETINGS[day])


def _filter_options(df: pd.DataFrame, col: str) -> list:  # خيارات الفلتر: السرية بترتيبها (عام ← سري ← سري للغاية) والأهمية بترتيبها المنطقي
    """خيارات الفلتر: السرية بترتيبها، والأهمية بترتيبها المنطقي، وغيرها أبجدياً. تُبنى من البيانات المرئية للمستخدم فقط."""
    vals = [v for v in df[col].dropna().unique()]
    if col == "السرية":  # عام ثم سري ثم سري للغاية (فقط ما يحق للمستخدم رؤيته)
        return sorted(vals, key=lambda v: CONFIDENTIALITY_LEVELS.get(v, 9))
    if col == "درجة الأهمية":
        return sorted(vals, key=lambda v: _PRIORITY_ORDER.index(v) if v in _PRIORITY_ORDER else 9)
    return sorted(vals)


def _filters_panel(df: pd.DataFrame) -> dict:  # فلاتر الحي والقطاع والأهمية والسرية: قوائم تُبحث بالكتابة وتقبل قيماً يدوية (السرية تظهر خياراتها بحسب صلاحية المستخدم)
    st.markdown("### 🔍 فلاتر البحث والتحليل اللحظي")
    st.caption("اكتب للبحث، أو اختر، أو أضف قيمتك ثم Enter. الفارغ = الكل.")
    out = {}
    for col, label in _FILTER_COLUMNS.items():
        if col not in df.columns:  # عمود غير موجود في هذه البيانات: نتجاوزه بدل أن ينهار الفلتر
            continue
        out[col] = combo_multi(label, _filter_options(df, col), key=f"fq_{col}", placeholder="الكل")
    return out


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:  # يطبّق الفلاتر المختارة على الجدول (قيم متعددة = «أو»، وفلاتر متعددة = «و»)
    """يطبّق الفلاتر المختارة. القيمة قد تكون قائمة (الجديد) أو نصاً (القديم)؛ الفارغ وخيار «الكل» لا يصفّيان شيئاً."""
    for col, value in filters.items():
        terms = te.clean_terms([value] if isinstance(value, str) else value)
        terms = [t for t in terms if t != ALL_LABEL]
        if not terms or col not in df.columns:
            continue
        vocab = list(CONFIDENTIALITY_LEVELS) if col == "السرية" else None
        df = df[te.choice_mask(df[col], terms, vocab)]
    return df


# ======================================================
# شريط تسهيلات الوصول + النمط (يختاره المستخدم)
# ======================================================
def _reset_access() -> None:  # يعيد كل التفضيلات لوضعها الأصلي (callback: يسمح بتعديل مفاتيح الودجت)
    """يعيد كل التفضيلات لوضعها الأصلي (callback: يسمح بتعديل مفاتيح الودجت)."""
    st.session_state.update({"theme": THEMES[0], "font_scale": "عادي", "high_contrast": False, "reduce_motion": False,
                             "plain_font": False, "big_spacing": False, "mark_links": False, "show_chars": True, "ui_sounds": True, "chars_voice": True})


def render_access_bar() -> None:  # شريط علوي كما كان: النمط (4 أنماط)، حجم الخط، التباين العالي
    """شريط علوي كما كان: النمط (4 أنماط)، حجم الخط، التباين العالي. والمزيد من التسهيلات في expander. القيم تُقرأ في ui.inject_prefs()."""
    if st.session_state.get("theme") not in THEMES:  # قيمة قديمة من نسخة سابقة (وطني/نهاري...) ← الافتراضي
        st.session_state["theme"] = THEMES[0]
    c1, c2, c3 = st.columns([2, 2, 1.4])
    c1.selectbox("🎨 النمط", THEMES, key="theme", help="غيّر شكل المنصة بما يناسبك")  # النمط
    c2.radio("🔠 حجم الخط", ["عادي", "كبير", "أكبر"], key="font_scale", horizontal=True)  # A+ / A-
    c3.toggle("◐ تباين عالٍ", key="high_contrast")  # تباين
    with st.expander("♿ المزيد من التسهيلات"):
        st.session_state.setdefault("show_chars", True)
        st.session_state.setdefault("ui_sounds", True)
        st.session_state.setdefault("chars_voice", True)
        e1, e2, e3, e4, e5, e6, e7 = st.columns(7)
        e1.toggle("🅰️ خط أوضح", key="plain_font")
        e2.toggle("↕️ مسافات أوسع", key="big_spacing")
        e3.toggle("🔗 تمييز الروابط", key="mark_links")
        e4.toggle("🧘 إيقاف الحركة", key="reduce_motion", help="يوقف النجوم والشخصيتين")
        e5.toggle("🤖 الشخصيتان", key="show_chars")
        e6.toggle("🔔 أصوات تقنية", key="ui_sounds", help="أصوات خفيفة عند التفاعل مع Bin3abdAi وسعيدان (تُكتم أثناء صوت المساعد والتسجيل)")
        e7.toggle("🗣️ نطق الشخصيتين", key="chars_voice", help="ينطق Bin3abdAi وسعيدان كلامهما بصوتين مختلفين (بعد أول نقرة في الصفحة). يصمتان أثناء صوت المساعد أو تسجيل الميكروفون أو الكتابة، ويمكن كتمهما بزر 🔇 بينهما")
        st.button("↺ إعادة الضبط", key="acc_reset", on_click=_reset_access)
        st.button("♿ صفحة إمكانية الوصول", key="acc_open", on_click=open_page, args=("access",))


