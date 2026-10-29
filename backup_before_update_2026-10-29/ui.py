"""طبقة الواجهة: الثيم الفاخر (زجاج داكن + لمسات ذهبية وسماوية) + مكونات مشتركة.

وظيفة هذا الملف: كل ما يخص «الشكل» فقط. لا حسابات ولا بيانات هنا.
الأسماء العامة التي تستخدمها بقية الملفات: PALETTE, inject_theme, card, style_fig, top_banner.
"""
import html  # لتعقيم أي نص خارجي قبل وضعه داخل HTML

import streamlit as st
import streamlit.components.v1 as components  # مكتبة الواجهة

from config import APP_NAME, APP_TAGLINE, APP_VERSION, DEVELOPER_SIGNATURE  # اسم المنصة من مصدر واحد
from security import AuthContext  # سياق المستخدم (لعرض اسمه وصلاحيته في الشريط العلوي)

# ألوان الرسوم البيانية: ذهبي، زمردي، فيروزي، أخضر فاتح، وردي
PALETTE = ["#d4af37", "#1f9d62", "#22d3ee", "#7ddba3", "#f43f5e"]

# ======================================================
# أنماط المنصة (يختارها المستخدم). كل نمط = مجموعة متغيّرات ألوان فقط؛ بقية CSS واحدة تقرأ المتغيّرات.
# الأنماط الأربعة: «داكن زجاجي» (كحلي ليلي بلمسة ذهبية)، «فاتح هادئ» (الافتراضي)، «رملي»، «بحري». بلا نجوم في أي نمط.
# ======================================================
THEMES = ["داكن زجاجي (ليلي)", "فاتح هادئ (أخضر)", "رملي مريح للعين", "أزرق بحري رسمي"]  # الأول هو الافتراضي (الداكن الذي تفضّله)؛ بلا نجوم في كلها

_LIGHT = {"فاتح", "رملي", "بحري"}  # الأنماط الفاتحة (تحتاج قلب الجداول وألوان رسوم داكنة)

_VARS = {
    "داكن": dict(  # كحلي ليلي زجاجي + ذهبي وفيروزي (كما في التصميم الأصلي لكن بلا نجوم)
        bg0="#060a16", bg1="#0a1226", bg2="#101a35",
        glow1="rgba(34,211,238,.10)", glow2="rgba(224,184,76,.07)", glow3="rgba(99,102,241,.10)",
        aur1="rgba(34,211,238,.16)", aur2="rgba(224,184,76,.12)", aur3="rgba(99,102,241,.18)", pat_op=".05",
        accent="#e0b84c", accent2="#22d3ee", accent3="#f3d77a", text="#eef4ff", muted="#aebbd6",
        line="rgba(148,163,184,.24)", glass="rgba(11,19,40,.78)",
        card_a="rgba(24,38,72,.60)", card_b="rgba(8,14,30,.86)",
        ai_a="rgba(224,184,76,.13)", ai_b="rgba(8,14,30,.88)", ai_border="rgba(224,184,76,.5)", ai_tag="#f3d77a",
        ban_a="rgba(22,38,78,.92)", ban_b="rgba(8,14,30,.88)",
        btn_a="#e8c25a", btn_b="#b8921a", btn_text="#0a1226", btn_border="rgba(243,215,122,.7)", btn_glow="rgba(224,184,76,.28)",
        tab_bg="rgba(8,14,30,.72)", tab_a="#f3d77a", tab_b="#e0b84c", tab_text="#0a1226",
        input_bg="rgba(8,14,30,.78)", input_text="#eef4ff",
        side_a="#0b1530", side_b="#060b1c", side_text="#eef4ff", head="#f3d77a",
        h1a="#ffffff", h1b="#f3d77a", h1c="#e0b84c", ok_text="#6ee7b7", warn_text="#fda4af", pink_text="#f9a8d4",
        t1="#f1f5f9", t2="#cbd5e1", t3="#94a3b8", good="#6ee7b7", amber="#fcd34d", bad="#fda4af",
        surf="rgba(255,255,255,.05)", surf_line="rgba(148,163,184,.2)", shadow="rgba(0,0,0,.55)",
        hero_a="rgba(6,12,30,.86)", hero_b="rgba(14,30,66,.70)", hero_c="rgba(70,52,6,.50)", hero_base="#050a18"),
    "فاتح": dict(  # أبيض مخضرّ هادئ: الأنسب للعمل الطويل
        bg0="#e6eeea", bg1="#f5f8f7", bg2="#dbe7e1",
        glow1="rgba(15,122,85,.06)", glow2="rgba(15,122,85,.05)", glow3="rgba(184,146,26,.05)",
        aur1="rgba(15,122,85,.14)", aur2="rgba(184,146,26,.12)", aur3="rgba(34,160,120,.12)", pat_op=".07",
        accent="#0f7a55", accent2="#0f7a55", accent3="#0a5c3f", text="#14231c", muted="#51655a",
        line="rgba(15,122,85,.22)", glass="rgba(255,255,255,.86)",
        card_a="#ffffff", card_b="#f3f7f5",
        ai_a="#e8f5ef", ai_b="#d5eadf", ai_border="rgba(15,122,85,.5)", ai_tag="#0a5c3f",
        ban_a="#e1f0e8", ban_b="#d1e6db",
        btn_a="#13805a", btn_b="#0b5b40", btn_text="#ffffff", btn_border="#0b5b40", btn_glow="rgba(15,122,85,.25)",
        tab_bg="#e0ebe6", tab_a="#13805a", tab_b="#0b5b40", tab_text="#ffffff",
        input_bg="#ffffff", input_text="#14231c",
        side_a="#0e4a36", side_b="#093526", side_text="#f2fff9", head="#0b4a35",
        h1a="#0b4a35", h1b="#0f7a55", h1c="#b8921a", ok_text="#0b4a35", warn_text="#9f1239", pink_text="#9d174d",
        t1="#14231c", t2="#2f4339", t3="#566b60", good="#0b6b46", amber="#92400e", bad="#9f1239",
        surf="rgba(15,122,85,.06)", surf_line="rgba(15,122,85,.18)", shadow="rgba(20,60,45,.22)",
        hero_a="rgba(2,30,20,.86)", hero_b="rgba(6,60,40,.68)", hero_c="rgba(70,52,6,.50)", hero_base="#04251a"),
    "رملي": dict(  # كريمي دافئ قليل الوهج: مريح للعين
        bg0="#ece3d0", bg1="#f8f4ea", bg2="#e6dac1",
        glow1="rgba(138,106,47,.07)", glow2="rgba(79,107,58,.05)", glow3="rgba(138,106,47,.05)",
        aur1="rgba(184,146,60,.18)", aur2="rgba(79,107,58,.12)", aur3="rgba(205,150,90,.14)", pat_op=".08",
        accent="#8a6a2f", accent2="#4f6b3a", accent3="#6b5222", text="#2a2417", muted="#6a5f48",
        line="rgba(138,106,47,.30)", glass="rgba(255,253,247,.88)",
        card_a="#fffdf7", card_b="#f7f0e1",
        ai_a="#f6ecd2", ai_b="#ecdcb4", ai_border="rgba(138,106,47,.5)", ai_tag="#5d4519",
        ban_a="#efe4c8", ban_b="#e6d6b0",
        btn_a="#56743f", btn_b="#364c27", btn_text="#ffffff", btn_border="#364c27", btn_glow="rgba(79,107,58,.25)",
        tab_bg="#e9dfc8", tab_a="#56743f", tab_b="#364c27", tab_text="#ffffff",
        input_bg="#fffdf7", input_text="#2a2417",
        side_a="#3a3322", side_b="#262114", side_text="#fbf6e9", head="#4a3a14",
        h1a="#4a3a14", h1b="#4f6b3a", h1c="#8a6a2f", ok_text="#364c27", warn_text="#9f1239", pink_text="#9d174d",
        t1="#2a2417", t2="#473f2b", t3="#6f6450", good="#364c27", amber="#92400e", bad="#9f1239",
        surf="rgba(138,106,47,.07)", surf_line="rgba(138,106,47,.22)", shadow="rgba(90,66,20,.22)",
        hero_a="rgba(40,30,10,.86)", hero_b="rgba(70,56,24,.66)", hero_c="rgba(40,70,30,.45)", hero_base="#2a2010"),
    "بحري": dict(  # أزرق رسمي هادئ بلمسة حكومية
        bg0="#e2eaf3", bg1="#f2f6fa", bg2="#d6e2ee",
        glow1="rgba(31,95,158,.06)", glow2="rgba(31,95,158,.05)", glow3="rgba(184,146,26,.04)",
        aur1="rgba(31,107,176,.15)", aur2="rgba(184,146,26,.10)", aur3="rgba(80,140,210,.14)", pat_op=".07",
        accent="#1f5f9e", accent2="#1f5f9e", accent3="#164a7c", text="#12202f", muted="#4d6075",
        line="rgba(31,95,158,.24)", glass="rgba(255,255,255,.88)",
        card_a="#ffffff", card_b="#eef3f9",
        ai_a="#e1ecf8", ai_b="#cfe0f1", ai_border="rgba(31,95,158,.5)", ai_tag="#164a7c",
        ban_a="#dbe8f4", ban_b="#cbdef0",
        btn_a="#1f6bb0", btn_b="#154a80", btn_text="#ffffff", btn_border="#154a80", btn_glow="rgba(31,95,158,.25)",
        tab_bg="#d9e5f1", tab_a="#1f6bb0", tab_b="#154a80", tab_text="#ffffff",
        input_bg="#ffffff", input_text="#12202f",
        side_a="#10304f", side_b="#0a2038", side_text="#f1f7ff", head="#12365a",
        h1a="#12365a", h1b="#1f6bb0", h1c="#b8921a", ok_text="#0b5b40", warn_text="#9f1239", pink_text="#9d174d",
        t1="#12202f", t2="#2c4058", t3="#566b82", good="#0b6b46", amber="#92400e", bad="#9f1239",
        surf="rgba(31,95,158,.06)", surf_line="rgba(31,95,158,.2)", shadow="rgba(16,48,90,.22)",
        hero_a="rgba(6,24,52,.88)", hero_b="rgba(14,50,96,.68)", hero_c="rgba(70,52,6,.45)", hero_base="#07203f"),
}

