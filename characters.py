"""الشخصيتان Bin3abdAi (شخصية المطوّر) وسعيدان السهلي: رسمهما وحوارهما وتفاعلهما وأصواتهما.

- كل شيء الخاص بالشخصيتين هنا في ملف واحد (الرسم SVG، الحوار، الأنماط CSS، سكربت التفاعل).
- ui.py يستورد منه `companions` ويستدعيه views_public.render_fab في كل صفحة.
- لتغيير الحوار عدّل القاموس _SCENES فقط؛ لتغيير سرعة الظهور عدّل GAP_MIN / GAP_MAX (بالثواني).
- «متكلم واحد فقط»: الشخصيتان تخضعان لمنسّق الصوت (floor.py): تصمتان أثناء صوت المساعد أو تسجيل الميكروفون أو الكتابة،
  وتبقيان هادئتين نحو 20 ثانية بعدها، ويمكن كتمهما بزر 🔇 الصغير بينهما.
- تجهيز الأصوات مرة واحدة:  python characters.py        (وللتنظيف من المقاطع القديمة:  python characters.py --clean)
"""
import base64  # noqa: F401  (للتوافق)
import hashlib
import html  # noqa: F401  (للتوافق)
import json
import os
import threading
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from floor import boot_js

GAP_MIN, GAP_MAX = 55, 75       # الفاصل بين حوار وآخر: نحو دقيقة (بالثواني)
IDLE_SECONDS = 40               # إن لم يضغط المستخدم شيئاً هذه المدة يبدؤون حواراً يعرض المساعدة
FIRST_DELAY = 8                 # أول ظهور بعد فتح الصفحة (ثوانٍ)
_ENGINE_VER = "14"               # ارفعه عند تغيير _ENGINE ليُحمَّل المحرّك الجديد

# ======================================================
# رسم Bin3abdAi: روبوت أخضر بشماغ أحمر وأبيض وعقال (شخصية المطوّر)
# ======================================================
_ROBOT_SVG = """<svg viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="nbB" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#43e0a0"/><stop offset="1" stop-color="#0d7447"/></linearGradient>
<linearGradient id="nbS" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#c9e2d5"/></linearGradient>
<radialGradient id="nbF" cx="50%" cy="35%" r="75%"><stop offset="0" stop-color="#18603f"/><stop offset="1" stop-color="#03140d"/></radialGradient>
<pattern id="nbC" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#ffffff"/>
<rect width="3" height="3" fill="#d32f2f"/><rect x="3" y="3" width="3" height="3" fill="#d32f2f"/></pattern>
</defs>
<ellipse cx="50" cy="125.5" rx="28" ry="4.4" fill="#000" opacity=".3"/>
<rect x="35" y="110" width="11" height="13" rx="4.5" fill="#0c5c37"/><rect x="54" y="110" width="11" height="13" rx="4.5" fill="#0c5c37"/>
<rect x="33" y="119" width="15" height="6" rx="3" fill="#094a2d"/><rect x="52" y="119" width="15" height="6" rx="3" fill="#094a2d"/>
<path d="M33 88 Q20 94 17 106" stroke="#168d58" stroke-width="8.5" fill="none" stroke-linecap="round"/>
<circle cx="16.5" cy="108" r="5.4" fill="#eefaf3" stroke="#168d58" stroke-width="2"/>
<rect x="28" y="75" width="44" height="40" rx="18" fill="url(#nbB)" stroke="#d4af37" stroke-width="2.4"/>
<path d="M34 85 Q36 79 46 78" stroke="#fff" stroke-width="2.4" fill="none" opacity=".5" stroke-linecap="round"/>
<rect x="38" y="86" width="24" height="16" rx="8" fill="#0a3a25" opacity=".55"/>
<circle class="glow" cx="50" cy="94" r="6.4" fill="#ffe082"/><circle cx="50" cy="94" r="2.8" fill="#fff"/>
<rect x="35" y="104" width="30" height="3" rx="1.5" fill="#d4af37" opacity=".85"/>
<rect x="14" y="40" width="7" height="15" rx="3.5" fill="#d4af37"/><rect x="79" y="40" width="7" height="15" rx="3.5" fill="#d4af37"/>
<rect x="18" y="24" width="64" height="50" rx="23" fill="url(#nbS)" stroke="#1b9a60" stroke-width="3"/>
<rect x="25" y="34" width="50" height="30" rx="15" fill="url(#nbF)"/>
<path d="M30 38 Q40 34 50 35" stroke="#fff" stroke-width="2" opacity=".28" fill="none" stroke-linecap="round"/>
<g class="look"><g class="eye"><ellipse cx="40" cy="47" rx="5.2" ry="6.4" fill="#8dffc4"/><ellipse cx="38.4" cy="44.8" rx="1.7" ry="2.1" fill="#fff" opacity=".9"/></g>
<g class="eye"><ellipse cx="60" cy="47" rx="5.2" ry="6.4" fill="#8dffc4"/><ellipse cx="58.4" cy="44.8" rx="1.7" ry="2.1" fill="#fff" opacity=".9"/></g></g>
<path d="M35 38.5 Q40 36 45 38.5 M55 38.5 Q60 36 65 38.5" stroke="#8dffc4" stroke-width="1.8" fill="none" stroke-linecap="round" opacity=".8"/>
<path class="smile" d="M42 56.5 Q50 62 58 56.5" stroke="#8dffc4" stroke-width="2.6" fill="none" stroke-linecap="round"/>
<g class="talk"><ellipse cx="50" cy="58" rx="6.4" ry="3.6" fill="#8dffc4"/><ellipse cx="50" cy="58.6" rx="3.4" ry="1.5" fill="#06301f"/></g>
<path d="M16 44 Q8 12 50 10 Q92 12 84 44 Q78 29 50 27 Q22 29 16 44Z" fill="url(#nbC)" stroke="#a31f1f" stroke-width="1.6"/>
<path d="M18 30 Q50 18 82 30" stroke="#8a1b1b" stroke-width=".9" fill="none" opacity=".55"/>
<path d="M16 42 Q4 58 13 80 L27 71 Q19 58 23 46Z" fill="url(#nbC)" stroke="#a31f1f" stroke-width="1.6"/>
<path d="M84 42 Q96 58 87 80 L73 71 Q81 58 77 46Z" fill="url(#nbC)" stroke="#a31f1f" stroke-width="1.6"/>
<path d="M17 26 Q50 7 83 26" stroke="#171717" stroke-width="5.4" fill="none" stroke-linecap="round"/>
<path d="M18 22.5 Q50 4.5 82 22.5" stroke="#171717" stroke-width="3.2" fill="none" stroke-linecap="round" opacity=".9"/>
<path d="M17 26 Q50 7 83 26" stroke="#d4af37" stroke-width="1.2" fill="none" stroke-dasharray="1.6 4.6" stroke-linecap="round"/>
<line x1="50" y1="10" x2="50" y2="2.5" stroke="#d4af37" stroke-width="2.6"/><circle class="glow" cx="50" cy="2.8" r="4.4" fill="#ffd54f"/>
<g class="wave" style="transform-origin:67px 86px"><path d="M67 86 Q80 84 87 70" stroke="#168d58" stroke-width="8.5" fill="none" stroke-linecap="round"/>
<circle cx="88.5" cy="67.5" r="5.5" fill="#eefaf3" stroke="#168d58" stroke-width="2"/></g>
</svg>"""

