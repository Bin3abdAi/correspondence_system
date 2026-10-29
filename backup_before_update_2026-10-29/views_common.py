"""مشترك بين كل الجماهير: الاستيرادات والأدوات والمكوّنات المشتركة."""
"""واجهات الصفحات: كل تبويب دالة مستقلة تستقبل (البيانات, سياق الدخول)."""

import base64

import datetime

import hashlib

import html

import io

import json

import re

from pathlib import Path

import pandas as pd

import streamlit as st

import streamlit.components.v1 as components

import analytics as an

import notifier

import system_tools as sx

import charts

import database as db

from ai_service import (PERSONAS, analyze_feedback, analyze_project_full, analyze_image_json, ask_assistant, ask_assistant_stream, ask_sovereign_ai, feedback_mood, feedback_reply,
                        classify_municipal_batch, client, estimate_cost_effort, estimate_project_success, extract_transactions_ai,
                        generate_concept_image, spoken_version, suggest_projects, synthesize_speech,
                        transcribe_audio)

from auth import cancel_2fa, get_auth_context, login, logout, pending_2fa, verify_2fa

from config import (ALL_LABEL, APP_NAME, DEVELOPER_SIGNATURE, APP_TAGLINE, APP_VERSION, DEPARTMENTS, DISTRICT_COORDS, DISTRICTS, PRIORITIES,
                    STATUS_DONE, STATUS_FIELD, STATUSES, TARGET_COMPLETION_RATE, get_setting)

from data_layer import (find_feedback, find_ticket, load_academy, load_feedback, save_academy, save_feedback, save_ticket,
                        update_feedback, MAX_IMPORT_ROWS, apply_municipal_flags, delete_projects, load_all_transactions,
                        hijri_text, load_assignments, load_field_reports, load_issues, load_projects, load_rating,
                        next_outgoing_no, normalize_columns,
                        project_image_path, revert_project, rule_municipal, save_assignment, save_field_report, save_project,
                        save_issue, save_project_image, save_project_versioned, save_rating, validate_import)

from exports import csv_bytes, export_bar, pdf_bytes, play_audio, show_reply, speak_button, voice_toggle

from security import GUEST, AuthContext, audit, visible_transactions

from ui import THEMES, card, companions, dock_buttons, nav_buttons, recolor, theme_palette

try:
    from voice_assistant import render_voice_assistant_widget
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

    def render_voice_assistant_widget():  # بديل فارغ إن غاب المساعد الصوتي
        pass



def _frame(page: str, height: int) -> None:  # يعرض صفحة HTML مضمّنة
    """يعرض صفحة HTML مضمّنة. الافتراضي components.html (يعمل الآن مع تحذير إهمال)؛
    ضع USE_ST_IFRAME=1 في .env لتجربة st.iframe الجديد، ويرجع تلقائياً للقديم عند أي فشل."""
    page = recolor(page)  # أخضر وذهبي موحّد في كل الإطارات
    if get_setting("USE_ST_IFRAME", "0") == "1" and hasattr(st, "iframe"):
        try:
            st.iframe(page, height=height)
            return
        except Exception:
            pass
    components.html(page, height=height)


def is_admin(ctx: AuthContext) -> bool:  # المدير فقط (الموظف والزائر لا)
    """المدير فقط (الموظف والزائر لا). كل المحتوى الحساس يمرّ من هنا."""
    return bool(ctx.logged_in and ctx.role == "admin")


def _admin_gate(ctx: AuthContext, what: str) -> bool:  # يرجع True للمدير
    """يرجع True للمدير. غيره يرى بطاقة قفل ولا يُحسب أو يُعرض أي رقم من الصفحة (نخرج قبل الحساب)."""
    if is_admin(ctx):
        return True
    who = ("سجّل الدخول بحساب المدير لعرضها." if not ctx.logged_in
           else f"صلاحية حسابك ({ctx.role_label}) لا تشملها؛ هي لمدير النظام فقط.")
    card(f"🔒 <b>{html.escape(what)} — محتوى خاص بالمدير</b><br>{who}", "warn")
    key = f"denied:{what}:{ctx.role}"
    if not st.session_state.get(key):  # نسجّل المحاولة مرة واحدة لكل جلسة حتى لا يمتلئ السجل
        st.session_state[key] = True
        audit("admin_content_denied", ctx, page=what)
    return False