def _is_light(key: str) -> bool:  # هل النمط فاتح؟ (يحدد قلب الجداول وألوان الرسوم)
    return key in _LIGHT


def theme_key() -> str:  # مفتاح النمط الحالي (داكن | فاتح | رملي | بحري). الافتراضي: فاتح. القيم القديمة (وطني...) تُعامل كالافتراضي.
    """مفتاح النمط الحالي (داكن | فاتح | رملي | بحري). الافتراضي: داكن."""
    t = st.session_state.get("theme") or THEMES[0]
    for k in _VARS:  # يطابق اسم النمط من أوله أو من داخله (مثل «أزرق بحري رسمي» ← بحري)
        if str(t).startswith(k):
            return k
    for k in _VARS:
        if k in str(t):
            return k
    return "داكن"


def _stars_shadow(n: int, seed: int, c1: str, c2: str, glow: bool) -> str:  # نجوم عشوائية ثابتة (box-shadow) بمواضع نسبية لحجم الشاشة
    """نجوم عشوائية ثابتة (box-shadow) بمواضع نسبية لحجم الشاشة."""
    import random
    r = random.Random(seed)
    out = []
    for i in range(n):
        col = c1 if i % 4 else c2
        out.append(f"{r.randint(0, 100)}vw {r.randint(0, 100)}vh {'0 1px' if glow else '0 0'} {col}" if not glow
                   else f"{r.randint(0, 100)}vw {r.randint(0, 100)}vh 5px 1px {col}")
    return ",".join(out)


_LIGHT_EXTRA = """<style>/*nofix*/
[data-testid='stDataFrame']{filter:invert(.93) hue-rotate(180deg);}
.glass-card,.ai-card-glow,.security-banner{box-shadow:0 8px 24px -14px rgba(20,40,30,.28),inset 0 1px 0 rgba(255,255,255,.8) !important;}
[data-testid="stMetric"],.stMetric{box-shadow:0 6px 18px -12px rgba(20,40,30,.3) !important;}
button[data-baseweb="tab"]:hover{background:rgba(0,0,0,.06) !important;}
.ops-card.danger b{color:#9f1239}.ops-card.warn b{color:#92400e}.ops-card.info b{color:var(--accent3)}.ops-card.ok b{color:#0b6b46}
.sev-red{color:#9f1239}.sev-amber{color:#92400e}
.ops-card::after{display:none}
</style>"""