# ======================================================
# رسم سعيدان السهلي: سعودي بغترة بيضاء وعقال وثوب وبشت بني بحواف ذهبية
# ======================================================
_SAUDI_SVG = """<svg viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="sdT" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e6ece9"/><stop offset=".45" stop-color="#ffffff"/><stop offset="1" stop-color="#d9e1dd"/></linearGradient>
<radialGradient id="sdK" cx="45%" cy="35%" r="80%"><stop offset="0" stop-color="#f6d3ae"/><stop offset="1" stop-color="#d09a69"/></radialGradient>
<linearGradient id="sdG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#dfe7e3"/></linearGradient>
<linearGradient id="sdB" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6b4b2e"/><stop offset=".55" stop-color="#3e2b19"/><stop offset="1" stop-color="#21150a"/></linearGradient>
<linearGradient id="sdZ" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7de8a"/><stop offset=".5" stop-color="#d4af37"/><stop offset="1" stop-color="#a8821a"/></linearGradient>
</defs>
<ellipse cx="50" cy="125.5" rx="30" ry="4.4" fill="#000" opacity=".3"/>
<path d="M22 124 Q23 84 50 78 Q77 84 78 124 Z" fill="url(#sdT)" stroke="#c3cdc8" stroke-width="2"/>
<path d="M50 80 L50 122" stroke="#d3dcd7" stroke-width="1.6"/>
<circle cx="50" cy="93" r="1.7" fill="#b9c5bf"/><circle cx="50" cy="103" r="1.7" fill="#b9c5bf"/><circle cx="50" cy="113" r="1.7" fill="#b9c5bf"/>
<path d="M41 79 Q50 91 59 79" fill="#f3dcc0" stroke="#c3cdc8" stroke-width="1.4"/>
<path d="M41 79 Q50 89 59 79" fill="none" stroke="#d4af37" stroke-width="1.6"/>
<!-- البشت: عباءة بنية بحواف ذهبية (زري) مفتوحة من الأمام -->
<path d="M41.5 78.5 C33 79 26.5 83.5 23.5 91 C19.5 102 17.5 113 17.5 124.5 L42 124.5 C43.2 112 44.8 100 46 90 C45.4 85 43.6 81 41.5 78.5 Z" fill="url(#sdB)" stroke="#1c1209" stroke-width=".8" stroke-linejoin="round"/>
<path d="M58.5 78.5 C67 79 73.5 83.5 76.5 91 C80.5 102 82.5 113 82.5 124.5 L58 124.5 C56.8 112 55.2 100 54 90 C54.6 85 56.4 81 58.5 78.5 Z" fill="url(#sdB)" stroke="#1c1209" stroke-width=".8" stroke-linejoin="round"/>
<path d="M27 95 C24.5 104 23 113 22.6 122" stroke="#fff" stroke-opacity=".12" stroke-width="2.6" fill="none" stroke-linecap="round"/>
<path d="M73 95 C75.5 104 77 113 77.4 122" stroke="#fff" stroke-opacity=".12" stroke-width="2.6" fill="none" stroke-linecap="round"/>
<path d="M41.5 78.5 C33 79 26.5 83.5 23.5 91 M58.5 78.5 C67 79 73.5 83.5 76.5 91" stroke="url(#sdZ)" stroke-width="2.2" fill="none" stroke-linecap="round"/>
<path d="M41.5 78.5 C43.6 81 45.4 85 46 90 C44.8 100 43.2 112 42 124 M58.5 78.5 C56.4 81 54.6 85 54 90 C55.2 100 56.8 112 58 124" stroke="url(#sdZ)" stroke-width="2.4" fill="none" stroke-linecap="round"/>
<path d="M17.8 122.6 L41.8 122.6 M58.2 122.6 L82.2 122.6" stroke="url(#sdZ)" stroke-width="1.7" fill="none" stroke-linecap="round"/>
<path d="M45.4 92 C44.4 101 43.2 110 42.6 118 M54.6 92 C55.6 101 56.8 110 57.4 118" stroke="#1c1209" stroke-opacity=".5" stroke-width=".7" fill="none" stroke-dasharray="1.2 2"/>
<path d="M30 88 Q20 100 25 113" stroke="#ffffff" stroke-width="10" fill="none" stroke-linecap="round"/>
<path d="M30 88 Q20 100 25 113" stroke="#c3cdc8" stroke-width="1" fill="none" stroke-linecap="round" opacity=".6"/>
<circle cx="25.5" cy="115" r="5" fill="url(#sdK)"/>
<rect x="44" y="68" width="12" height="12" rx="4" fill="#d6a275"/>
<ellipse cx="31.5" cy="52" rx="3.2" ry="5" fill="#d6a275"/><ellipse cx="68.5" cy="52" rx="3.2" ry="5" fill="#d6a275"/>
<ellipse cx="50" cy="51" rx="19.5" ry="21" fill="url(#sdK)"/>
<path d="M32 55 Q34 73 50 75.5 Q66 73 68 55 Q61 66 50 66 Q39 66 32 55Z" fill="#2a2a2a"/>
<path d="M41 62.5 Q50 60 59 62.5 Q50 65 41 62.5Z" fill="#2a2a2a"/>
<path class="smile" d="M44.5 65.5 Q50 69.5 55.5 65.5" stroke="#f4d9bd" stroke-width="1.9" fill="none" stroke-linecap="round"/>
<g class="talk"><ellipse cx="50" cy="66.4" rx="4.8" ry="2.9" fill="#6e2424"/><ellipse cx="50" cy="65.2" rx="3.2" ry="1" fill="#fff"/></g>
<path d="M50 52 Q48.5 57 51 58" stroke="#b9855a" stroke-width="1.5" fill="none" stroke-linecap="round"/>
<g class="look"><g class="eye"><ellipse cx="42" cy="50" rx="3.8" ry="3.2" fill="#fff"/><circle cx="42" cy="50" r="2.3" fill="#2a1a10"/><circle cx="41.2" cy="49.2" r=".8" fill="#fff"/></g>
<g class="eye"><ellipse cx="58" cy="50" rx="3.8" ry="3.2" fill="#fff"/><circle cx="58" cy="50" r="2.3" fill="#2a1a10"/><circle cx="57.2" cy="49.2" r=".8" fill="#fff"/></g></g>
<path d="M36 44.5 Q42 41 47 44 M53 44 Q58 41 64 44.5" stroke="#1c1c1c" stroke-width="2.6" fill="none" stroke-linecap="round"/>
<path d="M27 52 Q22 17 50 16 Q78 17 73 52 Q69 36 50 34 Q31 36 27 52Z" fill="url(#sdG)" stroke="#c3cdc8" stroke-width="1.6"/>
<path d="M33 30 Q50 22 67 30 M30 38 Q50 29 70 38" stroke="#cdd6d1" stroke-width="1.1" fill="none"/>
<path d="M27 48 Q15 64 25 82 L38 72 Q30 62 34 50Z" fill="url(#sdG)" stroke="#c3cdc8" stroke-width="1.6"/>
<path d="M73 48 Q85 64 75 82 L62 72 Q70 62 66 50Z" fill="url(#sdG)" stroke="#c3cdc8" stroke-width="1.6"/>
<path d="M26 32 Q50 15 74 32" stroke="#141414" stroke-width="5.4" fill="none" stroke-linecap="round"/>
<path d="M27 28.5 Q50 11.5 73 28.5" stroke="#141414" stroke-width="3.2" fill="none" stroke-linecap="round" opacity=".9"/>
<path d="M26 32 Q50 15 74 32" stroke="#d4af37" stroke-width="1.2" fill="none" stroke-dasharray="1.6 4.6" stroke-linecap="round"/>
<g class="wave" style="transform-origin:68px 90px"><path d="M68 90 Q80 86 86 73" stroke="#ffffff" stroke-width="10" fill="none" stroke-linecap="round"/>
<path d="M68 90 Q80 86 86 73" stroke="#c3cdc8" stroke-width="1" fill="none" stroke-linecap="round" opacity=".6"/><circle cx="87.5" cy="70.5" r="5" fill="url(#sdK)"/></g>
</svg>"""

# ======================================================
# الحوار: مشاهد قصيرة (Bin3abdAi "r" وسعيدان "s") تنتهي بعرض مساعدة ورابط يفتح الصفحة
# كل سطر: {"w": المتحدث, "t": النص}؛ وآخر سطر قد يحمل رابطاً {"g": معرّف الزر المخفي, "l": نص الرابط}
# معرّفات الروابط (تُنشأ كأزرار مخفية في views_public.render_quick_links):
#   PG_assistant / PG_translate / PG_services / PG_support / PG_faq / PG_access
#   PG_t_tracking / projects / opendata / training / feedback / privacy / dash / intake / field / ops / letters / quality / ready
# Bin3abdAi: شخصية المطوّر — جدّي وذكي وخبير بالذكاء الاصطناعي ونظم المعلومات، لطيف بمداعبة خفيفة، لهجة سعودية بيضاء.
# سعيدان: سعودي كريم خفيف ظل بالبشت، يناديه «بن عبد». وهما صديقان يمزحان بأدب ويخدمان الناس.
# ======================================================
def _sc(*lines):  # يبني مشهداً من سطور (متحدث، نص[، معرّف الرابط، نص الرابط])
    out = []
    for ln in lines:
        d = {"w": ln[0], "t": ln[1]}
        if len(ln) > 2:
            d["g"], d["l"] = ln[2], ln[3]
        out.append(d)
    return out


