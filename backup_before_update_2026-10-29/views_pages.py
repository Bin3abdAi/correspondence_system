"""الصفحات المستقلة التي تفتحها الأزرار العائمة والروابط: المساعد الكامل، إمكانية الوصول، خدماتي، الدعم، الأسئلة الشائعة.

تُعرض بدل التبويبات عند st.session_state["view"] = اسم الصفحة (انظر open_page في views_common).
"""
from views_common import *  # noqa: F401,F403
from views_public import _FAQ, _GUIDE_EXTRA, _GUIDE_Q  # noqa: F401
from views_shell import _reset_access  # noqa: F401

PAGES = {"assistant": "💬 المساعد الكامل", "access": "♿ إمكانية الوصول", "services": "🧩 خدماتي",
         "support": "🛟 الدعم والتواصل", "faq": "❓ الأسئلة الشائعة"}


def _role_key(ctx: AuthContext) -> str:  # أدوار الموظفين (موظف/مدير إدارة/مراجع) تأخذ مسار الموظف
    """أدوار الموظفين (موظف/مدير إدارة/مراجع) تأخذ مسار الموظف."""
    return "admin" if is_admin(ctx) else ("employee" if ctx.logged_in else "guest")


# ------------------------------------------------------ 1) المساعد الكامل
_FULL_EXTRA = ("أنت في صفحة المساعد الكامل: أجب بتفصيل مرتّب بعناوين قصيرة وخطوات عند الحاجة. إن طُلب تحليل فقدّم تحليلاً كاملاً "
               "بأرقام من البيانات المتاحة فقط، وإن طُلب مشروع فاذكر الأهمية والأولوية وأثره على رؤية 2030 (والطرق مهمة جداً). "
               "ممنوع ذكر تاريخ تدريبك أو أنك نموذج. وجّه المستخدم لاسم التبويب أو الزر بالضبط.")


def _page_assistant(ctx: AuthContext, df_all: pd.DataFrame) -> None:  # صفحة المساعد الكامل: محادثة نص وصوت مع بث الرد
    card(("🔓 مسجّل: " + html.escape(ctx.username or "") + f" ({html.escape(ctx.role_label)}) — يصل المساعد للمستويات: " + "، ".join(ctx.visible_levels))
         if ctx.logged_in else "🔒 أنت زائر: يصل المساعد إلى المعاملات العامة فقط.", "ok" if ctx.logged_in else "warn")
    st.markdown("**أسئلة سريعة:**")
    qs = _GUIDE_Q[_role_key(ctx)] + ["حلّل لي وضع المشاريع وأولوياتها"]
    cols = st.columns(2)
    for i, q in enumerate(qs):
        cols[i % 2].button("❓ " + q, key=f"fq{i}", on_click=lambda t=q: st.session_state.__setitem__("full_q", t), width="stretch")
    hist = st.session_state.setdefault("full_hist", [])
    for i, m in enumerate(hist):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    q = st.session_state.pop("full_q", None) or st.chat_input("اكتب سؤالك أو اطلب تحليلاً أو خطاباً…", key="full_chat")
    fa = st.audio_input("🎙️ أو تحدّث", key="full_audio")
    if fa is not None and not q:
        raw = fa.getvalue()
        sig = hashlib.md5(raw).hexdigest()
        if st.session_state.get("full_sig") != sig:
            st.session_state["full_sig"] = sig
            q = transcribe_audio(raw, "full.wav").get("text") or None
    if q:
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            ans = st.write_stream(ask_assistant_stream(q, hist, ctx, df_all, extra_system=_FULL_EXTRA + " " + _GUIDE_EXTRA))
        ans = ans if isinstance(ans, str) else "".join(map(str, ans))
        speak_now(ans)
        hist += [{"role": "user", "content": q}, {"role": "assistant", "content": ans}]
        del hist[:-20]
    if hist and st.button("🗑️ محادثة جديدة", key="full_clear"):
        st.session_state["full_hist"] = []
        st.rerun()
    last = next((m["content"] for m in reversed(hist) if m["role"] == "assistant"), "")
    if last and not last.startswith(("❌", "⚠️")):
        export_bar("assistant_full", "رد المساعد الذكي", ctx, text=last)