def _pattern(color: str) -> str:  # نقشة معيّنات هندسية خفيفة (تشبه الزخارف النجدية والعسيرية) كخلفية بلا نجوم
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64'><path d='M32 0 64 32 32 64 0 32Z' fill='none' stroke='{color}' stroke-width='1'/>"
           f"<path d='M32 15 49 32 32 49 15 32Z' fill='none' stroke='{color}' stroke-width='.6'/></svg>")
    return "url(\"data:image/svg+xml;utf8," + svg.replace("#", "%23").replace("<", "%3C").replace(">", "%3E") + "\")"


def _vars_css(key: str) -> str:  # يحوّل متغيرات النمط الحالي إلى CSS (بلا نجوم في أي نمط)
    v = _VARS[key]
    root = ":root{" + "".join(f"--{k.replace('_', '-')}:{val};" for k, val in v.items()) + f"--pattern:{_pattern(v['accent'])};" + "}"
    extra = _LIGHT_EXTRA if _is_light(key) else ""
    return f"<style>/*nofix*/{root}</style>{extra}"


_BASE_CSS = """
<style>/*nofix*/
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap');
.stApp{isolation:isolate;
  background:
    radial-gradient(900px 500px at 85% -10%, var(--glow1), transparent 60%),
    radial-gradient(800px 480px at 5% 0%, var(--glow2), transparent 60%),
    radial-gradient(700px 400px at 50% 110%, var(--glow3), transparent 60%),
    linear-gradient(180deg,var(--bg1),var(--bg0)) !important;
  color:var(--text) !important; direction:rtl; text-align:right;
  font-family:'IBM Plex Sans Arabic','Segoe UI',Tahoma,sans-serif;}
/* (أُزيلت المجرة والنجوم من كل الأنماط بطلب المستخدم) — بدلها «شفق» هادئ ونقشة معيّنات خفيفة جداً */
.stApp::before{content:"";position:fixed;inset:-15%;z-index:-2;pointer-events:none;filter:blur(34px);
  background:radial-gradient(38% 34% at 18% 22%,var(--aur1),transparent 70%),radial-gradient(34% 30% at 82% 18%,var(--aur2),transparent 70%),
             radial-gradient(40% 38% at 62% 92%,var(--aur3),transparent 70%);animation:aurora 26s ease-in-out infinite alternate;}
.stApp::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:var(--pat-op);background-image:var(--pattern);background-size:64px 64px;
  -webkit-mask-image:linear-gradient(180deg,#000 0%,transparent 75%);mask-image:linear-gradient(180deg,#000 0%,transparent 75%);}
@keyframes aurora{0%{transform:translate3d(-2%,0,0) scale(1)}100%{transform:translate3d(3%,2%,0) scale(1.08)}}
::selection{background:var(--accent);color:var(--btn-text);}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}
[data-testid="stMainBlockContainer"]{animation:pagein .55s ease both;}
@keyframes pagein{from{opacity:0}to{opacity:1}}
div[data-testid="stAppViewContainer"]{direction:rtl;text-align:right;padding:6px 18px;background:transparent !important;}
[data-testid="stMain"]{background:transparent !important;}
header[data-testid="stHeader"]{background:transparent !important;}
h1,h2,h3,h4{letter-spacing:-.2px;font-weight:700 !important;}
h1{background:linear-gradient(90deg,var(--h1a),var(--h1b) 45%,var(--h1c));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
h2,h3,h4,h5{color:var(--head) !important;}
a{color:var(--accent3) !important;}
hr{border-color:var(--line) !important;}
::-webkit-scrollbar{width:9px;height:9px}::-webkit-scrollbar-thumb{background:var(--line);border-radius:9px}

/* ===== وضوح النصوص (يمنع النص الباهت في كل الأنماط) ===== */
[data-testid="stMarkdownContainer"],[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong,[data-testid="stMarkdownContainer"] em,
[data-testid="stWidgetLabel"],[data-testid="stWidgetLabel"] p,label,label p,
div[role="radiogroup"] label *,[data-testid="stCheckbox"] *,[data-testid="stToggle"] *,
[data-testid="stExpander"] summary *,[data-testid="stForm"] label *,[data-testid="stAlert"] *,
[data-testid="stSelectbox"] label *,[data-testid="stTextInput"] label *{color:var(--text) !important;}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *,small{color:var(--muted) !important;}
[data-testid="stMarkdownContainer"] h2,[data-testid="stMarkdownContainer"] h3,[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5{color:var(--head) !important;}

/* ===== البطاقات ===== */
.glass-card,.ai-card-glow,.security-banner,.top-banner{position:relative;backdrop-filter:blur(20px) saturate(140%);
  -webkit-backdrop-filter:blur(20px) saturate(140%);border-radius:20px;margin-bottom:20px;color:var(--text);}
.glass-card{background:linear-gradient(145deg,var(--card-a),var(--card-b));border:1px solid var(--line);padding:22px 24px;
  box-shadow:0 18px 40px -16px var(--shadow),inset 0 1px 0 rgba(255,255,255,.07);transition:transform .3s ease,box-shadow .3s ease,border-color .3s;}
.glass-card:hover{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 26px 50px -18px var(--shadow);}
.glass-card::before{content:"";position:absolute;top:0;right:24px;left:24px;height:2px;border-radius:2px;
  background:linear-gradient(90deg,transparent,var(--accent),var(--accent3),transparent);opacity:.8;}
.ai-card-glow{background:linear-gradient(145deg,var(--ai-a),var(--ai-b));padding:22px 24px;border:1px solid var(--ai-border);margin-top:14px;
  box-shadow:0 20px 50px -14px var(--ai-border);}
.ai-card-glow::after{content:"AI";position:absolute;top:12px;left:16px;font-size:.68rem;font-weight:700;letter-spacing:2px;color:var(--ai-tag);
  border:1px solid var(--ai-border);border-radius:20px;padding:1px 9px;background:rgba(255,255,255,.06);}
.security-banner{background:linear-gradient(135deg,var(--ban-a),var(--ban-b));padding:20px 24px;border:1px solid var(--line);
  box-shadow:0 18px 40px -14px var(--line);}
.top-banner{background:linear-gradient(120deg,var(--ban-a),var(--ban-b));padding:16px 26px;border:1px solid var(--line);
  display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;}
.brand{font-weight:700;font-size:1.25rem;background:linear-gradient(90deg,var(--accent),var(--accent3));-webkit-background-clip:text;
  background-clip:text;-webkit-text-fill-color:transparent;}
.brand-sub{color:var(--muted);font-size:.85rem;margin-right:14px;}
div[data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,var(--card-a),var(--card-b));border-color:var(--line) !important;
  border-radius:18px !important;}

/* ===== الإشعارات والشارات ===== */
.notice{padding:14px 18px;border-radius:14px;margin-bottom:14px;font-weight:600;}
.notice-ok{background:rgba(16,185,129,.14);border:1px solid rgba(16,185,129,.4);border-right:5px solid #10b981;color:var(--ok-text);}
.notice-warn{background:rgba(244,63,94,.12);border:1px solid rgba(244,63,94,.4);border-right:5px solid #f43f5e;color:var(--warn-text);}
.notice-pink{background:rgba(236,72,153,.13);border:1px solid rgba(236,72,153,.4);border-right:5px solid #ec4899;color:var(--pink-text);}
.badge-status,.auth-chip{display:inline-block;padding:5px 15px;border-radius:25px;font-size:.82rem;font-weight:600;margin-left:8px;}
.badge-green{background:linear-gradient(135deg,#10b981,#047857);color:#fff;}
.badge-orange{background:linear-gradient(135deg,#d4af37,#9a7b12);color:#1c1500;}
.badge-red{background:linear-gradient(135deg,#f43f5e,#be123c);color:#fff;}
.auth-on{background:rgba(16,185,129,.16);border:1px solid #10b981;color:var(--ok-text);}
.auth-off{background:rgba(244,63,94,.14);border:1px solid #f43f5e;color:var(--warn-text);}

/* ===== المؤشرات ===== */
[data-testid="stMetric"],.stMetric{background:linear-gradient(145deg,var(--card-a),var(--card-b));padding:20px 22px;border-radius:18px;
  border:1px solid var(--line);border-right:4px solid var(--accent);box-shadow:0 14px 30px -14px var(--shadow);transition:transform .25s,box-shadow .25s;}
[data-testid="stMetric"]:hover{transform:translateY(-3px);box-shadow:0 20px 40px -12px var(--line);}
[data-testid="stMetricValue"],[data-testid="stMetricValue"] *{font-weight:700 !important;color:var(--head) !important;}
[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] *{color:var(--muted) !important;}

/* ===== التبويبات ===== */
div[data-baseweb="tab-list"]{gap:6px;background:var(--tab-bg);padding:6px;border-radius:16px;border:1px solid var(--line);}
button[data-baseweb="tab"]{border-radius:12px !important;padding:8px 16px !important;background:transparent !important;transition:all .2s;font-weight:500;}
button[data-baseweb="tab"],button[data-baseweb="tab"] *{color:var(--text) !important;}
button[data-baseweb="tab"]:hover{background:rgba(255,255,255,.1) !important;}
button[data-baseweb="tab"][aria-selected="true"]{background:linear-gradient(135deg,var(--tab-a),var(--tab-b)) !important;box-shadow:0 6px 20px var(--btn-glow);}
button[data-baseweb="tab"][aria-selected="true"],button[data-baseweb="tab"][aria-selected="true"] *{color:var(--tab-text) !important;font-weight:700 !important;}
div[data-baseweb="tab-highlight"],div[data-baseweb="tab-border"]{display:none !important;}

/* ===== الأزرار ===== */
.stButton button,.stFormSubmitButton button,.stDownloadButton button,[data-testid="stPopover"] button{
  background:linear-gradient(135deg,var(--btn-a),var(--btn-b)) !important;border-radius:12px !important;font-weight:600 !important;
  border:1px solid var(--btn-border) !important;box-shadow:0 6px 20px var(--btn-glow) !important;transition:all .25s ease;}
.stButton button *,.stFormSubmitButton button *,.stDownloadButton button *,[data-testid="stPopover"] button *{color:var(--btn-text) !important;}
.stButton button,.stFormSubmitButton button,.stDownloadButton button{position:relative;overflow:hidden;}
.stButton button::after,.stFormSubmitButton button::after,.stDownloadButton button::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(110deg,transparent 35%,rgba(255,255,255,.28) 50%,transparent 65%);transform:translateX(-130%);transition:transform .6s;}
.stButton button:hover::after,.stFormSubmitButton button:hover::after,.stDownloadButton button:hover::after{transform:translateX(130%);}
.stButton button:hover,.stFormSubmitButton button:hover,.stDownloadButton button:hover{transform:translateY(-2px);filter:brightness(1.08);}
.stButton button:disabled{opacity:.45;filter:grayscale(.5);}

/* ===== الحقول والقوائم والتسجيل ===== */
.stTextInput input,.stTextArea textarea,.stNumberInput input,div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,
[data-testid="stAudioInput"],[data-testid="stFileUploaderDropzone"]{background:var(--input-bg) !important;color:var(--input-text) !important;
  border:1px solid var(--line) !important;border-radius:12px !important;}
.stTextInput input,.stTextArea textarea,.stNumberInput input,div[data-baseweb="select"] *{color:var(--input-text) !important;}
[data-testid="stAudioInput"] *,[data-testid="stFileUploaderDropzone"] *{color:var(--input-text) !important;}
.stTextInput input:focus,.stTextArea textarea:focus{border-color:var(--accent) !important;box-shadow:0 0 0 3px var(--btn-glow) !important;}
div[data-baseweb="popover"] > div,ul[role="listbox"]{background:var(--bg1) !important;border:1px solid var(--line);}
li[role="option"],li[role="option"] *{color:var(--text) !important;}
li[role="option"]:hover{background:var(--card-a) !important;}
div[data-testid="stPopoverBody"]{background:linear-gradient(180deg,var(--bg1),var(--bg0)) !important;border:1px solid var(--line);color:var(--text);}
div[role="dialog"]{background:linear-gradient(180deg,var(--bg1),var(--bg0)) !important;border:1px solid var(--line);}

/* ===== الشريط الجانبي ===== */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,var(--side-a),var(--side-b)) !important;border-left:1px solid var(--line);}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,section[data-testid="stSidebar"] label *,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,section[data-testid="stSidebar"] summary *{color:var(--side-text) !important;}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3{color:#f3d77a !important;}
section[data-testid="stSidebar"] .stTextInput input,section[data-testid="stSidebar"] div[data-baseweb="select"]>div{background:rgba(255,255,255,.1) !important;}
section[data-testid="stSidebar"] .stTextInput input,section[data-testid="stSidebar"] div[data-baseweb="select"] *{color:#f4fff8 !important;}
section[data-testid="stSidebar"] [data-testid="stAudioInput"]{background:rgba(255,255,255,.08) !important;}

/* ===== الجداول والمحادثة ===== */
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden;}
[data-testid="stChatMessage"]{background:var(--card-a);border:1px solid var(--line);border-radius:16px;}
div[data-testid="stAlert"]{border-radius:14px;}
div[data-testid="stExpander"]{border:1px solid var(--line) !important;border-radius:14px;background:var(--card-a);}
[data-testid="stPlotlyChart"]{background:var(--card-a);border:1px solid var(--line);border-radius:16px;padding:6px;}

/* ===== غرفة العمليات الحية ===== */
.live-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;color:var(--muted);font-size:.85rem;margin-bottom:10px}
.live-dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:#10b981;margin-left:8px;animation:livepulse 1.4s infinite}
@keyframes livepulse{0%{box-shadow:0 0 0 0 rgba(16,185,129,.75)}70%{box-shadow:0 0 0 11px rgba(16,185,129,0)}100%{box-shadow:0 0 0 0 rgba(16,185,129,0)}}
.ops-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-bottom:14px}
.ops-card{position:relative;overflow:hidden;padding:14px 18px;border-radius:16px;border:1px solid var(--line);background:linear-gradient(145deg,var(--card-a),var(--card-b))}
.ops-card span{display:block;color:var(--muted);font-size:.82rem}
.ops-card b{display:block;font-size:1.9rem;font-variant-numeric:tabular-nums;margin-top:2px}
.ops-card::after{content:"";position:absolute;top:0;left:-60%;width:40%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.08),transparent);animation:sweep 4.5s infinite}
@keyframes sweep{to{left:130%}}
.ops-card.danger{border-color:rgba(244,63,94,.55)}.ops-card.danger b{color:#fda4af}
.ops-card.warn{border-color:rgba(245,158,11,.55)}.ops-card.warn b{color:#fcd34d}
.ops-card.info{border-color:var(--line)}.ops-card.info b{color:var(--accent3)}
.ops-card.ok{border-color:rgba(16,185,129,.5)}.ops-card.ok b{color:#6ee7b7}
.feed-row{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:10px 14px;margin-bottom:8px;border-radius:14px;background:var(--card-a);border:1px solid var(--line);animation:slidein .5s ease}
@keyframes slidein{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:none}}
.sev{padding:2px 12px;border-radius:20px;font-size:.75rem;font-weight:700}
.sev-red{background:rgba(244,63,94,.18);color:#fda4af;border:1px solid rgba(244,63,94,.5)}
.sev-amber{background:rgba(245,158,11,.18);color:#fcd34d;border:1px solid rgba(245,158,11,.5)}
.dev-sign{text-align:center;color:var(--muted);font-size:.8rem;padding:14px 0 6px}
.dev-sign b{background:linear-gradient(90deg,var(--accent),var(--accent3));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:.5px}

/* ===== المساعد العائم ===== */
.st-key-fab_assistant{position:fixed !important;bottom:112px;left:18px;z-index:99990;width:auto !important;}  /* فوق شريط الروابط السفلي */
.st-key-fab_assistant button{border-radius:999px !important;padding:12px 22px !important;font-weight:700 !important;
  background:linear-gradient(135deg,var(--tab-a),var(--tab-b)) !important;border:1px solid var(--btn-border) !important;
  box-shadow:0 10px 30px var(--btn-glow) !important;}
.st-key-fab_assistant button *{color:var(--tab-text) !important;}
div[data-testid="stPopoverBody"]{min-width:min(390px,92vw);max-height:72vh;overflow:auto;}
.fab-hello{padding:10px 14px;border-radius:14px;background:var(--card-a);border:1px solid var(--line);margin-bottom:10px;line-height:1.8;color:var(--text)}
.st-key-dock{position:fixed !important;bottom:12px;left:50%;right:auto !important;transform:translateX(-50%);z-index:99975;width:min(1040px,calc(100vw - 28px)) !important;
  background:var(--glass);backdrop-filter:blur(18px) saturate(150%);-webkit-backdrop-filter:blur(18px) saturate(150%);
  border:1px solid var(--line);border-radius:24px;box-shadow:0 18px 44px -12px var(--shadow),inset 0 1px 0 rgba(255,255,255,.12);padding:5px 10px 0 !important;}
.st-key-dock iframe{display:block;border:0}
[data-testid="stMainBlockContainer"]{padding-bottom:150px !important}
.st-key-pg_hidden{position:absolute !important;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none;}
[data-testid="stStatusWidget"]{background:var(--glass);border:1px solid var(--line);border-radius:999px;padding:2px 12px;backdrop-filter:blur(10px);}
[data-testid="stStatusWidget"] *{color:var(--text) !important;}
[data-testid="stToolbar"] *{color:var(--text);}
@media (max-width:640px){.st-key-dock{bottom:6px;border-radius:18px;width:calc(100vw - 14px) !important;}.glass-card{padding:16px 16px;}}
@media (prefers-reduced-motion: reduce){*{transition:none !important;animation:none !important;}.stApp::before{display:none}}
</style>
"""