_SCENES = {
    "common": [
        _sc(("r", "أنا Bin3abdAi، شخصية المطوّر في المنصة. أحلّل وأتأكد من كل رقم قبل لا أقوله 🤖"),
            ("s", "وأنا سعيدان السهلي، مسؤول الضيافة والقهوة. تخصصي ما يحتاج ذكاء اصطناعي ☕"),
            ("r", "ولو احتجت شي جدّي، افتح المساعد وأجاوبك بدقّة 👇", "PG_assistant", "💬 المساعد كاملاً")),
        _sc(("s", "يا بن عبد، شف مشاريع الأمانة، الأرقام تفرّح القلب!"),
            ("r", "والتحليل أفرح: نسب الإنجاز، والمتأخر قبل لا يتأخر 📊"),
            ("s", "تفضّل شوف بنفسك 👇", "PG_t_projects", "🏗️ مشاريع الأمانة")),
        _sc(("s", "يا بن عبد، لو كل معاملة تتأخر مثل الغدا عندي كان قفلنا الأمانة!"),
            ("r", "ما تخاف، لكل معاملة مؤشّر مهلة وتنبيه قبل التأخير. أما الغدا فما أضمنه 😄"),
            ("s", "اكتب رقم معاملتك وتتبّعها بنفسك 👇", "PG_t_tracking", "🔎 تتبّع معاملتك")),
        _sc(("s", "قل لي يا بن عبد، الذكاء الاصطناعي يقدر يسوي قهوة سعودية؟"),
            ("r", "يحلّل الطلب والتوقيت والكمية، بس الهيل يبي يد أصيلة مثل يدك ☕"),
            ("s", "كلامك عسل! خلّنا نخدم الناس 😄")),
        _sc(("r", "قاعدتي الذهبية: كل واحد يشوف بس اللي يحق له يشوفه. الصلاحيات عندي خط أحمر 🔒"),
            ("s", "حتى أنا يا بن عبد؟"),
            ("r", "حتى أنت يا سهلي، بس القهوة مفتوحة للجميع ☕", "PG_t_privacy", "🔐 الأمان والخصوصية")),
        _sc(("s", "وش رأيك نفتح البيانات للناس يا بن عبد؟"),
            ("r", "نفتحها مجمّعة ومجهّلة، بدون أسماء وبدون أسرار. شفافية بمسؤولية 📈"),
            ("s", "جرّب الأرقام المفتوحة بنفسك 👇", "PG_t_opendata", "📈 بيانات مفتوحة")),
        _sc(("r", "كلّم المساعد بصوتك، يفهم لهجتك السعودية ويرد عليك صوت وكتابة 🎙️"),
            ("s", "حتى لو قلت «ابغى» و«وش»؟"),
            ("r", "حتى لو قلتها بسرعة، Whisper يلتقطها 😉 جرّبه", "PG_assistant", "💬 المساعد كاملاً")),
        _sc(("s", "عندي ضيف ما يتكلم عربي، وش أسوي؟"),
            ("r", "المترجم الصوتي يسمعك ويترجم فوراً ويقرأ الترجمة بصوت واضح 🌍"),
            ("s", "يعني ما أحتاج أتعلّم لغات؟ أبشر! 👇", "PG_translate", "🌍 المترجم الصوتي")),
        _sc(("r", "سعيدان، ليش وجهك كذا؟ تحليل الملامح يقول: حزن بنسبة ستين بالمئة 😅"),
            ("s", "ما أحد قيّم خدمتنا اليوم 🥲"),
            ("r", "رأي المستخدم يطوّر المنصة، أعطونا خمس نجوم ⭐", "PG_t_feedback", "💬 رأيك يهمنا")),
        _sc(("r", "إذا علقت بخطوة لا تحتار، افتح تذكرة دعم وفريقنا يتابع معك 🛟"),
            ("s", "ونحن وراك مثل ظلّك 🤝", "PG_support", "🛟 الدعم والتواصل")),
        _sc(("s", "عندك سؤال متكرر؟ يمكن جوابه جاهز!"),
            ("r", "الأسئلة الشائعة فيها بحث ذكي يوصلك للجواب بثواني 🔍", "PG_faq", "❓ الأسئلة الشائعة")),
        _sc(("r", "تقدر تكبّر الخط وتغيّر الألوان وتفعّل التباين العالي. المنصة للجميع ♿"),
            ("s", "وهذا شي أفتخر فيه، كل واحد يستفيد", "PG_access", "♿ إمكانية الوصول")),
        _sc(("s", "ما تدري من وين تبدأ؟"),
            ("r", "«خدماتي» تعرض لك كل شي مرتّب حسب دورك في مكان واحد 🧩", "PG_services", "🧩 خدماتي")),
        _sc(("r", "تبي تتعلّم المنصة بسرعة؟ مركز التدريب فيه مرشد صوتي 🎓"),
            ("s", "أحلى من محاضرة طويلة والقهوة باردة 😄", "PG_t_training", "🎓 التدريب والدعم")),
        _sc(("s", "يا بن عبد، متى تنام؟ شفتك تشتغل من الفجر!"),
            ("r", "السحابة ما تنام يا سهلي، وأنا أراقب الأرقام وأحدّث الأنظمة 😅"),
            ("s", "الله يعطيك العافية، بس خذ لك استراحة ☕")),
        _sc(("r", "قاعدتي: ما أقول رقم إلا وله مصدر في بيانات المنصة 🔍"),
            ("s", "وأنا قاعدتي: ما أقدّم قهوة إلا وفيها هيل ☕"),
            ("r", "كل واحد وتخصصه 😄 اسألني وأنا أتأكد", "PG_assistant", "💬 المساعد كاملاً")),
    ],
    "guest": [
        _sc(("r", "أهلاً بالزائر الكريم! أنا Bin3abdAi، وهذي المنصة مفتوحة لك 🤖"),
            ("s", "وأنا سعيدان السهلي، يا هلا ومرحبا ☕"),
            ("r", "اكتب رقم معاملتك أو قله بصوتك وأنا أدلّك", "PG_t_tracking", "🔎 تتبّع معاملتك")),
        _sc(("s", "تبي تعرف وش تقدّم لك المنصة كزائر؟"),
            ("r", "تتبّع المعاملة، ومشاريع الأمانة، والبيانات المفتوحة، والدعم. كلها بدون تسجيل دخول", "PG_services", "🧩 خدماتي")),
    ],
    "employee": [
        _sc(("r", "يا زميل، المعاملات الجديدة بانتظارك. وقت الجد جد 💼"),
            ("s", "وإدخال البلاغ بالصورة أسرع من الشاهي 🫖"),
            ("r", "جرّب إدخال البيانات والتحليل البصري", "PG_t_intake", "📝 إدخال البيانات")),
        _sc(("s", "يا بن عبد، وين الفرق الميدانية اليوم؟"),
            ("r", "في الميدان يا سهلي، ولا تسأل كأنك المدير 😄"),
            ("s", "نكلّفهم ونتابعهم من هنا 👇", "PG_t_field", "👷 الفرق الميدانية")),
        _sc(("r", "عندك خطاب رسمي؟ أصيغه لك بأسلوب المراسلات الحكومية"),
            ("s", "وأنا أراجع الشكل، ما أخلّيه يطلع غلط 😅"),
            ("r", "افتح الخطابات الرسمية", "PG_t_letters", "📨 الخطابات الرسمية")),
    ],
    "manager": [
        _sc(("r", "يا مدير الإدارة، المتأخرات تحت المجهر، وأنبّهك قبل لا تتأخر ⏰"),
            ("s", "وحنا نحلم بيوم صفر متأخرات يا بن عبد 😂"),
            ("r", "تابع مهلة الإنجاز من لوحة التحليلات", "PG_t_dash", "📊 لوحة التحليلات")),
        _sc(("s", "طال عمرك، فرق إدارتك في الميدان"),
            ("r", "وتقدر تكلّفهم وتتابعهم بضغطة", "PG_t_field", "👷 الفرق الميدانية")),
    ],
    "reviewer": [
        _sc(("r", "أهلاً بالمراجع! كل شي قدامك للقراءة والتدقيق"),
            ("s", "ولا أحد يلمس شي بدون تدقيق 😎"),
            ("r", "ابدأ بجودة البيانات", "PG_t_quality", "🧪 جودة البيانات")),
    ],
    "admin": [
        _sc(("s", "طال عمرك المدير، الأرقام جاهزة 📊"),
            ("r", "اسألني: حلّل لي وضع الطرق وأولويات رؤية 2030 🛣️", "PG_assistant", "💬 المساعد كاملاً")),
        _sc(("r", "قبل أي عرض للمنصة، افحص الجاهزية يا سهلي"),
            ("s", "ولا نبدأ الاجتماع قبل ما يطلع كل شي ✅", "PG_t_ready", "🚀 جاهزية المشروع")),
        _sc(("s", "أبشر بالتحليل: أرقام وأسباب ومخاطر"),
            ("r", "ونجهّز لك التوقعات والمتأخرات بسؤال واحد", "PG_t_dash", "📊 لوحة التحليلات")),
    ],
}