# ------------------------------------------------------ 2) إمكانية الوصول
_ACC_ROWS = [
    ("🎨 الأنماط الأربعة", "داكن رسمي، وثلاثة أنماط فاتحة هادئة (أخضر هادئ، رملي مريح للعين، أزرق بحري)، بلا نجوم ولا حركة مزعجة."),
    ("🔠 حجم الخط", "عادي وكبير وأكبر، يكبّر الصفحة كلها."),
    ("◐ التباين العالي", "ألوان أوضح للنص والحدود لضعاف البصر."),
    ("🅰️ خط أوضح", "خط بسيط مألوف بديلاً عن الخط الزخرفي."),
    ("↕️ مسافات أوسع", "يوسّع المسافة بين الأسطر لسهولة القراءة."),
    ("🔗 تمييز الروابط", "تسطير الروابط وتثخينها."),
    ("🧘 إيقاف الحركة", "يوقف النجوم والمجرة وحركة الشخصيتين لمن تزعجه الحركة."),
    ("🎙️ الصوت", "اسأل المساعد بصوتك واستمع لردوده؛ ويمكنك اختيار صوت توني أو سعيدان."),
]


def _preset_comfort() -> None:  # إعداد جاهز: قراءة مريحة
    st.session_state.update({"font_scale": "كبير", "plain_font": True, "big_spacing": True, "mark_links": True})


def _preset_contrast() -> None:  # إعداد جاهز: تباين عالٍ
    st.session_state.update({"high_contrast": True, "font_scale": "كبير", "mark_links": True})


def _preset_calm() -> None:  # إعداد جاهز: بلا حركة
    st.session_state.update({"reduce_motion": True, "show_chars": False})


def _page_access(ctx: AuthContext) -> None:  # صفحة إمكانية الوصول وشرح الخيارات
    card("نهدف أن تكون المنصة قابلة للاستخدام للجميع بمن فيهم كبار السن وذوو الإعاقة البصرية والحركية. "
         "نراعي مبادئ إرشادات WCAG 2.1 (المستوى AA) في التباين والخطوط والتنقل بلوحة المفاتيح، "
         "ولم يُجرَ بعد تدقيق رسمي مستقل، وملاحظاتك تساعدنا على التحسين.", "banner")
    st.markdown("#### ⚡ إعدادات جاهزة بضغطة")
    c1, c2, c3, c4 = st.columns(4)
    c1.button("👓 قراءة مريحة", on_click=_preset_comfort, width="stretch", key="pa1")
    c2.button("◐ تباين عالٍ", on_click=_preset_contrast, width="stretch", key="pa2")
    c3.button("🧘 هدوء (بلا حركة)", on_click=_preset_calm, width="stretch", key="pa3")
    c4.button("↺ إعادة الضبط", on_click=_reset_access, width="stretch", key="pa4")
    st.caption("للتحكم الدقيق افتح الزر الأخضر ♿ أسفل الصفحة.")
    st.markdown("#### ما الذي يتوفر؟")
    for a, b in _ACC_ROWS:
        st.markdown(f"**{a}:** {b}")
    st.markdown("#### ⌨️ التنقل بلوحة المفاتيح")
    st.markdown("- **Tab** للانتقال بين العناصر، و**Shift+Tab** للرجوع.\n- **Enter** أو **المسافة** لتفعيل الزر.\n- **Ctrl +** و**Ctrl −** لتكبير الصفحة أو تصغيرها في المتصفح.")
    st.markdown("#### 🗣️ واجهت صعوبة؟")
    with st.form("acc_issue", clear_on_submit=True):
        txt = st.text_area("صف الصعوبة", max_chars=1200)
        contact = st.text_input("وسيلة تواصل (اختياري)")
        if st.form_submit_button("📤 إرسال", width="stretch"):
            if len(txt.strip()) < 10:
                st.error("اكتب وصفاً أوضح.")
            else:
                ref = save_ticket("دعم", "ملاحظة إمكانية وصول", txt, ctx.username or "زائر", ctx.role, contact)
                audit("accessibility_report", ctx, ref=ref)
                st.success(f"وصلتنا ملاحظتك، رقمها **{ref}**.")