_CARD_CLASSES = {  # نوع البطاقة ← صنف CSS
    "glass": "glass-card", "ai": "ai-card-glow", "banner": "security-banner",
    "ok": "notice notice-ok", "warn": "notice notice-warn", "pink": "notice notice-pink",
}

_CONTRAST_CSS = """
<style>/*nofix*/
:root{--muted:#f1f5f9;--line:rgba(255,255,255,.7);}
[data-testid="stMain"] p,[data-testid="stMain"] li,[data-testid="stMain"] label{font-weight:600;}
.glass-card,[data-testid="stMetric"],div[data-testid="stExpander"]{border:2px solid #ffffff !important;}
a{text-decoration:underline !important;}
</style>
"""
_CONTRAST_LIGHT = """
<style>/*nofix*/
:root{--text:#000000;--muted:#1f2937;--line:rgba(0,0,0,.7);}
[data-testid="stMain"] p,[data-testid="stMain"] li,[data-testid="stMain"] label{font-weight:600;}
.glass-card,[data-testid="stMetric"],div[data-testid="stExpander"]{border:2px solid #0a4a2e !important;}
a{text-decoration:underline !important;}
</style>
"""
_ZOOM = {"عادي": 1.0, "كبير": 1.15, "أكبر": 1.3}


def inject_theme() -> None:  # يحقن CSS الأساسي + متغيّرات النمط الحالي (يُستدعى مرة في app.py)
    """يحقن CSS الأساسي + متغيّرات النمط الحالي (يُستدعى مرة في app.py)."""
    key = theme_key()
    st.session_state["_th_inj"] = key
    st.session_state["official_theme"] = _is_light(key)  # يقرؤه style_fig للرسوم
    st.markdown(_BASE_CSS + _vars_css(key), unsafe_allow_html=True)