_DIALOGUE = _SCENES  # اسم قديم للتوافق


# مشاهد التفاعل عند وضع الفأرة على إحدى الشخصيتين (تُختار عشوائياً، ولكل شخصية تهدئة 12 ثانية)
_HOVER = {
    "r": [
        _sc(("r", "هلا فيك! اسألني بدقّة وأجاوبك بدقّة 😉")),
        _sc(("r", "لحظة… أحلّل المؤشر… النتيجة: ضيف لطيف ✨")),
        _sc(("r", "أهلاً! أنا Bin3abdAi، بخدمتك 💡")),
        _sc(("r", "تبي تتبّع معاملتك؟ أسرع من الريح 💨", "PG_t_tracking", "🔎 تتبّع معاملتك")),
        _sc(("r", "هلا! شايفك تقرّب… تحتاج مساعدة؟ 😉"), ("s", "لا تخوّف الضيف يا بن عبد 😂")),
    ],
    "s": [
        _sc(("s", "يا هلا والله! تفضّل ☕")),
        _sc(("s", "أبشر! بس لا تمسك العقال 😅")),
        _sc(("s", "هلا بالغالي، القهوة جاهزة وخدمتك أجهز ☕")),
        _sc(("s", "سلّم على الضيف يا بن عبد!"), ("r", "هلا هلا بالضيف 👋🤖")),
        _sc(("s", "تبي أدلّك على خدماتك؟", "PG_services", "🧩 خدماتي")),
    ],
}

# مشاهد تُعرض حين «تستشعر» الشخصيتان أن المستخدم لم يضغط شيئاً منذ مدة (IDLE_SECONDS)
_IDLE = [
    _sc(("r", "سعيدان… شكل الضيف سرح 😄 تبي نساعده؟"),
        ("s", "ولا ضغط شي من شوي! جرّب «خدماتي» وتشوف كل شي بمكان واحد", "PG_services", "🧩 خدماتي")),
    _sc(("s", "هلا! شفناك ساكت… يمكن تبي تتبّع معاملتك؟"),
        ("r", "أو اسأل المساعد بصوتك، ما نعضّ 😁", "PG_assistant", "💬 المساعد كاملاً")),
    _sc(("r", "لو محتار من وين تبدأ، الأزرار تحت قدامك 👇"),
        ("s", "وإذا تعبت… القهوة عليّ ☕ والخدمة علينا")),
    _sc(("s", "يا بن عبد، الضيف ساكت من زمان!"),
        ("r", "يمكن ينتظر أحد يفاتحه 😂 تفضّل، الأسئلة الشائعة فيها كل شي", "PG_faq", "❓ الأسئلة الشائعة")),
]

# ردود الشخصيتين عند النقر عليهما (Bin3abdAi ثم سعيدان)
_REACT = {"r": ["أبشر! ⚡", "جاهز، اسألني!", "Bin3abdAi بخدمتك 💡", "تحليل جاهز، تفضّل 😄", "حاضر يا غالي"],
          "s": ["حيّاك الله ☕", "تفضّل يا طيب", "وش أخدمك فيه؟", "على راسي 🌴", "أنا السهلي وأبشر! 😎"]}

