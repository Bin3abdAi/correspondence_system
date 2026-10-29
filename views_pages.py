"""الصفحات المستقلة التي تفتحها الأزرار العائمة والروابط: المساعد الكامل، إمكانية الوصول، خدماتي، الدعم، الأسئلة الشائعة.

تُعرض بدل التبويبات عند st.session_state["view"] = اسم الصفحة (انظر open_page في views_common).
"""
import uuid

from ai_service import LANGUAGES, speak_translation, translate_text, whisper_lang_code  # noqa: F401  (المترجم الصوتي)
from views_common import *  # noqa: F401,F403
from views_public import _FAQ, _GUIDE_EXTRA, _GUIDE_Q  # noqa: F401
from views_shell import _reset_access  # noqa: F401

PAGES = {"assistant": "💬 المساعد الكامل", "access": "♿ إمكانية الوصول", "services": "🧩 خدماتي",
         "support": "🛟 الدعم والتواصل", "faq": "❓ الأسئلة الشائعة", "translate": "🌍 المترجم الصوتي"}


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
    ("🎙️ الصوت", "اسأل المساعد بصوتك واستمع لردوده، واختر صوته من «⚙️ إعدادات الصوت» (الافتراضي alloy). لا يتكلم اثنان معاً: يصمت Bin3abdAi وسعيدان أثناء صوت المساعد أو تسجيلك أو كتابتك، ويمكن كتمهما بزر 🔇."),
    ("🌍 المترجم الصوتي", "تحدّث أو اكتب بأي لغة فيترجم لك فوراً ويقرأ الترجمة (Whisper للتفريغ وGPT للترجمة)."),
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
              ("🔐", "الأمان والخصوصية", "الأمان والخصوصية", "ضوابطنا وحقوقك"),
              ("🌍", "المترجم الصوتي", "page:translate", "تحدّث أو اكتب بأي لغة فتُترجم وتُقرأ لك (Whisper)")],
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
                if tab.startswith("page:"):  # خدمة صفحة مستقلة (مثل المترجم) لا قسم تبويب
                    st.button(f"افتح {name}", key=f"sv_{tab}", on_click=open_page, args=(tab[5:],), width="stretch")
                else:
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
    ("كيف أغيّر صوت المساعد؟", "من الشريط الجانبي افتح «⚙️ إعدادات الصوت» في المساعد الصوتي واختر الصوت (يبدأ بصوت alloy)، وفعّل أو أوقف الرد الصوتي من الشريط نفسه."),
    ("لماذا يصمت Bin3abdAi وسعيدان أحياناً؟", "حتى لا يتكلم اثنان معاً ولا يزعجاك: يصمتان أثناء صوت المساعد وتسجيل الميكروفون والكتابة، ويعودان بعد نحو عشرين ثانية. ويمكنك كتمهما بزر 🔇 الصغير بينهما."),
    ("كيف أترجم كلاماً أو أحدّث أجنبياً؟", "افتح «المترجم الصوتي» من الشريط السفلي أو من خدماتي: سجّل صوتك أو اكتب، واختر اللغة، فتظهر الترجمة ويقرؤها لك المساعد."),
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


# ------------------------------------------------------ 6) المترجم الصوتي (Whisper يفرّغ ← الذكاء الاصطناعي يترجم ← المساعد يقرأ)
_LANG_AR = {"ar": "العربية", "en": "الإنجليزية", "ur": "الأردية", "hi": "الهندية", "bn": "البنغالية", "tl": "الفلبينية",
            "id": "الإندونيسية", "tr": "التركية", "fr": "الفرنسية", "es": "الإسبانية", "fa": "الفارسية", "ru": "الروسية",
            "zh": "الصينية", "ml": "المالايالامية", "ta": "التاميلية"}
_RTL_LANGS = {"ar", "ur", "fa"}  # لغات تُكتب من اليمين لليسار
_AUTO = "auto"
_TR_LIMIT = {True: 200, False: 40}  # أقصى عدد ترجمات للجلسة: المسجّل / الزائر (حماية التكلفة)
_TR_MAX = 1500  # أقصى طول للنص المكتوب
_AR_CH = re.compile(r"[؀-ۿ]")
_LETTER = re.compile(r"[^\W\d_]")