_TABLE_LIMIT = 2000


# ======================================================
# المساعد التقني (GPT-4o) — يُستدعى أسفل كل صفحة
# ======================================================
_AI_PRESETS = {
    "📊 حلّل الوضع": "حلّل بيانات هذه الصفحة ولديك جميع بيانات المنصة بالكامل: ما أبرز نقاط القوة والضعف؟",
    "🛠️ اقترح حلولاً": "اقترح حلولاً عملية مرتبة بالأولوية للمشكلات الظاهرة في هذه الصفحة، وطرح عدة حلول متقنة لحل المشكلات وتفاديها في المستقبل.",
    "🔮 توقّع القادم": "توقّع أداء الأسابيع القادمة بناءً على الاتجاه الحالي: هل سيكون العمل المستمر إيجابياً أم سلبياً، ولماذا؟ وهل مؤشر الإنجاز للمعاملات سلبي أم إيجابي؟",
}


def ai_panel(page_key: str, page_title: str, summary: str, df_all, ctx: AuthContext) -> None:  # المساعد التقني: نص + صوت
    """المساعد التقني: نص + صوت. df_all=None يعني: حمّل كل السجلات عند الطلب فقط."""
    st.markdown(
        '<div class="ai-card-glow"><h4 style="color:#c084fc;margin:0 0 6px 0;">🤖 المساعد التقني — GPT-4o</h4>'
        '<span style="color:#94a3b8;">يحلّل بيانات هذه الصفحة ويقترح الحلول ويتوقّع المسار القادم ضمن صلاحيتك، '
        "ويردّ عليك نصاً وصوتاً.</span></div>",
        unsafe_allow_html=True,
    )
    store = st.session_state.setdefault("ai_panel_answers", {})
    key = f"{page_key}:{ctx.role}:{ctx.username or '-'}"  # يفصل إجابات كل مستخدم/صلاحية

    prompt = None
    for col, (label, text) in zip(st.columns(len(_AI_PRESETS)), _AI_PRESETS.items()):
        if col.button(label, key=f"{key}:{label}", width="stretch"):
            prompt = text
    with st.form(f"form:{key}", clear_on_submit=True):
        free = st.text_input("أو اسأل المساعد عن هذه الصفحة", placeholder="مثال: لماذا تأخر أضعف الأقسام؟")
        asked = st.form_submit_button("إرسال 🚀")
    if asked and free.strip():
        prompt = free.strip()

    if prompt:
        full = (f"[الصفحة: {page_title}]\nملخص الأرقام الحالية (من البيانات المتاحة لصلاحيتي):\n"
                f"{summary}\n\nالطلب: {prompt}")
        data = df_all if df_all is not None else load_all_transactions()
        with st.spinner("⏳ جاري التحليل..."):
            store[key] = (prompt, ask_assistant(full, [], ctx, data))
    if key in store:
        question, answer = store[key]
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            show_reply(answer, key=f"ai:{key}")  # نص + صوت


def _speak_once(text: str, key: str) -> None:  # ينطق النص تلقائياً مرة واحدة لكل مفتاح (إن كان «الرد الصوتي» مفعّلاً) مع زر اس
    """ينطق النص تلقائياً مرة واحدة لكل مفتاح (إن كان «الرد الصوتي» مفعّلاً) مع زر استمع للإعادة."""
    if not text:
        return
    done = st.session_state.setdefault("_spoken_keys", set())
    if st.session_state.get("speak_replies", True) and key not in done:
        done.add(key)
        try:
            audio = synthesize_speech(spoken_version(text))
            if audio:
                play_audio(audio, autoplay=True)
        except Exception:
            pass
    speak_button(text, f"sp:{key}")