# ======================================================
# أنماط CSS للشخصيتين (تُحقن مع الشخصيتين فقط)
# ======================================================
_CSS = """<style>/*nofix*/
.st-key-cmp_js{position:fixed !important;width:0 !important;height:0 !important;overflow:hidden !important;}
.st-key-cmp_audio{position:fixed !important;left:-9999px;top:0;width:1px !important;height:1px !important;overflow:hidden !important;opacity:0;pointer-events:none;}
.cmp-stage{position:fixed;left:14px;bottom:132px;z-index:99980;width:300px;height:250px;pointer-events:none;direction:rtl;--ex:0;--ey:0;}
.cmp{position:absolute;bottom:0;width:112px;height:146px;pointer-events:auto;cursor:pointer;transform-origin:50% 100%;
  animation:cmpfloat 4.2s ease-in-out infinite;filter:drop-shadow(0 8px 10px rgba(0,0,0,.4));-webkit-tap-highlight-color:transparent;}
.stApp:has([data-testid="stChatInput"]) .cmp-stage{bottom:204px}  /* صفحة فيها خانة محادثة ثابتة: ارفع الشخصيتين فلا تغطيان زر الإرسال */
.cmp.r{left:6px}.cmp.s{right:6px;animation-delay:-2.1s}
@keyframes cmpfloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
.cmp:hover{animation:cmphop .55s ease-in-out;filter:drop-shadow(0 10px 18px rgba(212,175,55,.55));}
.cmp.react{animation:cmpspin .85s ease-in-out;}
@keyframes cmphop{0%{transform:none}35%{transform:translateY(-16px) scale(1.06,.96)}70%{transform:translateY(0) scale(.97,1.04)}100%{transform:none}}
@keyframes cmpspin{0%{transform:none}30%{transform:translateY(-24px) rotate(-12deg)}60%{transform:translateY(-8px) rotate(9deg)}100%{transform:none}}
.cmp svg{width:100%;height:100%;overflow:visible;transform-origin:50% 92%;transform:rotate(calc(var(--lean,0) * 1deg));
  transition:transform .22s ease-out;animation:cmpbreathe 3.8s ease-in-out infinite}
@keyframes cmpbreathe{0%,100%{scale:1 1}50%{scale:1.012 1.02}}
.cmp .look{transform-box:fill-box;transform-origin:center;transform:translate(calc(var(--ex,0) * 3.6px),calc(var(--ey,0) * 2.6px));transition:transform .14s ease-out}
.cmp:hover .look{transform:translate(calc(var(--ex,0) * 3.6px),calc(var(--ey,0) * 2.6px)) scale(1.12)}
.cmp:hover .smile{transform-box:fill-box;transform-origin:center;transform:scale(1.18,1.5)}
.cmp:hover .wave{animation:cmpwave 1.1s ease-in-out infinite}
.cmp::before{content:"";position:absolute;left:6%;right:6%;bottom:-5px;height:16px;border-radius:50%;opacity:0;transition:opacity .3s,transform .3s;
  background:radial-gradient(ellipse at center,rgba(90,255,176,.65),rgba(90,255,176,0) 70%);transform:scale(.7)}
.cmp.s::before{background:radial-gradient(ellipse at center,rgba(255,213,79,.65),rgba(255,213,79,0) 70%)}
.cmp:hover::before{opacity:1;transform:scale(1.15)}
.cmp::after{content:"";position:absolute;left:-8px;right:-8px;top:-6px;bottom:8px;border-radius:50%;border:1.5px dashed rgba(141,255,196,.7);
  opacity:0;transition:opacity .3s;pointer-events:none;animation:cmpring 7s linear infinite}
.cmp.s::after{border-color:rgba(255,213,79,.75)}
.cmp:hover::after{opacity:.75}
@keyframes cmpring{to{transform:rotate(360deg)}}
.spk{position:absolute;width:5px;height:5px;border-radius:50%;background:#8dffc4;box-shadow:0 0 9px #8dffc4;pointer-events:none;
  animation:cmpspk 1.1s ease-out forwards}
.cmp.s .spk{background:#ffd54f;box-shadow:0 0 9px #ffd54f}
@keyframes cmpspk{0%{opacity:1;transform:translate(0,0) scale(1)}100%{opacity:0;transform:translate(var(--dx,0px),-60px) scale(.3)}}
.cmp .eye{transform-box:fill-box;transform-origin:center;animation:cmpblink 4.6s infinite}
.cmp.s .eye{animation-delay:-1.7s}
@keyframes cmpblink{0%,91%,100%{transform:scaleY(1)}94%{transform:scaleY(.08)}}
.cmp .wave{animation:cmpwave 7s ease-in-out infinite}
.cmp.s .wave{animation-delay:-3.4s}
@keyframes cmpwave{0%,22%,100%{transform:rotate(0)}5%,13%{transform:rotate(-26deg)}9%,17%{transform:rotate(8deg)}}
.cmp .glow{animation:cmpglow 2.4s ease-in-out infinite alternate}
@keyframes cmpglow{from{opacity:.55}to{opacity:1}}
.cmp .talk{opacity:0}
.cmp.talking .talk{opacity:1}.cmp.talking .smile{opacity:0}
.cmp.talking .talk ellipse{transform-box:fill-box;transform-origin:center;animation:cmpflap .26s ease-in-out infinite alternate}
/* عند وجود صوت حقيقي يتحرك الفم بحسب شدّة الموجة (--mo) بدل التحريك الثابت */
.cmp[data-sync] .talk ellipse{animation:none !important;transform:scaleY(calc(.22 + var(--mo,0)*1.5))}
.cmp[data-sync].talking{animation:none}
@keyframes cmpflap{from{transform:scaleY(.35)}to{transform:scaleY(1.45)}}
.cmp.talking{animation:cmptalkbob .5s ease-in-out infinite}
@keyframes cmptalkbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
.bub{position:absolute;bottom:152px;width:218px;padding:9px 13px;border-radius:16px;background:rgba(255,255,255,.98);color:#10281b;
  border:2px solid #d4af37;font-size:.83rem;font-weight:600;line-height:1.65;pointer-events:none;
  box-shadow:0 10px 26px rgba(0,0,0,.35);animation:cmppop .28s ease-out;z-index:3;}
.bub b{display:block;font-size:.68rem;opacity:.65;margin-bottom:1px}
@keyframes cmppop{from{opacity:0;transform:translateY(8px) scale(.85)}to{opacity:1;transform:none}}
.bub::after{content:"";position:absolute;bottom:-9px;width:14px;height:14px;background:inherit;border-right:2px solid #d4af37;border-bottom:2px solid #d4af37;transform:rotate(45deg);}
.bub.r{left:0}.bub.r::after{left:42px}
.bub.s{right:0}.bub.s::after{right:42px}
.bub .go{display:inline-block;margin-top:6px;padding:4px 12px;border-radius:999px;background:linear-gradient(135deg,#1f9d62,#0f6b40);color:#fff;
  font-weight:700;font-size:.78rem;cursor:pointer;pointer-events:auto;border:1px solid #d4af37;transition:.2s;text-decoration:none}
.bub .go:hover{transform:translateY(-1px);box-shadow:0 0 14px rgba(31,157,98,.7)}
/* زر كتم الشخصيتين بينهما: يوقف الكلام والحوار التلقائي (يُحفظ اختيارك في المتصفح) */
.cmp-mute{position:absolute;left:50%;bottom:6px;transform:translateX(-50%);width:30px;height:30px;border-radius:50%;padding:0;
  border:1.5px solid rgba(212,175,55,.85);background:rgba(8,20,16,.82);color:#f5d97a;font-size:14px;line-height:1;cursor:pointer;
  pointer-events:auto;z-index:4;opacity:.6;transition:opacity .2s,transform .2s,background .2s;display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 10px rgba(0,0,0,.4)}
.cmp-mute:hover,.cmp-mute:focus-visible{opacity:1;transform:translateX(-50%) scale(1.12)}
.cmp-mute.off{opacity:.95;background:rgba(130,28,28,.92);color:#fff}
@media (max-width:1250px){.cmp-stage{transform:scale(.76);transform-origin:left bottom}}
@media (max-width:820px){.cmp-stage{display:none}}
</style>"""