# ------------------------------------------------------ 3) خدماتي
_SERV = {
    "guest": [("🔎", "تتبّع معاملتك", "تتبّع معاملتك", "اعرف حالة معاملتك بالرقم أو بصوتك"),
              ("🏗️", "مشاريع الأمانة", "مشاريع الأمانة", "المشاريع المنفّذة وقيد التنفيذ والمقترحة"),
              ("📈", "بيانات مفتوحة", "بيانات مفتوحة", "أرقام مجمّعة آمنة للجميع"),
              ("🎓", "التدريب والدعم", "التدريب والدعم", "مرشد ومساعدة وتذاكر دعم"),
              ("💬", "رأيك يهمنا", "رأيك يهمنا", "قيّم المنصة وشاركنا ملاحظتك"),
              ("🔐", "الأمان والخصوصية", "الأمان والخصوصية", "ضوابطنا وحقوقك")],
    "employee": [("📝", "إدخال البيانات", "إدخال البيانات", "بلاغ بصورة أو إدخال يدوي أو ملفات"),
                 ("👷", "الفرق الميدانية", "الفرق الميدانية", "التكليف والتقارير الميدانية"),
                 ("📨", "الخطابات الرسمية", "الخطابات الرسمية", "صياغة وإرسال وتصدير"),
                 ("💬", "المساعد الذكي", "المساعد الذكي", "اسأل وصُغ خطاباً")],
    "admin": [("📊", "لوحة التحليلات", "لوحة التحليلات", "مؤشرات الأداء والتوقعات"),
              ("🚨", "العمليات وGIS", "العمليات والإنذارات", "الإنذارات والخرائط الحية"),
              ("🧪", "جودة البيانات", "جودة البيانات", "اكتشاف الخلل والتكرار"),
              ("🛡️", "النظام والتدقيق", "النظام والنسخ", "النسخ الاحتياطي وسجل التدقيق"),
              ("⚖️", "الحوكمة", "الحوكمة", "الامتثال والرقابة"),
              ("🚀", "الجاهزية", "جاهزية المشروع", "فحص شامل قبل الإطلاق")],
}


def _page_services(ctx: AuthContext) -> None:  # صفحة خدماتي: بطاقات الخدمات حسب الدور
    st.caption("كل الخدمات المتاحة لدورك، اضغط الخدمة لتفتحها.")
    role = _role_key(ctx)
    groups = [("🌐 خدمات الجميع", _SERV["guest"])]
    if role in ("employee", "admin"):
        groups.append(("👥 خدمات الموظفين" + (f" ({ctx.role_label})" if ctx.logged_in else ""), _SERV["employee"]))
    if role == "admin":
        groups.append(("🛡️ خدمات المدير", _SERV["admin"]))
    for title, items in groups:
        st.markdown(f"#### {title}")
        cols = st.columns(3)
        for i, (ic, name, tab, desc) in enumerate(items):
            with cols[i % 3]:
                card(f"<b>{ic} {html.escape(name)}</b><br><span style='opacity:.85'>{html.escape(desc)}</span>", "glass")
                st.button(f"افتح {name}", key=f"sv_{tab}", on_click=go_tab, args=(tab,), width="stretch")
    if not ctx.logged_in:
        card("🔑 للموظفين: سجّل الدخول من الشريط الجانبي لتظهر خدماتك.", "warn")


# ------------------------------------------------------ 4) الدعم والتواصل
def _page_support(ctx: AuthContext) -> None:  # صفحة الدعم والتواصل وتذاكر الدعم
    phone, mail = get_setting("CONTACT_PHONE"), get_setting("CONTACT_EMAIL")
    c1, c2, c3 = st.columns(3)
    with c1:
        card(f"📞 <b>الهاتف</b><br>{html.escape(phone) if phone else 'يُضاف في الإطلاق الرسمي'}", "glass")
    with c2:
        card(f"✉️ <b>البريد</b><br>{html.escape(mail) if mail else 'يُضاف في الإطلاق الرسمي'}", "glass")
    with c3:
        card("🕗 <b>ساعات الدعم</b><br>الأحد إلى الخميس، 8 ص – 4 م", "glass")
    t1, t2 = st.tabs(["🎫 تذكرة جديدة", "🔎 متابعة تذكرة"])
    with t1:
        with st.form("sup2_form", clear_on_submit=True):
            kind = st.selectbox("النوع", ["مشكلة تقنية", "استفسار", "اقتراح", "ملاحظة على الخدمة"])
            sub = st.text_input("الموضوع", max_chars=120)
            txt = st.text_area("التفاصيل", max_chars=1500)
            contact = st.text_input("وسيلة تواصل للرد (اختياري)")
            if st.form_submit_button("📤 إرسال", width="stretch"):
                if len(txt.strip()) < 10 or not sub.strip():
                    st.error("اكتب الموضوع ووصفاً أوضح.")
                else:
                    ref = save_ticket("دعم", f"{kind}: {sub}", txt, ctx.username or "زائر", ctx.role, contact)
                    audit("support_ticket", ctx, ref=ref)
                    st.success(f"فُتحت تذكرتك رقم **{ref}**، احتفظ به للمتابعة.")
    with t2:
        ref = st.text_input("رقم التذكرة", placeholder="SUP-2026-0001", key="sup2_ref")
        if ref:
            t = find_ticket(ref)
            st.info(f"الحالة: {t['status']}" + (f" — {t['reply']}" if t and t.get("reply") else "") if t else "لا توجد تذكرة بهذا الرقم.")
    st.markdown("**قبل فتح تذكرة:** جرّب **الأسئلة الشائعة** أو اسأل المساعد، فغالباً تجد الجواب في ثوانٍ.")
    b1, b2 = st.columns(2)
    b1.button("❓ الأسئلة الشائعة", key="sp_faq", on_click=open_page, args=("faq",), width="stretch")
    b2.button("💬 اسأل المساعد", key="sp_as", on_click=open_page, args=("assistant",), width="stretch")