# الشخصيتان توني وسعيدان انتقلتا إلى ملف characters.py (الرسم + الحوار + التفاعل) ونعيد تصديرهما هنا ليبقى الاستيراد القديم يعمل
from characters import _CMP_JS, _DIALOGUE, _REACT, _ROBOT_SVG, _SAUDI_SVG, companions  # noqa: E402,F401


_PLAIN_FONT_CSS = """<style>/*nofix*/:where(p,span,div,label,li,h1,h2,h3,h4,h5,button,input,textarea,td,th,a):not([data-testid="stIconMaterial"]){
font-family:Tahoma,Arial,sans-serif !important;}</style>"""
_SPACING_CSS = "<style>/*nofix*/.stApp p,.stApp li,.stApp label{line-height:2.1 !important;letter-spacing:.3px !important;}</style>"
_LINKS_CSS = "<style>/*nofix*/.stApp a{text-decoration:underline !important;text-underline-offset:3px;font-weight:700 !important;}</style>"
_NOMOTION_CSS = """<style>/*nofix*/*,*::before,*::after{animation:none !important;transition:none !important;}
.stApp::before,.stApp::after,div[data-testid='stAppViewContainer']::before{display:none !important;}</style>"""


def inject_prefs() -> None:  # بعد رسم شريط التسهيلات: إن غيّر المستخدم النمط في هذه الجولة نعيد حقن متغيّرات
    """بعد رسم شريط التسهيلات: إن غيّر المستخدم النمط في هذه الجولة نعيد حقن متغيّراته، ثم التباين وحجم الخط."""
    key = theme_key()
    st.session_state["official_theme"] = _is_light(key)
    if key != st.session_state.get("_th_inj"):
        st.session_state["_th_inj"] = key
        st.markdown(_vars_css(key), unsafe_allow_html=True)
    if st.session_state.get("high_contrast"):
        st.markdown(_CONTRAST_LIGHT if _is_light(key) else _CONTRAST_CSS, unsafe_allow_html=True)
    for flag, css in (("reduce_motion", _NOMOTION_CSS), ("plain_font", _PLAIN_FONT_CSS),
                      ("big_spacing", _SPACING_CSS), ("mark_links", _LINKS_CSS)):
        if st.session_state.get(flag):
            st.markdown(css, unsafe_allow_html=True)
    zoom = _ZOOM.get(st.session_state.get("font_scale", "عادي"), 1.0)
    if zoom != 1.0:  # zoom يكبّر الصفحة كلها بما فيها الأحجام الثابتة
        st.markdown(f"<style>/*nofix*/[data-testid='stMain']{{zoom:{zoom};}}</style>", unsafe_allow_html=True)