# ======================================================
# المحرّك: يعمل داخل صفحة المتصفح الأم (لا يتأثر بإعادة رسم Streamlit)
# العيون تتبع المؤشر · تحريك/نقر/لمس · أصوات خفيفة · حوار كل دقيقة تقريباً · روابط داخل الفقاعات
# «متكلم واحد فقط»: لا يبدآن ولا يكملان أثناء صوت المساعد أو الميكروفون أو الكتابة (عبر window.__floor)
# ======================================================
_ENGINE = r"""(function(){
var P=window,D=document;function C(){return P.__cmpCfg||{};}
function FL(){return P.__floor||null;}
var S=P.__cmp={ac:null,last:null,busy:false,lastScene:-1,tok:0,cid:0,mt:0,muted:false,hv:{r:0,s:0}};
try{S.muted=P.localStorage.getItem('cmpMuted')==='1';}catch(e){}
function hard(){var F=FL();return !!(F&&F.hard&&F.hard());}
function ac(){try{if(!S.ac){var X=P.AudioContext||P.webkitAudioContext;if(X)S.ac=new X();}if(S.ac&&S.ac.state==='suspended')S.ac.resume();}catch(e){}return S.ac;}
function tone(f1,f2,d,type,vol,at){var a=S.ac;if(!a||!C().sound||S.muted||hard())return;var t=a.currentTime+(at||0),o=a.createOscillator(),g=a.createGain();
 o.type=type;o.frequency.setValueAtTime(f1,t);o.frequency.exponentialRampToValueAtTime(f2,t+d);
 g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(vol,t+0.02);g.gain.exponentialRampToValueAtTime(0.0001,t+d);
 o.connect(g);g.connect(a.destination);o.start(t);o.stop(t+d+0.02);}
function hoverSnd(w){if(w==='r'){tone(740,1180,.11,'sine',.035);}else{tone(420,560,.12,'triangle',.035);}}
function clickSnd(w){if(w==='r'){tone(520,520,.07,'square',.025);tone(780,780,.07,'square',.025,.08);tone(1170,1170,.1,'square',.025,.16);}
 else{tone(392,392,.1,'triangle',.04);tone(523,523,.1,'triangle',.04,.1);tone(659,659,.14,'triangle',.04,.2);}}
function blip(w){if(w==='r'){tone(900,1300,.06,'sine',.03);}else{tone(330,420,.08,'triangle',.03);}}
// ---- صوت المتصفح العربي: احتياطي فقط إن لم يوجد مفتاح OpenAI (وإلا تُستعمل المقاطع الجاهزة بصوتيهما المميّزين) ----
var MALE=/hamed|naayf|taim|shakir|fahed|omar|hamza|maged|majed|salem|tarik|abdul|ahmed|saud|mohammed/i,FEM=/sana|zariyah|hoda|laila|salma|fatima|reem|amina|maryam|noura|hanan|rana|zeina|amira|sara/i;
function pickVoice(w){var V=(P.speechSynthesis&&P.speechSynthesis.getVoices())||[],ar=V.filter(function(v){return /^ar/i.test(v.lang);});if(!ar.length)return null;
 var best=null,bs=-99;ar.forEach(function(v){var sc=0;if(v.lang.toLowerCase()==='ar-sa')sc+=3;else if(/^ar-(jo|ae|eg)/i.test(v.lang))sc+=1;
 if(MALE.test(v.name))sc+=2;if(FEM.test(v.name))sc-=3;if(/natural|online/i.test(v.name))sc+=1;if(w==='s'&&/hamed|naayf/i.test(v.name))sc+=2;if(w==='r'&&/taim|shakir/i.test(v.name))sc+=2;
 if(sc>bs){bs=sc;best=v;}});return best;}
function clean(t){return t.replace(/[^؀-ۿݐ-ݿa-zA-Z0-9\s،.؟!:«»"-]/g,' ').replace(/\s+/g,' ').trim();}
function clipEl(k){return k?D.querySelector('.st-key-cmpa_'+k+' audio'):null;}
function haveClip(k){return !!clipEl(k);}
// ---- حركة الفم: تتبع موجة الصوت الفعلية (AnalyserNode) وتتوقف لحظة انتهاء الكلام ----
function startMouth(w,an){var c=D.querySelector('.cmp.'+w);if(!c)return;var tok=(S.mt=(S.mt||0)+1);c.dataset.sync='1';c.classList.add('talking');var buf=an?new Uint8Array(an.fftSize):null;
 (function f(){if(tok!==S.mt)return;var v;if(an){an.getByteTimeDomainData(buf);var s=0;for(var i=0;i<buf.length;i++){var d=(buf[i]-128)/128;s+=d*d;}v=Math.min(1,Math.sqrt(s/buf.length)*6.5);}
  else{v=.25+.6*Math.abs(Math.sin(Date.now()/90));}
  c.style.setProperty('--mo',v.toFixed(2));P.requestAnimationFrame(f);})();}
function stopMouth(){S.mt=(S.mt||0)+1;D.querySelectorAll('.cmp').forEach(function(c){c.classList.remove('talking');delete c.dataset.sync;c.style.setProperty('--mo','0');});}
function freeFloor(){var F=FL();if(F&&F.release)F.release('cmp');}
function stopSpeak(){S.cid=(S.cid||0)+1;try{if(P.speechSynthesis)P.speechSynthesis.cancel();}catch(e){}
 try{if(S.au){S.au.onended=null;S.au.onerror=null;S.au.onplaying=null;S.au.pause();S.au=null;}}catch(e){}stopMouth();}
// ---- النطق من مقاطع جاهزة بصوت كل شخصية (OpenAI) ----
function playClip(w,key,cb){stopSpeak();var id=(S.cid=(S.cid||0)+1);var el=clipEl(key);if(!el){return false;}var au=new P.Audio(el.currentSrc||el.src);au.preload='auto';au.volume=1;S.au=au;var fired=false,an=null;
 function end(){if(fired||id!==S.cid)return;fired=true;S.au=null;stopMouth();freeFloor();cb&&cb();}
 try{var a=ac();if(a&&a.state==='running'){var src=a.createMediaElementSource(au);an=a.createAnalyser();an.fftSize=512;src.connect(an);an.connect(a.destination);}}catch(e){an=null;}
 au.onended=end;au.onerror=end;au.onplaying=function(){if(id===S.cid)startMouth(w,an);};
 var p=au.play();if(p&&p.catch){p.catch(function(){end();});}
 P.setTimeout(end,40000);return true;}
// يرجع true (بدأ النطق) · false (بلا صوت: نص فقط) · null (رفض المنسّق: غيرهما يتكلم أو يُسجَّل أو تُكتب خانة)
function speak(w,text,cb,key,force){
 if(!C().voice||S.muted||!(P.navigator.userActivation&&P.navigator.userActivation.hasBeenActive)){return false;}
 var F=FL();if(F&&F.claim&&!F.claim('char','cmp',function(){abortScene('preempt');},0,!!force)){return null;}
 if(haveClip(key)){var ok=playClip(w,key,cb);if(!ok)freeFloor();return ok;}
 if(!C().fallback){freeFloor();return false;}
 var ss=P.speechSynthesis;if(!ss){freeFloor();return false;}
 try{stopSpeak();var u=new P.SpeechSynthesisUtterance(clean(text));var v=pickVoice(w);if(v){u.voice=v;u.lang=v.lang;}else{u.lang='ar-SA';}
  u.rate=(w==='r')?1.0:0.94;u.pitch=(w==='r')?1.08:0.88;u.volume=1;var fired=false;function end(){if(fired)return;fired=true;stopMouth();freeFloor();cb&&cb();}
  u.onstart=function(){startMouth(w,null);};u.onend=end;u.onerror=end;ss.speak(u);P.setTimeout(end,Math.max(6000,text.length*190));return true;}catch(e){freeFloor();return false;}}
if(P.speechSynthesis){try{P.speechSynthesis.onvoiceschanged=function(){};P.speechSynthesis.getVoices();}catch(e){}}
function who(el){return el.classList.contains('r')?'r':'s';}
D.addEventListener('pointerdown',function(){ac();},{passive:true});
S.lastMove=Date.now();S.lastAct=Date.now();S.lastAt=Date.now();
['pointerdown','keydown','touchstart'].forEach(function(ev){D.addEventListener(ev,function(){S.lastAct=Date.now();},{passive:true,capture:true});});
D.addEventListener('mousemove',function(e){S.lastMove=Date.now();D.querySelectorAll('.cmp').forEach(function(c){if(c.dataset.lock)return;var r=c.getBoundingClientRect();
 var cx=r.left+r.width/2,cy=r.top+r.height*0.3,dx=e.clientX-cx,dy=e.clientY-cy;var x=Math.max(-1,Math.min(1,dx/260)),y=Math.max(-1,Math.min(1,dy/260));
 c.style.setProperty('--ex',x.toFixed(2));c.style.setProperty('--ey',y.toFixed(2));
 var near=Math.sqrt(dx*dx+dy*dy)<340;c.style.setProperty('--lean',near?(Math.max(-1,Math.min(1,dx/200))*6).toFixed(1):'0');});},{passive:true});
P.setInterval(function(){if(Date.now()-S.lastMove<5000)return;D.querySelectorAll('.cmp').forEach(function(c){if(c.dataset.lock)return;
 c.style.setProperty('--ex',(Math.random()*1.6-0.8).toFixed(2));c.style.setProperty('--ey',(Math.random()*0.8-0.3).toFixed(2));c.style.setProperty('--lean','0');});},3800);
function sparks(c){for(var i=0;i<6;i++){var k=D.createElement('i');k.className='spk';k.style.left=(18+Math.random()*64)+'%';k.style.bottom=(40+Math.random()*50)+'%';
 k.style.setProperty('--dx',((Math.random()*50)-25).toFixed(0)+'px');c.appendChild(k);(function(n){setTimeout(function(){n.remove();},1200);})(k);}}
function popoverOpen(){return !!D.querySelector('[data-testid="stPopoverBody"]');}
// يصمتان تماماً: أثناء صوت المساعد أو تسجيل الميكروفون أو الكتابة (وفترة هدوء بعدها) أو عند فتح قائمة أو إخفاء الصفحة
function sysQuiet(){var F=FL();if(F&&F.canChar&&!F.canChar())return true;return D.hidden||popoverOpen();}
function hoverReact(c){var w=who(c);sparks(c);if(S.busy||S.muted||!C().talk||sysQuiet()||Date.now()-S.hv[w]<12000)return;var H=(C().hover||{})[w];if(!H||!H.length)return;
 var Hk=H.filter(sceneOk);if(!Hk.length)return;S.hv[w]=Date.now();var sc=Hk[Math.floor(Math.random()*Hk.length)];
 startScene(sc,function(){S.lastAt=Date.now();if(S.nextAt<Date.now()+20000)plan(20);});}
D.addEventListener('mouseover',function(e){var c=e.target.closest&&e.target.closest('.cmp');if(c&&c!==S.last){S.last=c;hoverSnd(who(c));hoverReact(c);}else if(!c){S.last=null;}},{passive:true});
function clearBubs(st){st.querySelectorAll('.bub').forEach(function(x){x.remove();});st.querySelectorAll('.cmp.talking').forEach(function(x){x.classList.remove('talking');});st.querySelectorAll('.cmp').forEach(function(x){delete x.dataset.lock;});}
function bubble(st,w,text,go,label){clearBubs(st);var b=D.createElement('div');b.className='bub '+w;
 var n=D.createElement('b');n.textContent=(w==='r'?'Bin3abdAi':'سعيدان السهلي');b.appendChild(n);b.appendChild(D.createTextNode(text));
 if(go){var a=D.createElement('a');a.className='go';a.textContent=label||'افتح';a.setAttribute('data-go',go);b.appendChild(a);}
 st.appendChild(b);var c=st.querySelector('.cmp.'+w),o=st.querySelector('.cmp.'+(w==='r'?'s':'r'));if(c){c.classList.add('talking');c.dataset.lock='1';c.style.setProperty('--ex','0');c.style.setProperty('--ey','-0.1');c.style.setProperty('--lean','0');}
 if(o){o.dataset.lock='1';o.style.setProperty('--ex',w==='r'?'-0.95':'0.95');o.style.setProperty('--ey','0.05');o.style.setProperty('--lean',w==='r'?'-4':'4');}return b;}
function openGo(key){var bb=[].slice.call(D.querySelectorAll('.st-key-pg_hidden button')).find(function(x){return x.textContent.indexOf(key)>-1;});if(bb){bb.click();return true;}return false;}
D.addEventListener('click',function(e){var g=e.target.closest&&e.target.closest('.bub .go');if(!g)return;e.preventDefault();ac();clickSnd('r');
 openGo(g.getAttribute('data-go'));abortScene('go');},true);
// ---- زر الكتم ----
function syncMute(){var b=D.querySelector('.cmp-mute');if(!b)return;b.textContent=S.muted?'🔇':'🔊';b.title=S.muted?'تشغيل صوت الشخصيتين وحوارهما':'كتم الشخصيتين';b.setAttribute('aria-pressed',S.muted?'true':'false');b.classList.toggle('off',S.muted);}
D.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('.cmp-mute');if(!b)return;e.preventDefault();e.stopPropagation();
 S.muted=!S.muted;try{P.localStorage.setItem('cmpMuted',S.muted?'1':'0');}catch(x){}if(S.muted){abortScene('mute');}else{plan(25);}syncMute();},true);
// ---- رد النقر: كلام قصير إلا إن كان المساعد يتكلم أو الميكروفون يسجّل (فحركة فقط) ----
function say(c){var st=c.parentNode,w=who(c);if(hard())return;var L=(C().react||{})[w];if(!L||!L.length)return;var it=L[Math.floor(Math.random()*L.length)];
 if(S.busy)abortScene('click');var my=(S.tok=(S.tok||0)+1);var b=bubble(st,w,it.t);setBusy(true);
 function done(){if(my!==S.tok)return;if(b.parentNode){clearBubs(st);}stopMouth();freeFloor();setBusy(false);S.lastAt=Date.now();if(S.nextAt<Date.now()+20000)plan(20);}
 var r=speak(w,it.t,function(){setTimeout(done,700);},it.a,true);
 if(r===null){abortScene('refused');return;}
 if(!r){setTimeout(done,2600);}}
D.addEventListener('click',function(e){var c=e.target.closest&&e.target.closest('.cmp');if(!c)return;ac();c.classList.remove('react');void c.offsetWidth;c.classList.add('react');
 setTimeout(function(){c.classList.remove('react');},850);say(c);clickSnd(who(c));},true);
D.addEventListener('dblclick',function(e){var c=e.target.closest&&e.target.closest('.cmp');if(!c)return;var b=D.querySelector('.st-key-fab_assistant button');if(b)b.click();},true);
function sceneOk(sc){if(!C().voice||C().fallback)return true;return sc.every(function(l){return haveClip(l.a);});}
function pick(idle){var pool=(idle&&C().idle&&C().idle.length)?C().idle:(C().scenes||[]);var ok=pool.filter(sceneOk);if(!ok.length)return null;pool=ok;var n=pool.length,i=0,t=0;do{i=Math.floor(Math.random()*n);t++;}while(i===S.lastScene&&n>1&&t<12);S.lastScene=i;return pool[i];}
// مشهد كامل: كل سطر يتحقق من المنسّق أولاً؛ أي صوت آخر أو تسجيل أو كتابة يُنهي المشهد فوراً بصمت
function playScene(sc,my,done){var i=0;(function next(){if(my!==S.tok)return;var st=D.querySelector('.cmp-stage');
 if(!st||i>=sc.length){if(st&&!(sc[sc.length-1]||{}).g){clearBubs(st);}freeFloor();done();return;}
 if(sysQuiet()){abortScene('quiet');return;}
 var L=sc[i++],last=(i>=sc.length);var b=bubble(st,L.w,L.t,L.g,L.l);blip(L.w);
 var minMs=Math.max(2600,L.t.length*60),t0=Date.now(),fin=false;
 function after(){if(fin||my!==S.tok)return;fin=true;var wait=Math.max(0,minMs-(Date.now()-t0))+350;
  setTimeout(function(){if(my!==S.tok)return;if(last&&L.g){setTimeout(function(){if(my!==S.tok)return;if(b.parentNode){clearBubs(st);}freeFloor();done();},5500);}else{next();}},wait);}
 var r=speak(L.w,L.t,after,L.a,false);
 if(r===null){abortScene('refused');return;}
 if(!r){setTimeout(function(){if(my===S.tok)stopMouth();},Math.min(minMs,L.t.length*70));setTimeout(after,Math.max(3300,L.t.length*80)-350);}})();}
// ---- جدولة واحدة: مؤقّت يفحص كل ثانيتين؛ لا يبدأ شيء أثناء أي صوت أو تسجيل أو كتابة ----
function plan(sec){var g=(sec!=null)?sec:((C().gapMin||60)+Math.random()*((C().gapMax||120)-(C().gapMin||60)));S.nextAt=Date.now()+g*1000;}
function setBusy(b){S.busy=b;S.busyAt=Date.now();}
function abortScene(why){S.tok=(S.tok||0)+1;setBusy(false);stopSpeak();freeFloor();var st=D.querySelector('.cmp-stage');if(st)clearBubs(st);S.lastAt=Date.now();plan(why==='stuck'?20:30);}
function startScene(sc,done){var my=(S.tok=(S.tok||0)+1);setBusy(true);playScene(sc,my,function(){if(my!==S.tok)return;setBusy(false);if(done)done();});}
function runScene(idle){var sc=pick(idle);if(!sc){plan();return;}startScene(sc,function(){S.lastAt=Date.now();plan();});}
function tick(){syncMute();if(!C().talk||S.muted||!D.querySelector('.cmp-stage'))return;var now=Date.now(),idleMs=C().idleMs||40000;
 if(S.busy){if(now-S.busyAt>90000){abortScene('stuck');}return;}
 if(sysQuiet()){if(S.nextAt<now+5000)S.nextAt=now+5000;return;}
 if(now-S.lastAct>idleMs&&now-S.lastAt>idleMs){runScene(true);return;}
 if(now>=S.nextAt){runScene(false);}}
P.addEventListener('floor-change',function(){var F=FL();if(F&&S.busy&&F.canChar&&!F.canChar()){abortScene('floor');}});
plan(C().first||8);S.lastAt=Date.now();S.busyAt=Date.now();syncMute();
P.setInterval(tick,2000);
})();"""

