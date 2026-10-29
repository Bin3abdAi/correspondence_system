"""المساعد الصوتي السيادي: تسجيل ← Whisper ← GPT-4o (حسب الصلاحية) ← صوت بشري.

يظهر في الشريط الجانبي فيبقى حاضراً في كل الصفحات.
"""
import hashlib
import html
import re

import streamlit as st

from ai_service import (TTS_VOICE, ask_assistant, detect_language, spoken_version,
                        synthesize_speech, transcribe_audio)
from auth import get_auth_context
from exports import play_audio  # مشغّل الصوت الصامت (بلا شريط) مع زر 🔊
from data_layer import load_all_transactions

_VOICES = ["onyx", "ash", "echo", "fable", "alloy", "nova", "coral", "sage", "shimmer"]

# توجيه أسلوب الرد حسب لغة المتحدث (يُضاف لتعليمات المساعد الواعي بالصلاحيات)
_STYLE = {
    "ar": ("وضع الرد الصوتي (يتجاوز قاعدة الإيجاز السابقة): تكلّم باللهجة السعودية البيضاء بأسلوب مهذب "
           "ودافئ وموجز، بجمل قصيرة تناسب النطق، بلا رموز ولا قوائم ولا تنسيق. افهم لهجة المتحدث السعودية "
           "(ابغى، وش، ايش، الحين، مره، يا طويل العمر) ولا تصحّح كلامه. لا تتجاوز أربع جمل ما لم يطلب التفصيل. توني (روبوت أردني الأصل مولود في السعودية بشماغ أحمر) وسعيدان السهلي (سعودي بغترة وعقال) صديقا طفولة وهما شخصيتا المنصة التفاعليتان المتحاورتان؛ إن سُئلت عنهما فعرّف بهما، "
           "وإن سمعت اسماً قريباً من «توني» أو «سعيدان» (مثل طوني أو تونّي أو تني) فافهم أنه توني."),
    "en": ("Voice mode: the user spoke a non-Arabic language. This overrides the earlier rule about replying "
           "in Arabic: answer in the user's own language, briefly (max 4 sentences), plain text, no markdown."),
}

_CSS = """
<style>
.voice-card{background:linear-gradient(135deg,var(--card-a),var(--card-b));border:1px solid var(--line);border-radius:18px;padding:14px;
  text-align:center;margin-bottom:10px;box-shadow:0 8px 30px var(--btn-glow);}
.voice-orb{width:46px;height:46px;margin:0 auto 8px;border-radius:50%;
  background:radial-gradient(circle at 30% 30%,var(--accent3),var(--accent) 55%,var(--accent2));animation:voicepulse 2.4s infinite;}
@keyframes voicepulse{0%{box-shadow:0 0 0 0 var(--btn-glow)}70%{box-shadow:0 0 0 16px transparent}100%{box-shadow:0 0 0 0 transparent}}
.voice-title{font-weight:700;color:var(--head)}
.voice-sub{font-size:.78rem;color:var(--muted)}
.voice-bubble{border-radius:14px;padding:10px 12px;margin:8px 0;font-size:.88rem;line-height:1.7;color:var(--side-text,var(--text))}
.voice-user{background:var(--card-a);border:1px solid var(--line)}
.voice-bot{background:var(--ai-a);border:1px solid var(--ai-border)}
@media (prefers-reduced-motion: reduce){.voice-orb{animation:none}}
</style>
"""


def _esc(text: str) -> str:  # نص آمن للعرض داخل الفقاعة: يحوّل **غامق** إلى <b> ويحذف رموز الماركداون الأخرى
    """نص آمن للعرض داخل الفقاعة: يحوّل **غامق** إلى <b> ويحذف رموز الماركداون الأخرى."""
    safe = html.escape(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe, flags=re.S)
    safe = re.sub(r"^\s*#{1,6}\s*", "", safe, flags=re.M)
    safe = re.sub(r"^\s*[-*•]\s+", "• ", safe, flags=re.M)
    return safe.replace("*", "").replace("\n", "<br>")


def _clean_for_speech(text: str) -> str:  # ينظّف النص قبل نطقه
    return re.sub(r"\s+", " ", re.sub(r"[*#_`>|~]+", " ", text)).strip()