def _lang_label(code: str) -> str:  # اسم اللغة بالعربية (+ كتابتها بلغتها)
    if code == _AUTO:
        return "🔎 تلقائي — Whisper يكتشف اللغة"
    native = LANGUAGES.get(code, (code, code))[0]
    ar = _LANG_AR.get(code, native)
    return ar if native == ar else f"{ar} — {native}"


def _arabic_ratio(text: str) -> float:  # نسبة الحروف العربية بين حروف النص
    letters = _LETTER.findall(text or "")
    return len(_AR_CH.findall(text or "")) / len(letters) if letters else 0.0


def _direction(text: str, det: str, other: str) -> tuple:
    """وضع المحادثة الثنائية (عربي ⇄ لغة أخرى): يُرجع (لغة المصدر المرجّحة أو فارغ، لغة الهدف).
    det = اللغة التي حدّدها Whisper من الصوت إن وُجدت."""
    if det:
        return (det, other) if det == "ar" else (det, "ar")
    if other in ("ur", "fa"):
        return "", other  # الخط العربي مشترك مع الأردية والفارسية: نترك النموذج يكتشف ثم نصحّح الاتجاه بعد الترجمة
    if _arabic_ratio(text) >= 0.5:
        return "ar", other
    return "", "ar"


def _do_translate(text: str, mode: str, src: str, tgt: str, other: str, det: str = "") -> dict:
    """يترجم ويُرجع {"orig","out","src","tgt"} أو {"error"}. mode: two = محادثة ثنائية، one = اتجاه واحد."""
    if mode == "two":
        s_hint, t = _direction(text, det, other)
    else:
        s_hint = det or ("" if src == _AUTO else src)
        t = tgt
    r = translate_text(text, t, s_hint)
    if r.get("error"):
        return r
    got = r.get("src") or s_hint
    if mode == "two" and t == other and got == other:  # المتكلم بلغة «الأخرى» (حالة الخط المشترك): الاتجاه للعربية
        r2 = translate_text(text, "ar", other)
        if r2.get("error"):
            return r2
        return {"orig": text, "out": r2["text"], "src": other, "tgt": "ar"}
    return {"orig": text, "out": r["text"], "src": got, "tgt": t}


def _tr_swap() -> None:  # زر ⇄ : يبدّل لغتي المصدر والهدف (callback قبل رسم الحقول)
    s, t = st.session_state.get("tr_src", _AUTO), st.session_state.get("tr_tgt", "en")
    st.session_state["tr_src"] = t
    st.session_state["tr_tgt"] = s if s != _AUTO else ("ar" if t != "ar" else "en")


def _tr_run(text: str, ctx: AuthContext, det: str = "") -> bool:
    """يترجم النص ويحفظ النتيجة (وقراءتها الصوتية) في سجل الجلسة. يُرجع True عند النجاح."""
    done = st.session_state.get("tr_count", 0)
    if done >= _TR_LIMIT[bool(ctx.logged_in)]:
        st.warning("وصلت للحد التجريبي من الترجمات في هذه الجلسة. حدّث الصفحة لبدء جلسة جديدة، أو سجّل الدخول لحدّ أعلى.")
        return False
    mode = st.session_state.get("tr_mode", "two")
    with st.spinner("🌍 جارٍ الترجمة…"):
        res = _do_translate(text.strip()[:_TR_MAX], mode, st.session_state.get("tr_src", _AUTO), st.session_state.get("tr_tgt", "en"),
                            st.session_state.get("tr_other", "en"), det)
    if res.get("error"):
        st.error(res["error"])
        return False
    entry = dict(res, id=uuid.uuid4().hex[:8], audio=b"")
    if st.session_state.get("tr_speak", True):
        with st.spinner("🔊 أجهّز القراءة الصوتية…"):
            try:
                entry["audio"] = speak_translation(res["out"][:1200], res["tgt"]) or b""
            except Exception:
                entry["audio"] = b""
    hist = st.session_state.setdefault("tr_hist", [])
    hist.insert(0, entry)
    for old in hist[3:]:  # الصوت لآخر ثلاث ترجمات فقط (يخفّف حجم الصفحة)
        old["audio"] = b""
    del hist[10:]
    st.session_state["tr_count"] = done + 1
    audit("translate", ctx, src=res["src"], tgt=res["tgt"], chars=len(text))  # بلا محتوى النص (خصوصية)
    return True