_LOADER = """<script>(function(){try{var P=window.parent,D=P.document;__FLOOR__
P.__cmpCfg=__CFG__;
if(P.__cmpVer&&P.__cmpVer!=='__VER__'){try{if(!P.sessionStorage.getItem('cmpR__VER__')){P.sessionStorage.setItem('cmpR__VER__','1');P.location.reload();return;}}catch(e){}}
if(P.__cmpVer==='__VER__')return;P.__cmpVer='__VER__';
var s=D.createElement('script');s.textContent=__CODE__;D.head.appendChild(s);}catch(e){}})();</script>"""

# للتوافق مع check_install (اسم قديم): نص المحمّل
_CMP_JS = _LOADER


# ======================================================
# أصوات الشخصيتين: مقاطع OpenAI (كل شخصية بصوتها المميّز) تُولَّد مرة واحدة وتُحفظ في مجلد character_voices
# ======================================================
_VOICE_DIR = Path(__file__).resolve().parent / "character_voices"  # مجلد المقاطع الجاهزة (يُنشأ تلقائياً)
_PERSONA = {"r": "nabras", "s": "saeed"}  # من يتكلم ← شخصية الصوت (nabras = Bin3abdAi · saeed = سعيدان)
_BYTES: dict = {}  # كاش في الذاكرة لمقاطع الصوت (بايت)
_WARM: dict = {}  # الدور ← وقت آخر بدء توليد (لتفادي تكرار الخيوط)


