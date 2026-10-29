"""نقطة الدخول: ربط الوحدات فقط. التشغيل:  streamlit run app.py"""
import streamlit as st

from config import PAGE_TITLE  # يحمّل .env قبل أي شيء آخر
import database as db
import system_tools
from ai_service import client
from auth import check_idle, get_auth_context
from data_layer import load_all_transactions
from floor import floor_init
from security import visible_transactions
from ui import footer, inject_prefs, inject_theme, official_footer
import views

st.set_page_config(page_title=PAGE_TITLE, page_icon="🏛️", layout="wide",
                   initial_sidebar_state="expanded")
db.init_db()
floor_init()  # منسّق الصوت: متكلم واحد فقط (المساعد / بن عبد / سعيدان / الميكروفون) — يُزرع في المتصفح مرة واحدة
try:  # نسخة احتياطية تلقائية كل 24 ساعة (لا توقف المنصة عند الفشل)
    system_tools.maybe_auto_backup()
except Exception:
    pass

# ---- سياق الدخول + البيانات (نقطة الفلترة الوحيدة) ----
ctx = get_auth_context()
if check_idle(ctx):  # انتهت الجلسة بسبب الخمول
    ctx = get_auth_context()
if st.session_state.pop("idle_notice", False):
    st.warning("⏱️ انتهت جلستك لعدم النشاط، سجّل الدخول من جديد.")
df_all = load_all_transactions()                 # كل السجلات — للمساعد (يفلتر داخلياً بحسب ctx)
df_visible = visible_transactions(df_all, ctx)   # ما يحق للمستخدم رؤيته — للواجهة

filters = views.render_sidebar(ctx, df_visible)
df_filtered = views.apply_filters(df_visible, filters)

views.render_access_bar()  # النمط + حجم الخط + التباين
inject_theme()             # ألوان النمط المختار (بعد قراءة اختيار المستخدم)
inject_prefs()             # التباين وحجم الخط
views.render_welcome(ctx, df_visible, api_ok=client is not None,
                     record_count=len(df_visible) if views.is_admin(ctx) else None)  # الواجهة الرئيسية بصورة المبنى (السجلات للمدير فقط)
views.welcome_voice(ctx)  # ترحيب صوتي يعرّف المستخدم ويراعي الوقت (مرة لكل حالة دخول)
views.render_quick_links()  # روابط تهمّك (أزرار تفتح التبويب)
st.divider()

# ---- التبويبات: (العنوان، الدالة، هل تظهر في الوضع المبسّط) ----
ALL_PAGES = [
    ("🔎 تتبّع معاملتك", lambda: views.render_tracking(ctx, df_visible), True),            # عام: بحث بالرقم الكامل
    ("🏗️ مشاريع الأمانة", lambda: views.render_projects(ctx, df_all), True),               # عام: عرض؛ للمدير إدخال وتحليل
    ("📊 لوحة التحليلات والتنفيذ", lambda: views.render_dashboard(df_filtered, df_visible, df_all, ctx), False),
    ("📝 إدخال البيانات والتحليل البصري (Vision)", lambda: views.render_intake(ctx), False),
    ("🚨 العمليات والإنذارات وغرفة GIS", lambda: views.render_gis(df_filtered), False),
    ("💬 المساعد الذكي وصانع الخطابات", lambda: views.render_assistant(df_all, ctx), True),
    ("👷 الفرق الميدانية والكاميرا الحية", lambda: views.render_field_teams(df_filtered, df_all, ctx), False),  # فيها التحليل التنبؤي (تبويب رابع)
    ("📨 الخطابات الرسمية والتقارير", lambda: views.render_official(ctx, df_all), False),
    ("🧪 جودة البيانات", lambda: views.render_quality(ctx, df_all), False),
    ("🛡️ النظام والنسخ والتدقيق", lambda: views.render_system(ctx), False),                  # للمدير
    ("⚖️ الحوكمة والامتثال والرقابة", lambda: views.render_governance(ctx), False),
    ("🚀 جاهزية المشروع والتدقيق الشامل", lambda: views.render_readiness(df_all), False),
    # ---- آخر أربعة تبويبات (بهذا الترتيب) ----
    ("🎓 التدريب والدعم", lambda: views.render_training(ctx, df_all), True),
    ("📈 بيانات مفتوحة", lambda: views.render_open_data(df_all), True),
    ("💬 رأيك يهمنا", lambda: views.render_feedback(ctx, df_all), True),
    ("🔐 الأمان والخصوصية", lambda: views.render_privacy(ctx), True),
]
view = st.session_state.get("view")
if view in views.PAGES:  # صفحة مستقلة (من الأزرار العائمة أو الروابط) بدل التبويبات
    views.render_page(view, ctx, df_all)
elif isinstance(view, str) and view.startswith("tab:"):  # قسم من أقسام التبويبات يُفتح كصفحة مستقلة (من «روابط تهمّك» أو خدماتي)
    _hit = next((p for p in ALL_PAGES if view[4:] in p[0]), None)
    if _hit is None:
        views.close_page()
    else:
        views.page_header(_hit[0])
        _hit[1]()
else:
    _basic_only = st.session_state.get("simple_mode") or not ctx.logged_in  # الزائر والوضع المبسّط: التبويبات العامة فقط (أسهل وأوضح)
    PAGES = [p for p in ALL_PAGES if p[2]] if _basic_only else ALL_PAGES
    for tab, (_, render, _) in zip(st.tabs([p[0] for p in PAGES]), PAGES):
        with tab:
            render()
    views.run_pending_tab()  # (احتياطي) فتح تبويب طلبه زر قديم

views.render_fab(ctx, df_all)  # المساعد العائم + رأيك يهمنا
official_footer(ctx)           # تذييل رسمي (رؤية 2030 + آخر تحديث)
footer()  # توقيع المطوّر Bin3abdAi أسفل كل الصفحات