def _tr_voice(raw: bytes, ctx: AuthContext) -> bool:  # تسجيل صوتي ← Whisper ← ترجمة
    mode, src = st.session_state.get("tr_mode", "two"), st.session_state.get("tr_src", _AUTO)
    lang = src if (mode == "one" and src != _AUTO) else ""  # لغة معروفة تُحسّن الدقة؛ غير ذلك يكتشفها Whisper
    with st.spinner("🎧 Whisper يفرّغ كلامك…"):
        r = transcribe_audio(raw, "translate.wav", language=lang, hint=None if lang else "")  # بلا تلميح عربي عند اكتشاف اللغة تلقائياً
    if r.get("error"):
        st.error(r["error"])
        return False
    text = (r.get("text") or "").strip()
    if not text:
        st.warning("🎙️ لم أسمع كلاماً واضحاً. قرّب الميكروفون وتحدّث بصوت أعلى قليلاً ثم أعد المحاولة.")
        return False
    return _tr_run(text, ctx, whisper_lang_code(r.get("lang", "")))


def _tr_show(e: dict, latest: bool, ctx: AuthContext) -> None:  # بطاقة ترجمة: الأصل + الترجمة + قراءة صوتية + مشاركة
    s, t = e.get("src") or "", e.get("tgt") or ""
    d = lambda c: "rtl" if c in _RTL_LANGS else "ltr"
    st.markdown(f"**{html.escape(_lang_label(s)) if s else 'لغة النص'}** ⟵ **{html.escape(_lang_label(t))}**")
    c1, c2 = st.columns(2)
    with c1:
        card(f"<div style='font-size:.8rem;opacity:.8;margin-bottom:6px'>النص الأصلي</div>"
             f"<div dir='{d(s)}' style='font-size:1.05rem;line-height:2;white-space:pre-wrap'>{html.escape(e['orig'])}</div>", "glass")
    with c2:
        card(f"<div style='font-size:.8rem;opacity:.8;margin-bottom:6px'>الترجمة</div>"
             f"<div dir='{d(t)}' style='font-size:1.15rem;font-weight:700;line-height:2;white-space:pre-wrap'>{html.escape(e['out'])}</div>", "ok")
    if e.get("audio"):
        play_audio(e["audio"], autoplay=latest, label="اقرأ الترجمة", token=e["id"], prio=2)  # تُقرأ مرة واحدة تلقائياً، ويعيدها الزر
    if latest:
        with st.expander("📤 مشاركة الترجمة أو إرسالها (واتساب • رسالة • بريد)"):
            to = st.text_input("إلى (اختياري): رقم جوال 05XXXXXXXX أو بريد", key="tr_to", placeholder="05XXXXXXXX أو name@example.com").strip()
            msg = f"{e['orig']}\n⟵ {e['out']}"
            lk = notifier.share_links(msg, "ترجمة من منصة أمانة محافظة جدة", to)
            b1, b2, b3 = st.columns(3)
            with b1:
                link_btn("💬 واتساب", lk["whatsapp"])
            with b2:
                link_btn("📱 رسالة نصية", lk["sms"])
            with b3:
                link_btn("✉️ بريد", lk["mailto"])
            if to and not (notifier.normalize_phone(to) or notifier.valid_email(to)):
                st.caption("⚠️ الصيغة غير مفهومة: اكتب جوالاً سعودياً مثل 0555123456 أو بريداً صحيحاً.")
            if ctx.logged_in and (notifier.normalize_phone(to) or notifier.valid_email(to)):
                if st.button("📨 أرسل من المنصة مباشرة", key="tr_send", width="stretch",
                             help="يستخدم إعدادات البريد SMTP أو بوابة الرسائل المضبوطة في ملف .env"):
                    ok, info = notifier.notify(to, "ترجمة من منصة أمانة محافظة جدة", msg, ctx)
                    (st.success if ok else st.warning)(info)
            elif not ctx.logged_in:
                st.caption("الإرسال المباشر من المنصة للموظفين المسجّلين، أما الأزرار أعلاه فتفتح تطبيقاتك أنت.")
            st.code(e["out"], language=None)  # زر النسخ يظهر في زاوية المربع