def card(body_html: str, kind: str = "glass") -> None:  # body_html يجب أن يكون HTML موثوقاً — مرّر أي نص خارجي عبر html.escape أولاً
    """body_html يجب أن يكون HTML موثوقاً — مرّر أي نص خارجي عبر html.escape أولاً."""
    st.markdown(f'<div class="{_CARD_CLASSES[kind]}">{body_html}</div>', unsafe_allow_html=True)


def style_fig(fig):  # يطبّق هوية المنصة على أي رسم Plotly: خلفية شفافة، خطوط وشبكة هادئة، وألوان موح
    """يطبّق هوية المنصة على أي رسم Plotly: خلفية شفافة، خطوط وشبكة هادئة، وألوان موحّدة."""
    day = _is_light(theme_key())
    grid = "rgba(120,90,10,.18)" if day else "rgba(212,175,55,.14)"
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#15291d" if day else "#e9f7ee", size=13, family="IBM Plex Sans Arabic, Segoe UI, Tahoma"),
        colorway=PALETTE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    fig.update_xaxes(gridcolor=grid, zerolinecolor=grid)
    fig.update_yaxes(gridcolor=grid, zerolinecolor=grid)
    return fig


def top_banner(ctx: AuthContext, api_ok: bool, record_count=None) -> None:  # الشريط العلوي القديم (صار دمجه داخل الواجهة الرئيسية render_welcome)؛ يُبقى لل
    """الشريط العلوي القديم (صار دمجه داخل الواجهة الرئيسية render_welcome)؛ يُبقى للتوافق."""
    if ctx.logged_in:
        chip = f'<span class="auth-chip auth-on">🟢 موثّق: {html.escape(ctx.username)}</span>'
    else:
        chip = '<span class="auth-chip auth-off">🔒 زائر — بيانات عامة فقط</span>'
    api = ('<span class="badge-status badge-green">● النظام والـ API: متصل</span>' if api_ok
           else '<span class="badge-status badge-red">● الـ API: غير مُفعّل</span>')
    count = (f'<span class="badge-status badge-orange">⚡ السجلات المتاحة لك: {record_count:,}</span>'
             if record_count is not None else "")
    st.markdown(f"""<div class="top-banner"><div><span class="brand">🏛️ {html.escape(APP_NAME)}</span>
<span class="brand-sub">| {html.escape(APP_TAGLINE)} · {APP_VERSION}</span></div><div>{api}{count}{chip}</div></div>""",
                unsafe_allow_html=True)


def footer() -> None:  # توقيع المطوّر أسفل الصفحة: اسم العلامة فقط (Bin3abdAi) دون بيانات شخصية
    """توقيع المطوّر أسفل الصفحة: اسم العلامة فقط (Bin3abdAi) دون بيانات شخصية."""
    st.markdown(f'<div class="dev-sign">صُنع بإتقان · تطوير <b>{html.escape(DEVELOPER_SIGNATURE)}</b> · '
                f'{html.escape(APP_NAME)} {APP_VERSION}</div>', unsafe_allow_html=True)