def _voice_of(w: str) -> str:  # اسم صوت OpenAI لهذه الشخصية (يدخل في معرّف المقطع فيُعاد توليده عند تغيير الصوت من .env)
    try:
        from ai_service import PERSONAS
        return str(PERSONAS[_PERSONA[w]]["openai"])
    except Exception:
        return ""


def _key(w: str, text: str) -> str:  # معرّف ثابت لسطر الحوار: الشخصية + صوتها + النص
    return hashlib.sha1(f"v3|{_PERSONA.get(w, w)}|{_voice_of(w)}|{text}".encode("utf-8")).hexdigest()[:14]


def _ann_scene(sc: list) -> list:  # يضيف معرّف المقطع الصوتي لكل سطر
    return [dict(l, a=_key(l["w"], l["t"])) for l in sc]


def _react_ann() -> dict:
    return {w: [{"t": t, "a": _key(w, t)} for t in lst] for w, lst in _REACT.items()}


def _hover_ann() -> dict:
    return {w: [_ann_scene(sc) for sc in lst] for w, lst in _HOVER.items()}


def _scenes_for(role: str) -> list:  # المشاهد المناسبة للدور: العامة + مشاهد الدور (مكرّرة ليكثر ظهورها)
    """المشاهد المناسبة للدور: العامة + مشاهد الدور (مكرّرة لتكثر)، وفي كل سطر معرّف مقطعه الصوتي a."""
    own = _SCENES.get(role) or []
    return [_ann_scene(sc) for sc in _SCENES["common"] + own + own]


def _lines_for(role: str) -> list:  # كل أسطر الشخصيتين لهذا الدور: [(المتحدث، النص، المعرّف)]
    seen, out = set(), []
    groups = [sc for sc in _SCENES["common"] + (_SCENES.get(role) or []) + _IDLE]
    groups += [sc for lst in _HOVER.values() for sc in lst]
    for sc in groups:
        for l in sc:
            k = _key(l["w"], l["t"])
            if k not in seen:
                seen.add(k)
                out.append((l["w"], l["t"], k))
    for w, lst in _REACT.items():
        for t in lst:
            k = _key(w, t)
            if k not in seen:
                seen.add(k)
                out.append((w, t, k))
    return out


def _clip_path(k: str) -> Path:
    return _VOICE_DIR / f"{k}.mp3"


def _make_clips(lines: list) -> int:  # يولّد المقاطع الناقصة (4 في آنٍ واحد) ويحفظها؛ يرجع عدد ما وُلّد
    from concurrent.futures import ThreadPoolExecutor

    from ai_service import _plain_speech, client, synthesize_speech
    if client is None:
        return 0
    _VOICE_DIR.mkdir(exist_ok=True)
    todo = [ln for ln in lines if not _clip_path(ln[2]).exists()]

    def one(item) -> int:
        w, t, k = item
        try:
            audio = synthesize_speech(_plain_speech(t), persona=_PERSONA[w])  # صوت الشخصية ونبرتها من ai_service.PERSONAS
        except Exception:
            audio = b""
        if not audio:
            return 0
        f = _clip_path(k)
        tmp = f.with_suffix(".tmp")
        tmp.write_bytes(audio)
        os.replace(tmp, f)
        return 1

    if not todo:
        return 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        return sum(ex.map(one, todo))


def _all_lines() -> list:  # كل أسطر كل الأدوار بلا تكرار
    allines, seen = [], set()
    for r in _SCENES:
        for ln in _lines_for(r):
            if ln[2] not in seen:
                seen.add(ln[2])
                allines.append(ln)
    return allines


def warm_all(clean: bool = False) -> None:  # تجهيز كل أصوات الشخصيتين دفعة واحدة:  python characters.py
    allines = _all_lines()
    print(f"عدد الأسطر: {len(allines)}")
    print("تم توليد", _make_clips(allines), "مقطع جديد في", _VOICE_DIR)
    keep = {k for _, _, k in allines}
    old = [f for f in _VOICE_DIR.glob("*.mp3") if f.stem not in keep] if _VOICE_DIR.exists() else []
    if old and clean:
        for f in old:
            f.unlink()
        print(f"حُذف {len(old)} مقطعاً قديماً غير مستعمل.")
    elif old:
        print(f"يوجد {len(old)} مقطعاً قديماً غير مستعمل (من نسخ سابقة). لحذفها:  python characters.py --clean")


def _start_warm(role: str, lines: list) -> None:  # يشغّل التوليد في الخلفية مرة لكل دور (لا يعطّل الصفحة)
    from ai_service import client
    if client is None or time.time() - _WARM.get(role, 0) < 900:
        return
    if all(_clip_path(k).exists() for _, _, k in lines):
        return
    _WARM[role] = time.time()
    threading.Thread(target=_make_clips, args=(lines,), daemon=True).start()


def _clip_bytes(k: str) -> bytes:  # بايتات المقطع (من الكاش أو القرص)
    if k in _BYTES:
        return _BYTES[k]
    f = _clip_path(k)
    if not f.exists():
        return b""
    try:
        _BYTES[k] = f.read_bytes()
    except Exception:
        return b""
    return _BYTES[k]


def companions(role: str) -> None:  # الشخصيتان Bin3abdAi وسعيدان: حوار كل دقيقة تقريباً، تفاعل مع المؤشر واللمس، أصوات، وروابط مساعدة
    """الشخصيتان Bin3abdAi وسعيدان: حوار كل دقيقة تقريباً بأسلوب كوميدي محترم، تفاعل مع المؤشر واللمس، وروابط مساعدة.
    تصمتان أثناء صوت المساعد أو الميكروفون أو الكتابة (منسّق الصوت floor.py)."""
    if st.session_state.get("show_chars") is False or st.session_state.get("reduce_motion"):
        return
    st.markdown(_CSS + '<div class="cmp-stage" aria-label="Bin3abdAi وسعيدان">'
                f'<div class="cmp r" title="Bin3abdAi">{_ROBOT_SVG}</div><div class="cmp s" title="سعيدان السهلي">{_SAUDI_SVG}</div>'
                '<button class="cmp-mute" type="button" title="كتم الشخصيتين" aria-label="كتم الشخصيتين" aria-pressed="false">🔊</button></div>',
                unsafe_allow_html=True)
    cfg = {"sound": bool(st.session_state.get("ui_sounds", True)), "voice": bool(st.session_state.get("chars_voice", True)), "talk": True, "first": FIRST_DELAY,
           "gapMin": GAP_MIN, "gapMax": GAP_MAX, "scenes": _scenes_for(role), "react": _react_ann(), "hover": _hover_ann(),
           "idle": [_ann_scene(sc) for sc in _IDLE], "idleMs": IDLE_SECONDS * 1000}
    try:
        from ai_service import client
        cfg["fallback"] = client is None  # بلا مفتاح OpenAI نستخدم صوت المتصفح؛ ومعه المفتاح نستخدم المقاطع الجاهزة فقط
        lines = _lines_for(role)
        _start_warm(role, lines)  # يولّد الناقص بالخلفية (أول مرة فقط)
        # المقاطع تُعرض كعناصر st.audio مخفية (روابط صغيرة تحمّلها الصفحة عند الحاجة) بدل تضمينها كلها داخل الصفحة (كانت ميغابايتات تُبطئ الصفحة وتعطّل الشخصيتين)
        with st.container(key="cmp_audio"):
            for _, _, k in lines:
                data = _clip_bytes(k)
                if data:
                    try:
                        with st.container(key=f"cmpa_{k}"):
                            st.audio(data, format="audio/mp3")
                    except Exception:  # تعذّر عرض مقطع واحد لا يمنع بقية المقاطع ولا الحوار
                        continue
    except Exception:
        cfg["fallback"] = True
    code = json.dumps(_ENGINE, ensure_ascii=False).replace("</", "<\\/")  # نص آمن داخل وسم script
    page = (_LOADER.replace("__FLOOR__", boot_js())
            .replace("__CFG__", json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__VER__", _ENGINE_VER).replace("__CODE__", code))
    with st.container(key="cmp_js"):  # iframe صفري الحجم لا يؤثر على التخطيط
        components.html(page, height=0)


if __name__ == "__main__":  # python characters.py  ← يجهّز أصوات الشخصيتين مرة واحدة (--clean يحذف المقاطع القديمة غير المستعملة)
    import sys
    warm_all(clean="--clean" in sys.argv)