_APPROVAL_STATES = ["مسودة", "بانتظار الاعتماد", "معتمد", "أُعيد بملاحظات"]


_FAB_CHIPS = [("🔎 معاملتي", "كيف أتابع معاملتي؟"), ("🏗️ مشاريع", "ما أبرز مشاريع الأمانة المعروضة؟"),
              ("📝 شكوى", "كيف أقدّم شكوى أو بلاغاً؟"), ("🔐 خصوصيتي", "كيف تحمون بياناتي؟"), ("🎓 تدريب", "من أين أبدأ التدريب على المنصة؟")]




# ---- موجّه الصفحات المستقلة (المساعد الكامل، الوصول، خدماتي، الدعم، الأسئلة الشائعة) ----
def open_page(name: str, question: str = "") -> None:  # callback للأزرار: يفتح صفحة مستقلة بدل التبويبات (question يُملأ مسبقاً في الم
    """callback للأزرار: يفتح صفحة مستقلة بدل التبويبات (question يُملأ مسبقاً في المساعد الكامل)."""
    st.session_state["view"] = name
    st.session_state["_scroll_page"] = True  # بعد الرسم نمرّر الشاشة لبداية الصفحة المفتوحة
    if question:
        st.session_state["full_q"] = question


def close_page() -> None:  # يغلق الصفحة المستقلة ويعود للتبويبات
    st.session_state["view"] = None


def go_tab(label: str) -> None:  # callback: يفتح قسم التبويب (الذي يحوي label) كصفحة مستقلة — طريقة مضمونة بلا جافاسكربت
    """callback: يفتح قسم التبويب (الذي يحوي label) كصفحة مستقلة. البديل المضمون لنقر التبويب بجافاسكربت."""
    open_page("tab:" + label)


def scroll_to_page() -> None:  # يمرّر الشاشة لزر «رجوع» (أول الصفحة المفتوحة) مرة واحدة بعد كل فتح
    """يمرّر الشاشة لبداية الصفحة المفتوحة حتى لا يظن المستخدم أن الزر لم يعمل (المحتوى يظهر أسفل الروابط)."""
    if st.session_state.pop("_scroll_page", False):
        components.html("<script>setTimeout(function(){try{var d=window.parent.document;var e=d.querySelector('.st-key-pg_back');"
                        "if(e){e.scrollIntoView({behavior:'smooth',block:'start'});}}catch(x){}},250);</script>", height=0)


def run_pending_tab() -> None:  # يُستدعى في app.py بعد رسم التبويبات: ينقر التبويب المطلوب مرة واحدة
    """يُستدعى في app.py بعد رسم التبويبات: ينقر التبويب المطلوب مرة واحدة."""
    label = st.session_state.pop("pending_tab", None)
    if label:
        components.html("<script>try{var d=window.parent.document;var t=[].slice.call(d.querySelectorAll('button[role=\"tab\"]'))"
                        ".find(function(b){return b.textContent.indexOf(" + json.dumps(label) + ")>-1});if(t){t.click();"
                        "t.scrollIntoView({block:'center',inline:'center'});}}catch(e){}</script>", height=0)


def speak_now(text: str) -> None:  # ينطق الرد تلقائياً (بعد عرض النص فوراً): تنظيف محلي سريع ثم صوت
    """ينطق الرد تلقائياً (بعد عرض النص فوراً): تنظيف محلي سريع ثم صوت. يحترم مفتاح «الرد الصوتي» ولا يفشل بصمت مزعج."""
    if not text or text.startswith(("❌", "⚠️")) or not st.session_state.get("speak_replies", True):
        return
    try:
        audio = synthesize_speech(spoken_version(text))
        if audio:
            play_audio(audio, autoplay=True)
    except Exception:
        pass