_RECOLOR = [  # يحوّل ألوان الأسطح القديمة (كحلي/سماوي/بنفسجي) إلى أخضر وذهبي في النمطين الوطني والنهاري
    ("#22d3ee", "#d4af37"), ("#67e8f9", "#f0d684"), ("#a5f3fc", "#f6e7a8"), ("#38bdf8", "#d4af37"), ("#c084fc", "#7ddba3"),
    ("rgba(34,211,238", "rgba(212,175,55"), ("rgba(103,232,249", "rgba(240,214,132"), ("rgba(14,116,144", "rgba(10,92,58"),
    ("rgba(109,40,217", "rgba(27,127,79"), ("rgba(15,23,42", "rgba(4,38,24"), ("rgba(30,27,75", "rgba(8,70,42"),
    ("rgba(8,47,73", "rgba(6,60,36"), ("rgba(10,16,32", "rgba(3,30,18"), ("rgba(30,41,59", "rgba(10,74,46"),
    ("rgba(5,12,24", "rgba(2,24,14"), ("#05070f", "#021a0f"), ("#0f172a", "#04281a"), ("#94a3b8", "#b9d9c7"),
    ("#cbd5e1", "#dff2e6"), ("#e2e8f0", "#eefaf2"), ("#f1f5f9", "#f6fff9"), ("rgba(148,163,184", "rgba(212,175,55"),
    ("#e0b84c", "#d4af37"), ("#f5d97a", "#f3d77a")]


_GREEN_PAIRS = _RECOLOR  # (للتوافق)

_LIGHT_BG = ["rgba(15,23,42", "rgba(4,38,24", "rgba(6,60,36", "rgba(2,24,14", "rgba(3,30,18", "rgba(10,74,46", "rgba(8,70,42",
             "rgba(10,16,32", "rgba(30,41,59", "rgba(5,12,24", "rgba(2,6,23", "rgba(10,92,58", "rgba(27,127,79"]  # أسطح داكنة تتحوّل إلى بيضاء في الأنماط الفاتحة


def _light_fix(text: str, key: str) -> str:  # يحوّل نصوصاً وأسطحاً مبنية على خلفية داكنة لتُقرأ على خلفية فاتحة
    v = _VARS[key]
    for old in _LIGHT_BG:
        text = text.replace(old, "rgba(@W@")
    text = text.replace("rgba(255,255,255,", "rgba(20,40,30,").replace("rgba(@W@", "rgba(255,255,255")
    pairs = [("#f8fafc", v["t1"]), ("#f1f5f9", v["t1"]), ("#e2e8f0", v["t1"]), ("#eefaf2", v["t1"]), ("#f6fff9", v["t1"]), ("#dff2e6", v["t1"]),
             ("#cbd5e1", v["t2"]), ("#b9d9c7", v["t2"]), ("#94a3b8", v["t3"]), ("#6ee7b7", v["good"]), ("#fcd34d", v["amber"]), ("#fde68a", v["amber"]),
             ("#fda4af", v["bad"]), ("#a5f3fc", v["accent"]), ("#67e8f9", v["accent"]), ("#22d3ee", v["accent"]), ("#38bdf8", v["accent"]),
             ("#f5d97a", "#8a6a12"), ("#f3d77a", "#9a7b12"), ("#f0d684", "#a8861a"), ("#e0b84c", "#8a6a12"), ("#d4af37", "#9a7b12"),
             ("(90deg,#fff,", f"(90deg,{v['t1']},"), ("color:#fff;", f"color:{v['t1']};")]
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def recolor(text: str) -> str:  # يلائم أي CSS/HTML قديم الألوان مع النمط الحالي (أخضر/ذهبي للفاتح والرملي، وقراءة صحيحة على الخلفيات الفاتحة)
    """يلائم أي CSS/HTML قديم الألوان مع النمط الحالي. الداكن والبحري يبقيان على لوحتهما الأصلية؛ علامة <!--keepdark--> تُبقي الصفحة داكنة في كل الأنماط."""
    key = theme_key()
    if key == "داكن":
        return text
    if key in ("فاتح", "رملي"):
        for old, new in _RECOLOR:
            text = text.replace(old, new)
    if "<!--keepdark-->" in text or not _is_light(key):
        return text
    return _light_fix(text, key)


def _install_markdown_filter() -> None:  # يمرّر كل st.markdown(unsafe_allow_html) عبر recolor حتى لا تظهر نصوص فاتحة على خلفية فاتحة
    orig = getattr(st.markdown, "_cmp_orig", st.markdown)

    def themed(body, *a, **k):
        if isinstance(body, str) and k.get("unsafe_allow_html") and "/*nofix*/" not in body:
            try:
                body = recolor(body)
            except Exception:
                pass
        return orig(body, *a, **k)

    themed._cmp_orig = orig
    st.markdown = themed


_install_markdown_filter()


# ======================================================
# أزرار التنقّل التقنية (iframe) — تفتح التبويب بالاسم
# ======================================================
_PAL = {"داكن": ("#e0b84c", "#22d3ee", "#eef4ff"), "فاتح": ("#0f7a55", "#b8921a", "#14231c"),
        "رملي": ("#8a6a2f", "#4f6b3a", "#2a2417"), "بحري": ("#1f5f9e", "#0f7a55", "#12202f")}


def theme_palette() -> tuple:  # ألوان النمط الحالي للمكونات المضمّنة
    return _PAL[theme_key()]


_NAV_JS = """<script>
function go(l){try{var d=window.parent.document;
 if(l.indexOf('btn:')===0){var k=l.slice(4);var bb=[].slice.call(d.querySelectorAll('.st-key-pg_hidden button')).find(function(x){return x.textContent.indexOf(k)>-1});if(bb)bb.click();return;}
 if(l==='__top__'){var m=d.querySelector('[data-testid="stMain"]');if(m)m.scrollTo({top:0,behavior:'smooth'});return;}
 var t=[].slice.call(d.querySelectorAll('button[role="tab"]')).find(function(b){return b.textContent.indexOf(l)>-1});
 if(t){t.click();setTimeout(function(){t.scrollIntoView({behavior:'smooth',block:'center',inline:'center'})},60);}}catch(e){}}
</script>"""