def _page_translate(ctx: AuthContext) -> None:  # المترجم الصوتي: تحدّث أو اكتب بأي لغة ← ترجمة فورية بصوت المساعد
    card("🌍 <b>المترجم الصوتي الفوري</b><br>تحدّث بصوتك أو اكتب بأي لغة: <b>Whisper</b> يفرّغ كلامك، والذكاء الاصطناعي يترجمه، "
         "والمساعد يقرؤه لك بصوته. مفيد للتواصل مع المراجعين والعمالة والزوّار بلغاتهم.", "banner")
    if client is None:
        card("⚠️ المترجم يحتاج مفتاح OpenAI (OPENAI_API_KEY) في ملف .env لتفعيل Whisper والترجمة والقراءة الصوتية.", "warn")
        return
    st.radio("طريقة الترجمة", ["two", "one"], key="tr_mode", horizontal=True,
             format_func=lambda m: "🔁 محادثة ثنائية: عربي ⇄ لغة أخرى (يميّز لغتك تلقائياً)" if m == "two" else "➡️ اتجاه واحد: من لغة إلى لغة")
    langs = list(LANGUAGES)
    if st.session_state.get("tr_mode", "two") == "two":
        st.selectbox("اللغة الأخرى في المحادثة", [c for c in langs if c != "ar"], key="tr_other", format_func=_lang_label)
        st.caption("تحدّث بالعربية فتُترجم للغة الأخرى، وإذا تحدّث الطرف الآخر بلغته ترجمتُه لك بالعربية.")
    else:
        a, b, c = st.columns([5, 1, 5])
        a.selectbox("من", [_AUTO] + langs, key="tr_src", format_func=_lang_label)
        b.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
        b.button("⇄", key="tr_swap", on_click=_tr_swap, help="بدّل اللغتين")
        st.session_state.setdefault("tr_tgt", "en")  # القيمة الافتراضية عبر الحالة لا index (لا تحذير عند زر التبديل)
        c.selectbox("إلى", langs, key="tr_tgt", format_func=_lang_label)
    st.toggle("🔊 اقرأ الترجمة بصوت المساعد", value=True, key="tr_speak")

    n_rec = st.session_state.get("tr_rec_n", 0)  # رقم المسجّل: يزيد بعد كل ترجمة فيعود المسجّل فارغاً للتسجيل التالي
    aud = st.audio_input("🎙️ سجّل صوتك ثم أوقف التسجيل لتبدأ الترجمة تلقائياً", key=f"tr_audio_{n_rec}")
    st.caption("إن ظهرت رسالة خطأ في المسجّل فاسمح للمتصفح باستخدام الميكروفون (أيقونة القفل 🔒 بجانب عنوان الصفحة ثم الميكروفون ← سماح).")
    if aud is not None:
        raw = aud.getvalue()
        sig = hashlib.md5(raw).hexdigest()
        if st.session_state.get("tr_sig") != sig:  # تسجيل جديد فقط (لا إعادة معالجة مع كل تحديث للصفحة)
            st.session_state["tr_sig"] = sig
            if _tr_voice(raw, ctx):
                st.session_state["tr_rec_n"] = n_rec + 1
                st.rerun()

    with st.form("tr_form", clear_on_submit=False):
        txt = st.text_area("✍️ أو اكتب النص هنا", key="tr_text", height=110, max_chars=_TR_MAX, placeholder="اكتب أو الصق نصاً بأي لغة…")
        go = st.form_submit_button("🌍 ترجم النص", width="stretch")
    if go:
        if not txt.strip():
            st.warning("اكتب نصاً أولاً.")
        else:
            _tr_run(txt, ctx)

    hist = st.session_state.get("tr_hist", [])
    if hist:
        st.divider()
        _tr_show(hist[0], True, ctx)
        r1, r2 = st.columns(2)
        if r1.button("🔄 أعد ترجمة آخر نص بالإعدادات الحالية", key="tr_redo", width="stretch"):
            _tr_run(hist[0]["orig"], ctx)
            st.rerun()
        if r2.button("🗑️ امسح السجل", key="tr_clear", width="stretch"):
            st.session_state["tr_hist"] = []
            st.rerun()
        if len(hist) > 1:
            with st.expander(f"🕘 الترجمات السابقة ({len(hist) - 1})"):
                for e in hist[1:]:
                    _tr_show(e, False, ctx)
                    st.divider()
    st.caption("المترجم أداة مساعدة: راجع الترجمة في المحتوى الرسمي أو الحساس قبل اعتمادها. لا نحفظ تسجيلاتك الصوتية.")


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
    elif name == "translate":
        _page_translate(ctx)
    else:
        _page_faq(ctx)