def _process(data: bytes, ctx, ident: str) -> dict:  # ملاحظة صوتية كاملة: تفريغ ← فهم ← رد (بالصلاحيات) ← نطق
    """ملاحظة صوتية كاملة: تفريغ ← فهم ← رد (بالصلاحيات) ← نطق."""
    stt = transcribe_audio(data)
    if stt.get("error"):
        return {"error": stt["error"]}
    text = stt["text"]
    if not text:
        return {"error": "لم أسمع كلاماً واضحاً. تأكد أن الميكروفون مسموح في المتصفح وأنك تتحدث بقربه، "
                         "ثم اضغط «تسجيل جديد»."}

    lang = detect_language(text)
    history = st.session_state.setdefault(f"voice_hist:{ident}", [])
    reply = ask_assistant(text, history, ctx, load_all_transactions(), extra_system=_STYLE[lang])
    turn = {"text": text, "lang": lang, "reply": reply, "speech": "", "audio": b"", "played": False}
    if reply.startswith(("❌", "⚠️")):
        return turn  # رسالة خطأ: لا ننطقها

    # عربي: ننطق الرد نفسه. غير عربي: الرد مكتوب بلغته، والصوت عربي بلهجة سعودية.
    turn["speech"] = reply if lang == "ar" else spoken_version(reply)
    voice = st.session_state.get("voice_choice", TTS_VOICE)
    turn["audio"] = synthesize_speech(_clean_for_speech(turn["speech"]), voice)
    history += [{"role": "user", "content": text}, {"role": "assistant", "content": reply}]
    del history[:-8]
    return turn


def _show_turn(turn: dict) -> None:  # يعرض دورة المحادثة الصوتية (سمعتك/الرد/الصوت)
    if turn.get("error"):
        st.error(turn["error"])
        return
    chip = "🇸🇦 عربي" if turn["lang"] == "ar" else "🌐 English"
    st.markdown(f'<div class="voice-bubble voice-user"><b>🎤 سمعتك ({chip}):</b><br>{_esc(turn["text"])}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="voice-bubble voice-bot"><b>🤖 الرد:</b><br>{_esc(turn["reply"])}</div>',
                unsafe_allow_html=True)
    if turn["lang"] != "ar" and turn["speech"]:
        st.caption(f"🔊 الرد الصوتي (عربي): {turn['speech']}")
    if turn["audio"]:
        play_audio(turn["audio"], autoplay=not turn["played"])
        turn["played"] = True  # لا يُعاد التشغيل التلقائي عند أي إعادة رسم للصفحة
    elif not turn["reply"].startswith(("❌", "⚠️")):
        st.caption("تعذّر توليد الصوت، والرد مكتوب أعلاه.")


def render_voice_assistant_widget() -> None:  # بديل فارغ إن غاب المساعد الصوتي
    """يظهر في الشريط الجانبي فيبقى حاضراً في كل الصفحات."""
    ctx = get_auth_context()
    ident = f"{ctx.role}:{ctx.username or '-'}"  # حالة منفصلة لكل مستخدم/صلاحية
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="voice-card"><div class="voice-orb"></div>'
        '<div class="voice-title">المساعد الصوتي الذكي</div>'
        '<div class="voice-sub">سجّل ملاحظتك بلهجتك — أفهمها وأردّ عليك صوتاً</div></div>',
        unsafe_allow_html=True)
    with st.expander("⚙️ إعدادات الصوت"):
        st.selectbox("الصوت", _VOICES, index=_VOICES.index(TTS_VOICE) if TTS_VOICE in _VOICES else 0,
                     key="voice_choice")

    # رقم التسجيل: عند الضغط على «تسجيل جديد» يتغيّر مفتاح الأداة فتتصفّر وتعود للعمل بعد أي خطأ
    n = st.session_state.get(f"voice_n:{ident}", 0)
    audio = st.audio_input("اضغط وتحدّث", key=f"voice_in:{ident}:{n}", label_visibility="collapsed")
    if audio is not None:
        data = audio.getvalue()
        sig = hashlib.md5(data).hexdigest()
        if st.session_state.get(f"voice_sig:{ident}") != sig:  # لا نعالج التسجيل نفسه مرتين
            with st.spinner("🎧 أستمع وأحلّل..."):
                st.session_state[f"voice_turn:{ident}"] = _process(data, ctx, ident)
            st.session_state[f"voice_sig:{ident}"] = sig
    turn = st.session_state.get(f"voice_turn:{ident}")
    if turn:
        _show_turn(turn)
    if audio is not None or turn:
        if st.button("🎙️ تسجيل جديد", key=f"voice_reset:{ident}", width="stretch"):
            st.session_state[f"voice_n:{ident}"] = n + 1
            st.session_state.pop(f"voice_turn:{ident}", None)
            st.session_state.pop(f"voice_sig:{ident}", None)
            st.rerun()