_NAV_CSS = """<style>*{box-sizing:border-box}body{margin:0;direction:rtl;font-family:'IBM Plex Sans Arabic',Tahoma,sans-serif}
.w{display:flex;flex-wrap:wrap;gap:10px}
.nb{cursor:pointer;color:__T__;border:1px solid __A__;background:linear-gradient(135deg,__A__2e,__B__30);padding:10px 18px;text-decoration:none;
 border-radius:14px;font:600 14px 'IBM Plex Sans Arabic',Tahoma,sans-serif;position:relative;overflow:hidden;transition:.25s;display:inline-block}
.nb:hover{transform:translateY(-2px);border-color:__B__;box-shadow:0 0 22px __A__77}
.nb:before{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,.3) 50%,transparent 70%);
 transform:translateX(-130%);transition:.6s}.nb:hover:before{transform:translateX(130%)}</style>"""


def nav_buttons(items: list, height: int = 70) -> None:  # أزرار تقنية تفتح تبويباً بالاسم، أو رابط mailto:/tel
    """أزرار تقنية تفتح تبويباً بالاسم، أو رابط mailto:/tel:. items = [(أيقونة, نص, اسم_التبويب_أو_رابط)]."""
    a, b, t = theme_palette()
    parts = []
    for ic, lab, tab in items:
        if str(tab).startswith(("mailto:", "tel:")):
            parts.append(f'<a class="nb" href="{html.escape(tab)}">{ic} {html.escape(lab)}</a>')
        else:
            parts.append(f'<button class="nb" onclick="go(\'{tab}\')">{ic} {html.escape(lab)}</button>')
    page = (_NAV_CSS.replace("__A__", a).replace("__B__", b).replace("__T__", t) + _NAV_JS + f'<div class="w">{"".join(parts)}</div>')
    components.html(page, height=height)


_DOCK_CSS = """<style>*{box-sizing:border-box}body{margin:0;direction:rtl;font-family:'IBM Plex Sans Arabic',Tahoma,sans-serif;background:transparent}
.d{display:flex;gap:4px;overflow-x:auto;padding:2px 2px 6px;scrollbar-width:thin;justify-content:center}
.b{flex:0 0 auto;min-width:76px;display:flex;flex-direction:column;align-items:center;gap:1px;padding:6px 8px;border-radius:14px;border:1px solid transparent;
 background:transparent;color:__T__;cursor:pointer;font:600 12px 'IBM Plex Sans Arabic',Tahoma,sans-serif;transition:.2s;white-space:nowrap}
.b i{font-style:normal;font-size:22px;line-height:1.15}
.b:hover{background:__A__22;border-color:__A__77;transform:translateY(-2px)}
.b.on{background:__A__;color:__ON__;border-color:__A__}
@media (max-width:640px){.d{justify-content:flex-start}.b{min-width:68px}}</style>"""

_DOCK_JS = """<script>
function go(l){try{var d=window.parent.document;var k=l.slice(4);var bb=[].slice.call(d.querySelectorAll('.st-key-pg_hidden button')).find(function(x){return x.textContent.indexOf(k)>-1});
 if(bb)bb.click();}catch(e){}}
function fit(){try{var P=window.parent,d=P.document,m=d.querySelector('[data-testid="stMain"]'),k=d.querySelector('.st-key-dock');
 if(m&&k){var r=m.getBoundingClientRect();k.style.left=(r.left+r.width/2)+'px';k.style.maxWidth=Math.max(280,r.width-24)+'px';}}catch(e){}}
fit();setInterval(fit,700);
</script>"""


def dock_buttons(items: list, active: str = "", height: int = 74) -> None:  # شريط الروابط الثابت أسفل الشاشة: items = [(معرّف_الزر_المخفي, أيقونة, نص)]
    """شريط الروابط الثابت أسفل الشاشة. كل زر يضغط زراً مخفياً اسمه PG_xxx (انظر views_public.render_quick_links). active = معرّف الصفحة الحالية."""
    a, b, t = theme_palette()
    on = "#ffffff" if _is_light(theme_key()) else "#0a1226"  # لون النص فوق الزر المحدّد
    btns = "".join(f'<button class="b{" on" if k == active else ""}" onclick="go(\'btn:{k}\')"><i>{ic}</i>{html.escape(lab)}</button>' for k, ic, lab in items)
    page = (_DOCK_CSS.replace("__A__", a).replace("__T__", t).replace("__ON__", on) + _DOCK_JS + f'<div class="d">{btns}</div>')
    components.html(page, height=height)


def official_footer(ctx: AuthContext) -> None:  # تذييل رسمي بلا شريط أخضر: صف أزرار تقنية متناسقة + سطر آخر تحديث (هجري وميلادي
    """تذييل رسمي بلا شريط أخضر: صف أزرار تقنية متناسقة + سطر آخر تحديث (هجري وميلادي) وتنويه التجريبية."""
    import datetime
    from pathlib import Path

    from config import get_setting
    from data_layer import hijri_text
    try:
        d = datetime.datetime.fromtimestamp(Path(__file__).stat().st_mtime)
    except Exception:
        d = datetime.datetime.now()
    mail = (get_setting("CONTACT_EMAIL") or "").strip()
    phone = (get_setting("CONTACT_PHONE") or "").strip()
    st.markdown("<hr>", unsafe_allow_html=True)
    items = []  # الروابط الرئيسية انتقلت إلى الشريط السفلي الثابت (dock_buttons)؛ هنا بيانات التواصل فقط إن وُجدت
    if mail:
        items.append(("✉️", mail, f"mailto:{mail}"))
    if phone:
        items.append(("📞", phone, f"tel:{phone}"))
    if items:
        nav_buttons(items, height=64)
    st.markdown(f'<div class="dev-sign" style="line-height:1.9">تاريخ آخر تحديث للمنصة: {d.strftime("%Y/%m/%d")} م — '
                f'{html.escape(hijri_text(d.date()))}<br>🌴 نحو مدينة أذكى وخدمات أقرب للمستفيد — رؤية المملكة 2030<br>'
                "منصة تجريبية (Pilot) مقدَّمة لأمانة محافظة جدة لأغراض التقييم، ولا تُعدّ بوابة الأمانة الرسمية.</div>",
                unsafe_allow_html=True)
