"""هيكل الصفحة: الشريط الجانبي وتسجيل الدخول وتنبيهات SLA والفلاتر وزر إمكانية الوصول."""
import time

import notion_meetings
from config import CONFIDENTIALITY_LEVELS  # ترتيب مستويات السرية في الفلتر
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


def _sla_panel(ctx: AuthContext, df: pd.DataFrame) -> None:  # تنبيه مبكر: المعاملات المتأخرة والمستحقة خلال 24 ساعة ضمن نطاق صلاحية المستخدم
    """تنبيه مبكر: المعاملات المتأخرة والمستحقة خلال 24 ساعة ضمن نطاق صلاحية المستخدم."""
    st.markdown("### ⏰ تنبيهات مهلة الإنجاز (SLA)")
    ck = (ctx.role, ctx.department, len(df))
    cache = st.session_state.get("_sla_cache")
    if not cache or cache[0] != ck or time.time() - cache[1] > 120:  # نعيد الحساب كل دقيقتين أو عند تغيّر البيانات
        cache = (ck, time.time(), an.sla_summary(df))
        st.session_state["_sla_cache"] = cache
    sla = cache[2]
    c1, c2 = st.columns(2)
    c1.metric("🔴 متأخرة", f"{sla['overdue']:,}")
    c2.metric("🟠 خلال 24 ساعة", f"{sla['soon']:,}")
    if sla["overdue"] == 0 and sla["soon"] == 0:
        st.success("لا توجد معاملات متأخرة أو قريبة الاستحقاق.")
        return
    with st.expander("التفاصيل حسب الإدارة"):
        st.dataframe(sla["by_dept"], hide_index=True, width="stretch")
        if not sla["worst"].empty:
            st.caption("أقدم المتأخرات:")
            st.dataframe(sla["worst"], hide_index=True, width="stretch")
    if ctx.role in ("admin", "manager"):  # إرسال التنبيه بالبريد لمن يتابع الإنجاز
        to = get_setting("SLA_ALERT_EMAIL") or get_setting("ADMIN_2FA_EMAIL")
        if st.button("📧 إرسال ملخص التنبيه بالبريد", key="sla_mail", width="stretch"):
            if not to:
                st.warning("ضع SLA_ALERT_EMAIL في ملف .env لتحديد المستلم.")
            else:
                scope = ctx.department or "كل الإدارات"
                txt = (f"النطاق: {scope}\nمعاملات متأخرة: {sla['overdue']:,}\nتستحق خلال 24 ساعة: {sla['soon']:,}\n\n"
                       + sla["by_dept"].to_string(index=False))
                ok, msg = notifier.notify(to, "تنبيه مهلة الإنجاز SLA", txt, ctx)
                (st.success if ok else st.error)(msg)
                audit("sla_alert_sent", ctx, ok=ok)


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


def _filters_panel(df: pd.DataFrame) -> dict:  # فلاتر الحي والقطاع والأهمية والسرية (السرية تظهر خياراتها بحسب صلاحية المستخدم)
    st.markdown("### 🔍 فلاتر البحث والتحليل اللحظي")
    out = {}
    for col, label in _FILTER_COLUMNS.items():
        if col not in df.columns:  # عمود غير موجود في هذه البيانات: نتجاوزه بدل أن ينهار الفلتر
            continue
        out[col] = st.selectbox(label, [ALL_LABEL, *_filter_options(df, col)], key=f"flt_{col}")
    return out


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:  # يطبّق الفلاتر المختارة على الجدول
    for col, value in filters.items():
        if value != ALL_LABEL:
            df = df[df[col] == value]
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
        e6.toggle("🔔 أصوات تقنية", key="ui_sounds", help="أصوات خفيفة عند التفاعل مع توني وسعيدان")
        e7.toggle("🗣️ نطق الشخصيتين", key="chars_voice", help="ينطق توني وسعيدان كلامهما بصوت عربي (بعد أول نقرة في الصفحة)")
        st.button("↺ إعادة الضبط", key="acc_reset", on_click=_reset_access)
        st.button("♿ صفحة إمكانية الوصول", key="acc_open", on_click=open_page, args=("access",))