# ------------------------------------------------------ 5) الأسئلة الشائعة
_FAQ_MORE = [
    ("كيف أعرف المعاملات المتأخرة؟", "للموظفين والمدير: صندوق «تنبيهات مهلة الإنجاز» في الشريط الجانبي يعرض المتأخر والمستحق خلال 24 ساعة."),
    ("ما الفرق بين الموظف ومدير الإدارة والمراجع؟", "الموظف يعمل على كل المعاملات المسموحة له، ومدير الإدارة يرى معاملات إدارته فقط، والمراجع يقرأ فقط دون تعديل."),
    ("لماذا يطلب مني رمز تحقق عند دخول المدير؟", "حماية إضافية (تحقق ثنائي) حتى لو سُرّبت كلمة المرور."),
    ("كيف أغيّر شكل المنصة أو حجم الخط؟", "اضغط الزر الأخضر ♿ أسفل اليمين، أو افتح صفحة إمكانية الوصول."),
    ("هل تُحفظ محادثاتي مع المساعد؟", "تبقى في جلستك فقط وتُمسح عند تسجيل الخروج أو تغيّر الصلاحية، وتُسجَّل الأسئلة في سجل التدقيق لأغراض الرقابة."),
    ("كيف أغيّر صوت المساعد؟", "من زر ♿ اختر «من يتحدث معك؟» بين توني وسعيدان، وفعّل أو أوقف الرد الصوتي من الشريط الجانبي."),
    ("هل أستطيع تصدير ما أراه؟", "نعم، في أسفل الصفحات شريط التصدير: طباعة وPDF وCSV وإرسال بالبريد حسب صلاحيتك."),
]


def _page_faq(ctx: AuthContext) -> None:  # صفحة الأسئلة الشائعة مع بحث
    q = st.text_input("🔍 ابحث في الأسئلة", key="faq_q", placeholder="اكتب كلمة مثل: معاملة، صوت، خصوصية").strip()
    allq = _FAQ + _FAQ_MORE
    hits = [(a, b) for a, b in allq if not q or q in a or q in b]
    for a, b in hits:
        with st.expander(a):
            st.write(b)
    if not hits:
        card("ما وجدنا سؤالاً مطابقاً، اسأل المساعد مباشرة.", "warn")
    if q:
        st.button(f"💬 اسأل المساعد: «{q[:40]}»", key="faq_ask", on_click=open_page, args=("assistant", q), width="stretch")
    st.button("🛟 لم تجد جوابك؟ افتح تذكرة", key="faq_tk", on_click=open_page, args=("support",), width="stretch")


# ------------------------------------------------------ الموجّه
def page_header(title: str) -> None:  # رأس موحّد لأي صفحة مستقلة: زر رجوع + عنوان + تمرير الشاشة إليها
    """رأس موحّد لأي صفحة مستقلة: زر رجوع + عنوان + تمرير الشاشة إليها."""
    st.button("← رجوع للمنصة", key="pg_back", on_click=close_page)
    st.markdown(f"### {title}")
    scroll_to_page()


def render_page(name: str, ctx: AuthContext, df_all: pd.DataFrame) -> None:  # يعرض الصفحة المستقلة مع زر رجوع؛ يستدعيه app.py حين يكون st.session_state['vie
    """يعرض الصفحة المستقلة مع زر رجوع؛ يستدعيه app.py حين يكون st.session_state['view'] مضبوطاً."""
    page_header(PAGES[name])
    if name == "assistant":
        _page_assistant(ctx, df_all)
    elif name == "access":
        _page_access(ctx)
    elif name == "services":
        _page_services(ctx)
    elif name == "support":
        _page_support(ctx)
    else:
        _page_faq(ctx)
