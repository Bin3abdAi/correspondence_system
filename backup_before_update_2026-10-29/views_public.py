"""صفحات الجمهور والزوار: تتبّع المعاملة، مشاريع الأمانة، بيانات مفتوحة، الرأي، الخصوصية، التدريب، الواجهة الرئيسية والمساعد العائم."""
from views_common import *  # noqa: F401,F403  (الأسماء العامة + الاستيرادات)
from views_common import (  # noqa: F401  (أسماء خاصة لا يجلبها *)
    _frame,
    _speak_once)
from ui import _VARS, theme_key  # ألوان النمط الحالي للواجهة الرئيسية


# ======================================================
# شاشة الترحيب الحية (تظهر أعلى المنصة عند الفتح)
# ======================================================
_WELCOME_HTML = r"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><!--keepdark-->
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
*{box-sizing:border-box;margin:0}
body{background:transparent;font-family:'IBM Plex Sans Arabic','Segoe UI',Tahoma,sans-serif;color:#f1f5f9}
.wrap{position:relative;overflow:hidden;border-radius:24px;padding:26px 30px;min-height:430px;
 background:__BG__;
 border:1px solid rgba(224,184,76,.45);box-shadow:0 30px 70px -20px rgba(0,0,0,.75),0 0 80px -30px rgba(224,184,76,.55),inset 0 1px 0 rgba(255,255,255,.14)}
.wrap::before{content:"";position:absolute;inset:-35%;z-index:1;pointer-events:none;
 background:radial-gradient(34% 38% at 20% 30%,rgba(34,211,238,.20),transparent 70%),radial-gradient(30% 34% at 82% 72%,rgba(224,184,76,.22),transparent 70%);
 animation:drift 18s ease-in-out infinite alternate}
@keyframes drift{from{transform:translate3d(-3%,-2%,0) scale(1)}to{transform:translate3d(4%,3%,0) scale(1.1)}}
.wrap::after{content:"";position:absolute;left:0;right:0;bottom:0;height:3px;z-index:3;background:linear-gradient(90deg,transparent,#e0b84c,#22d3ee,#e0b84c,transparent);opacity:.85}
canvas{position:absolute;inset:0;width:100%;height:100%;opacity:.55}
.content{position:relative;z-index:2}
.top{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.pill{font-size:.8rem;padding:6px 15px;border-radius:30px;border:1px solid rgba(148,163,184,.32);background:rgba(15,23,42,.55);color:#e2e8f0;backdrop-filter:blur(8px);font-weight:500}
.live{border-color:rgba(16,185,129,.6);color:#6ee7b7}
.gold{border-color:#e0b84c;color:#f5d97a;background:rgba(224,184,76,.14)}.red{border-color:#f43f5e;color:#fda4af}
.live i{display:inline-block;width:9px;height:9px;border-radius:50%;background:#10b981;margin-left:7px;animation:pulse 1.6s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(16,185,129,.7)}70%{box-shadow:0 0 0 10px rgba(16,185,129,0)}100%{box-shadow:0 0 0 0 rgba(16,185,129,0)}}
.clock{margin-right:auto;text-align:left;line-height:1.35}
.clock b{display:block;font-size:1.5rem;letter-spacing:1px;color:#e0b84c;font-variant-numeric:tabular-nums}
.clock small{display:block;color:#94a3b8;font-size:.72rem}
h1{font-size:clamp(2.1rem,5vw,3.6rem);font-weight:700;direction:ltr;text-align:right;letter-spacing:-1.5px;line-height:1.1;
 background:linear-gradient(90deg,#fff,#a5f3fc 28%,#e0b84c 55%,#fff 80%,#a5f3fc);background-size:220% auto;animation:shine 8s linear infinite;
 -webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 6px 22px rgba(0,0,0,.35))}
@keyframes shine{to{background-position:220% center}}
.tag{color:#e2e8f0;font-size:1.15rem;margin:6px 0 14px;font-weight:500}
.greet{color:#e0b84c;font-weight:600;margin:6px 0 4px}
.type{min-height:34px;font-size:1.1rem;color:#a5f3fc;font-weight:500}
.type u{display:inline-block;width:2px;height:1.1em;background:#22d3ee;margin-right:3px;vertical-align:middle;animation:blink 1s steps(1) infinite;text-decoration:none}
@keyframes blink{50%{opacity:0}}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:20px}
.k{position:relative;padding:16px 18px;border-radius:18px;background:linear-gradient(145deg,rgba(255,255,255,.10),rgba(15,23,42,.62));
 border:1px solid rgba(148,163,184,.24);backdrop-filter:blur(12px);transition:transform .3s,border-color .3s,box-shadow .3s;overflow:hidden}
.k::before{content:"";position:absolute;top:0;right:18px;left:18px;height:2px;background:linear-gradient(90deg,transparent,#e0b84c,transparent);opacity:.8}
.k:hover{transform:translateY(-5px);border-color:rgba(224,184,76,.7);box-shadow:0 18px 36px -16px rgba(0,0,0,.7)}
.k b{display:block;font-size:1.7rem;font-variant-numeric:tabular-nums;background:linear-gradient(90deg,#fff,#67e8f9);-webkit-background-clip:text;background-clip:text;color:transparent}
.k span{font-size:.8rem;color:#94a3b8}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media (max-width:560px){.wrap{padding:20px 16px}.clock{margin-right:0}}
</style></head><body>
<div class="wrap"><canvas id="net"></canvas>
<div class="content">
 <div class="top">
  __CHIPS__
  <span class="pill live"><i></i>النظام يعمل مباشرةً</span>
  <span class="pill">🇸🇦 يدعم مستهدفات رؤية 2030</span>
  <span class="pill">🧪 نسخة تجريبية __VERSION__</span>
  <div class="clock"><b id="time">--:--:--</b><small id="hijri"></small><small id="greg"></small></div>
 </div>
 <h1>__NAME__</h1>
 <div class="tag">__TAGLINE__</div>
 <div class="greet" id="greet"></div>
 <div class="type"><span id="tw"></span><u></u></div>
 __KPIS__
</div></div>
<script>
// ---- الوقت والتاريخ الحي (هجري + ميلادي) ----
const fmt=(o,l)=>new Intl.DateTimeFormat(l,o);
function tick(){const d=new Date();
 document.getElementById('time').textContent=d.toLocaleTimeString('en-GB',{hour12:false});
 document.getElementById('hijri').textContent=fmt({weekday:'long',day:'numeric',month:'long',year:'numeric'},'ar-SA-u-ca-islamic-umalqura').format(d);
 document.getElementById('greg').textContent=fmt({day:'numeric',month:'long',year:'numeric'},'ar-SA-u-ca-gregory').format(d);}
tick();setInterval(tick,1000);
// ---- التحية حسب الوقت ----
const h=new Date().getHours();
document.getElementById('greet').textContent=(h<12?'صباح الخير':h<18?'مساء الخير':'مساء النور')+'، __USER__';
// ---- آلة كتابة تتبدل بين الرسائل ----
const lines=['تحوّل بلاغات المدينة إلى قرارات خلال ثوانٍ','تحدّث بلهجتك وسيفهمك المساعد ويردّ عليك صوتاً','تحليل وتوقّع فوري لأداء الأمانة بالذكاء الاصطناعي','بياناتك محمية بصلاحيات وسرية متعددة المستويات'];
let li=0,ci=0,del=false;const tw=document.getElementById('tw');
function type(){const s=lines[li];tw.textContent=s.slice(0,ci);
 if(!del&&ci<s.length){ci++;setTimeout(type,45)}
 else if(!del){del=true;setTimeout(type,1700)}
 else if(ci>0){ci--;setTimeout(type,18)}
 else{del=false;li=(li+1)%lines.length;setTimeout(type,300)}}
type();
// ---- عدّاد الأرقام التصاعدي ----
document.querySelectorAll('[data-count]').forEach(el=>{
 const to=parseFloat(el.dataset.count),dec=+(el.dataset.dec||0),suf=el.dataset.suf||'';const t0=performance.now(),dur=1600;
 (function f(t){const p=Math.min((t-t0)/dur,1),e=1-Math.pow(1-p,3);
  el.textContent=(to*e).toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec})+suf;
  if(p<1)requestAnimationFrame(f)})(t0)});
// ---- شبكة جسيمات متحركة في الخلفية ----
const c=document.getElementById('net'),x=c.getContext('2d');let W,H,P=[];
function size(){W=c.width=c.offsetWidth;H=c.height=c.offsetHeight;P=Array.from({length:Math.min(60,W/18)},()=>({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.4,vy:(Math.random()-.5)*.4}))}
size();addEventListener('resize',size);
(function draw(){x.clearRect(0,0,W,H);
 P.forEach((a,i)=>{a.x+=a.vx;a.y+=a.vy;if(a.x<0||a.x>W)a.vx*=-1;if(a.y<0||a.y>H)a.vy*=-1;
  x.fillStyle='rgba(103,232,249,.8)';x.beginPath();x.arc(a.x,a.y,1.6,0,6.3);x.fill();
  for(let j=i+1;j<P.length;j++){const b=P[j],d=Math.hypot(a.x-b.x,a.y-b.y);
   if(d<110){x.strokeStyle='rgba(224,184,76,'+(1-d/110)*.35+')';x.beginPath();x.moveTo(a.x,a.y);x.lineTo(b.x,b.y);x.stroke()}}});
 requestAnimationFrame(draw)})();
</script></body></html>"""


_KPIS_ADMIN = """<div class="kpis">
  <div class="k"><b data-count="__TOTAL__">0</b><span>معاملة متاحة لك الآن</span></div>
  <div class="k"><b data-count="__RATE__" data-dec="1" data-suf="%">0</b><span>معدل الإنجاز العام</span></div>
  <div class="k"><b data-count="__URGENT__">0</b><span>معاملة عاجلة مفتوحة</span></div>
  <div class="k"><b data-count="__DISTRICTS__">0</b><span>حيّاً تغطيها المنصة</span></div>
 </div>"""


_KPIS_PUBLIC = """<div class="kpis">
  <div class="k"><b>🎙️</b><span>مساعد صوتي بلهجتك</span></div>
  <div class="k"><b>🧠</b><span>تحليل ذكي للبلاغات</span></div>
  <div class="k"><b>🛡️</b><span>سرية متعددة المستويات</span></div>
  <div class="k"><b>🔒</b><span>الأرقام التفصيلية للمدير بعد تسجيل الدخول</span></div>
 </div>"""


_ENV_LAYERS = [  # طبقات بيئة المنصة من الأعلى (المستخدم) إلى الأسفل (البيانات)
    ("🖥️", "الواجهة", ["Streamlit", "عربي RTL", "ميكروفون وكاميرا", "رفع ملفات"]),
    ("🛡️", "الأمان والصلاحيات", ["تسجيل دخول مشفّر (PBKDF2)", "عام / سري / سري للغاية", "فلترة من الخادم", "سجل تدقيق"]),
    ("📊", "محرك التحليل", ["pandas + NumPy", "مؤشرات الإنجاز والتأخر", "توقّع خطي", "توزيع الفرق"]),
    ("🧠", "الذكاء الاصطناعي", ["GPT-4o للنص والتحليل", "Vision للصور", "Whisper: صوت ← نص", "TTS: نص ← صوت"]),
    ("🗄️", "البيانات", ["SQLite (WAL) + فهارس", "كاش ذكي", "جاهزة للترحيل إلى PostgreSQL", "150 ألف+ معاملة"]),
    ("📤", "المخرجات", ["طباعة", "PDF رسمي", "CSV آمن", "بريد رسمي"]),
]


_WELCOME_CSS = """<style>
.about-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.about-item{padding:14px 16px;border-radius:16px;background:rgba(15,23,42,.55);border:1px solid rgba(148,163,184,.18)}
.about-item b{color:#e0b84c}
.layer{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:12px 16px;border-radius:16px;
 background:rgba(15,23,42,.55);border:1px solid rgba(148,163,184,.18)}
.layer .t{min-width:170px;font-weight:700;color:#a5f3fc}
.chip{display:inline-block;padding:3px 12px;margin:2px;border-radius:20px;font-size:.8rem;background:rgba(34,211,238,.1);
 border:1px solid rgba(34,211,238,.3);color:#e2e8f0}
.arrow{text-align:center;color:#e0b84c;line-height:1.1;font-size:1.1rem}
.new-tag{display:inline-block;padding:1px 10px;border-radius:20px;font-size:.7rem;font-weight:700;color:#05070f;
 background:linear-gradient(135deg,#e0b84c,#f5d97a);margin-left:6px}
.pillar{padding:16px;border-radius:16px;background:linear-gradient(145deg,rgba(6,78,59,.35),rgba(15,23,42,.7));
 border:1px solid rgba(16,185,129,.35)}
.pillar h5{color:#6ee7b7;margin:0 0 6px}
</style>"""


def _welcome_details() -> None:  # الأقسام الأربعة: ما هي المنصة، بيئتها، ما الجديد، وربطها برؤية 2030
    """الأقسام الأربعة: ما هي المنصة، بيئتها، ما الجديد، وربطها برؤية 2030."""
    st.markdown(recolor(_WELCOME_CSS), unsafe_allow_html=True)
    t_about, t_sec, t_env, t_new, t_vision = st.tabs(["🎯 ما هي المنصة؟", "🛡️ السرية والأمن", "🧩 بيئة المنصة", "🆕 ما الذي تغيّر؟", "🇸🇦 رؤية 2030"])
    with t_about:
        st.markdown("**🎯 الأهداف:** ⏱️ تسريع الإنجاز · 🔎 شفافية ومساءلة · 🧠 قرارات مبنية على بيانات · 🗣️ خدمة بلغة المستفيد.")
        st.markdown(
            f"**{APP_NAME}** منصة تجريبية تجمع بلاغات ومعاملات أمانة محافظة جدة في مكان واحد، وتحوّلها إلى مؤشرات وقرارات "
            "ومهام ميدانية، مع مساعد ذكي يفهم لهجتك السعودية ويردّ عليك نصاً وصوتاً ضمن صلاحيتك فقط.")
        items = [
            ("📊 لوحة التحليلات", "معدل الإنجاز، المتأخر، الاتجاه الأسبوعي، التوقع، وأداء الأقسام + جدول تفاعلي بأزرار."),
            ("📝 إدخال المعاملات", "إدخال يدوي أو بصورة (تحليل بصري) أو برفع ملفات CSV / Excel / PDF مع كشف غير البلدي."),
            ("🚨 العمليات والإنذارات", "خريطة جدة ومركز إنذارات؛ الموظف يرفع التنبيه والمدير يعتمد إرساله."),
            ("💬 المساعد الذكي", "أسئلة وتحليل وصياغة خطابات رسمية، نصاً أو بصوتك، مع احترام درجة السرية."),
            ("👷 الفرق الميدانية", "توزيع المعاملات على الفرق، اقتراح الفريق الأنسب، وتقارير ميدانية بالصور."),
            ("⚖️ الحوكمة والامتثال", "الصلاحيات، سجل التدقيق، وضوابط الأمن."),
            ("🚀 الجاهزية", "فحص شامل لمدى جاهزية المنصة والبيانات."),
            ("📤 الإصدار الرسمي", "في كل صفحة: طباعة، PDF، CSV، وإرسال بريد رسمي."),
        ]
        st.markdown('<div class="about-grid">' + "".join(
            f'<div class="about-item"><b>{t}</b><br><span style="color:#cbd5e1">{d}</span></div>' for t, d in items)
            + "</div>", unsafe_allow_html=True)
    with t_sec:
        st.markdown("**ماذا يرى كل مستخدم؟** (يُطبَّق في الواجهة وفي المساعد الذكي معاً)")
        st.markdown('<div class="about-grid">'
                    '<div class="pillar"><h5>👁️ الزائر — الانطباع الأول</h5>معاملات <b>عامة</b> فقط، '
                    'وصفحة ترحيب وشرح للمنصة بلا أرقام تفصيلية.</div>'
                    '<div class="pillar"><h5>👷 الموظف — الاطلاع</h5>مستويات <b>عام + سري</b>، يرفع البلاغات والتنبيهات '
                    'ويكتب التقرير الميداني.</div>'
                    '<div class="pillar"><h5>🏛️ المدير — القرار</h5>كل المستويات حتى <b>سري للغاية</b>: لوحة التحليلات، '
                    'الخرائط، الفرق، الحوكمة، واعتماد التنبيهات.</div></div>', unsafe_allow_html=True)
        st.markdown("**ضوابط الأمن السيبراني المطبّقة:**")
        for icon, t in [("🔐", "تسجيل دخول بكلمات مرور مشفّرة وصلاحيات حسب الدور"),
                        ("🚫", "إخفاء المحتوى الإداري عن الزائر والموظف (يظهر للمدير فقط)"),
                        ("🧾", "سجل تدقيق لكل إجراء حساس ولكل محاولة دخول مرفوضة"),
                        ("🤖", "المساعد الذكي لا يرى إلا بيانات مستوى صلاحية المستخدم"),
                        ("✅", "اعتماد المدير قبل إرسال أي إنذار رسمي")]:
            st.markdown(f"- {icon} {t}")
    with t_env:
        st.caption("هكذا تعمل المنصة من لحظة ضغطك على الشاشة وحتى وصول النتيجة إليك:")
        parts = []
        for i, (icon, title, chips) in enumerate(_ENV_LAYERS):
            chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
            parts.append(f'<div class="layer"><div class="t">{icon} {title}</div><div>{chip_html}</div></div>')
            if i < len(_ENV_LAYERS) - 1:
                parts.append('<div class="arrow">▼</div>')
        st.markdown("".join(parts), unsafe_allow_html=True)
    with t_new:
        changes = [
            (True, "اسم وهوية جديدة", f"{APP_NAME} + تصميم زجاجي فاخر وتبويبات حديثة."),
            (True, "جدول تفاعلي بأزرار", "اختر أي معاملة ثم: تفاصيل، تحليل ذكي، تكليف فريق، تغيير الحالة، تقرير PDF/CSV."),
            (True, "رسوم تقنية أوضح", "حلقة الإنجاز مقابل المستهدف، واتجاه أسبوعي بنطاق توقّع، مع شرح لكل رسم."),
            (False, "سعة بيانات أكبر", "من 5 آلاف إلى 150 ألف+ معاملة بفهارس وكاش ذكي، وجاهزة للوصول إلى مليون."),
            (False, "مساعد صوتي في كل الصفحات", "يفهم اللهجة السعودية ويردّ صوتاً، ويُخفي تلقائياً ما فوق صلاحيتك."),
            (False, "شريط إصدار رسمي", "طباعة وPDF وCSV وبريد رسمي في كل صفحة."),
            (False, "مركز إنذارات باعتماد المدير", "الموظف يرفع والمدير يعتمد ويرسل مع سجل تدقيق."),
            (False, "المساعد التقني", "تحليل وحلول وتوقّع أسفل كل صفحة."),
        ]
        st.markdown("".join(
            f'<div class="about-item" style="margin-bottom:8px">{"<span class=new-tag>جديد</span>" if new else ""}'
            f'<b>{t}</b> — <span style="color:#cbd5e1">{d}</span></div>' for new, t, d in changes), unsafe_allow_html=True)
    with t_vision:
        st.markdown('<div class="about-grid">'
                    '<div class="pillar"><h5>🌿 مجتمع حيوي</h5>رفع جودة الحياة والمشهد الحضري: معالجة أسرع لبلاغات '
                    'النظافة والطرق والإنارة والتشوه البصري.</div>'
                    '<div class="pillar"><h5>💼 اقتصاد مزدهر</h5>كفاءة تشغيلية وخدمات تراخيص أسرع '
                    'وقرارات مبنية على بيانات بدل التقدير.</div>'
                    '<div class="pillar"><h5>🏛️ وطن طموح</h5>حكومة فعّالة وشفافة: مؤشرات أداء ومساءلة وسجل تدقيق '
                    'وتحوّل رقمي بالذكاء الاصطناعي.</div></div>', unsafe_allow_html=True)
        st.caption("ربط استرشادي بمحاور الرؤية لأغراض العرض التجريبي، وليس بياناً رسمياً من الأمانة.")


@st.cache_resource(show_spinner=False)
def _hero_image_uri() -> str:  # صورة المبنى الرئيسي (jeddah_building.*) كخلفية للواجهة
    """صورة المبنى الرئيسي (jeddah_building.*) كخلفية للواجهة. تُصغَّر وتُحفظ مرة واحدة؛ تُرجع "" إن لم توجد."""
    import base64
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        for pat in ("jeddah_building.*", "*building*.*", "main_building.*", "hero.*"):
            for f in sorted(base.glob(pat)):
                if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                    try:
                        from PIL import Image
                        im = Image.open(f).convert("RGB")
                        im.thumbnail((1700, 900))
                        buf = io.BytesIO()
                        im.save(buf, "JPEG", quality=80)
                        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
                    except Exception:
                        continue
    return ""


def render_welcome(ctx: AuthContext, df_visible: pd.DataFrame, api_ok: bool = True, record_count=None) -> None:  # الواجهة الرئيسية: صورة المبنى + اسم المنصة + شريط الحالة والسجلات + أرقام حية،
    """الواجهة الرئيسية: صورة المبنى + اسم المنصة + شريط الحالة والسجلات + أرقام حية، وتحتها تفاصيل المنصة."""
    total = len(df_visible)
    done = int((df_visible["الحالة"] == STATUS_DONE).sum()) if total else 0
    urgent = int(((df_visible["الحالة"] != STATUS_DONE) & df_visible["درجة الأهمية"].isin(["عاجل", "حرج للغاية"])).sum()) if total else 0
    user = ctx.username if ctx.logged_in else "ضيفنا الكريم"
    chips = ('<span class="pill live"><i></i>الذكاء الاصطناعي: متصل</span>' if api_ok
             else '<span class="pill red">● الذكاء الاصطناعي: غير مُفعّل</span>')
    if record_count is not None:  # الرقم للمدير فقط
        chips += f'<span class="pill gold">⚡ السجلات المتاحة لك: {record_count:,}</span>'
    chips += (f'<span class="pill">🟢 موثّق: {html.escape(ctx.username)}</span>' if ctx.logged_in
              else '<span class="pill red">🔒 زائر — بيانات عامة فقط</span>')
    img = _hero_image_uri()
    hv = _VARS[theme_key()]  # ألوان الغطاء الداكن فوق الصورة حسب النمط
    grad = f"linear-gradient(135deg,{hv['hero_a']},{hv['hero_b']} 55%,{hv['hero_c']})"
    bg = f"{grad},url({img}) center/cover,{hv['hero_base']}" if img else f"{grad},{hv['hero_base']}"
    page = (_WELCOME_HTML.replace("__KPIS__", _KPIS_ADMIN if is_admin(ctx) else _KPIS_PUBLIC).replace("__BG__", bg)
            .replace("__CHIPS__", chips)
            .replace("__NAME__", html.escape(APP_NAME)).replace("__TAGLINE__", html.escape(APP_TAGLINE))
            .replace("__VERSION__", html.escape(APP_VERSION)).replace("__USER__", html.escape(str(user)))
            .replace("__TOTAL__", str(total)).replace("__RATE__", f"{done / total * 100:.1f}" if total else "0")
            .replace("__URGENT__", str(urgent)).replace("__DISTRICTS__", str(len(DISTRICTS))))
    _frame(page, 450)
    first_visit = not st.session_state.get("welcome_seen")
    with st.expander("🌟 تعرّف على المنصة: وظيفتها • بيئتها • ما الجديد • رؤية 2030", expanded=first_visit):
        _welcome_details()
    st.session_state["welcome_seen"] = True  # بعد أول عرض يُطوى القسم تلقائياً


# ======================================================
# التبويب الأول (عام): تتبّع المعاملة — بحث بالرقم الكامل كتابةً أو صوتاً، بلا تسجيل دخول
# ======================================================
_TRACK_CSS = """<style>
.trk-hero{position:relative;overflow:hidden;border-radius:26px;padding:30px 28px;margin:4px 0 18px;
 background:linear-gradient(120deg,var(--ban-a),var(--ai-a),var(--ban-b));background-size:200% 200%;
 animation:trkflow 14s ease infinite;border:1px solid var(--line);box-shadow:0 20px 60px -20px var(--shadow)}
@keyframes trkflow{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
.trk-hero h2{margin:0 0 6px;font-size:1.7rem;color:#f8fafc}.trk-hero p{margin:0;color:#cbd5e1;line-height:1.9}
.trk-steps{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.trk-steps span{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);border-radius:999px;padding:5px 14px;font-size:.82rem;color:#e2e8f0}
.trk-badge{display:inline-block;padding:4px 16px;border-radius:999px;font-weight:800;font-size:.95rem}
.trk-grn{background:rgba(16,185,129,.16);color:#6ee7b7;border:1px solid rgba(16,185,129,.55)}
.trk-amb{background:rgba(245,158,11,.16);color:#fcd34d;border:1px solid rgba(245,158,11,.55)}
.trk-red{background:rgba(244,63,94,.16);color:#fda4af;border:1px solid rgba(244,63,94,.55)}
.trk-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:12px 0}
.trk-cell{border-radius:14px;padding:10px 14px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1)}
.trk-cell span{display:block;font-size:.76rem;color:#94a3b8}.trk-cell b{font-size:1rem;color:#f1f5f9}
.trk-line{list-style:none;margin:14px 0;padding:0;display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.trk-line li{position:relative;text-align:center;padding:12px 6px;border-radius:16px;background:rgba(255,255,255,.04);
 border:1px solid rgba(255,255,255,.1);font-size:.84rem;color:#94a3b8}
.trk-line li b{display:block;font-size:1.4rem}
.trk-line li.done{color:#6ee7b7;border-color:rgba(16,185,129,.5);background:rgba(16,185,129,.08)}
.trk-line li.cur{color:#fde68a;border-color:rgba(245,158,11,.7);background:rgba(245,158,11,.10);animation:trkpulse 2s infinite}
@keyframes trkpulse{0%{box-shadow:0 0 0 0 rgba(245,158,11,.5)}70%{box-shadow:0 0 0 12px rgba(245,158,11,0)}100%{box-shadow:0 0 0 0 rgba(245,158,11,0)}}
@media(max-width:700px){.trk-line{grid-template-columns:repeat(2,1fr)}}
@media (prefers-reduced-motion: reduce){.trk-hero,.trk-line li.cur{animation:none}}
</style>"""


_NOT_FOUND = "لم يتم العثور على معاملة بهذا الرقم. تأكد من الرقم كاملاً (مثال: TRX-JED-0755766) وحاول مرة أخرى."


_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")  # الأرقام العربية ← إنجليزية


def _normalize_trx(raw: str) -> str:  # يوحّد الرقم المكتوب: يقبل الرقم الكامل TRX-JED-0755766 أو الأرقام السبعة وحدها
    """يوحّد الرقم المكتوب: يقبل الرقم الكامل TRX-JED-0755766 أو الأرقام السبعة وحدها."""
    q = (raw or "").translate(_AR_DIGITS).strip().upper().replace(" ", "")
    return f"TRX-JED-{q}" if re.fullmatch(r"\d{7}", q) else q


def _trx_from_speech(text: str) -> str:  # يستخرج رقم المعاملة من كلام منطوق: يجمع الأرقام السبعة (Whisper قد يفصلها بمسا
    """يستخرج رقم المعاملة من كلام منطوق: يجمع الأرقام السبعة (Whisper قد يفصلها بمسافات أو شرطات)."""
    digits = re.sub(r"\D", "", (text or "").translate(_AR_DIGITS))
    return f"TRX-JED-{digits}" if len(digits) == 7 else ""


def _typical_days(df: pd.DataFrame, dept: str):  # المدة المعتادة للقسم (وسيط الفرق بين الاستلام والموعد المتوقع في معاملاته المش
    """المدة المعتادة للقسم (وسيط الفرق بين الاستلام والموعد المتوقع في معاملاته المشابهة)."""
    sub = df.loc[df["القسم المكلف"] == dept, ["تاريخ الاستلام", "تاريخ الإنجاز المتوقع"]].dropna()
    if sub.empty:
        return None
    return int((sub["تاريخ الإنجاز المتوقع"] - sub["تاريخ الاستلام"]).dt.days.median())


def _fmt_date(v) -> str:  # تنسيق تاريخ للعرض
    return f"{v:%Y-%m-%d}" if pd.notna(v) else "—"


def _tracking_result(row: pd.Series, df: pd.DataFrame, ctx: AuthContext) -> None:  # بطاقة النتيجة: الجهة، الحالة، التواريخ، الخط الزمني، سبب التأخير مع اعتذار مهذ
    """بطاقة النتيجة: الجهة، الحالة، التواريخ، الخط الزمني، سبب التأخير مع اعتذار مهذب، وطرق الاتصال."""
    trx, dept = str(row["رقم المعاملة"]), str(row["القسم المكلف"])
    status = str(row["الحالة"])
    label, cls, icon = {STATUS_DONE: ("منجزة", "grn", "✅"),
                        STATUS_FIELD: ("جاري العمل", "amb", "🛠️")}.get(status, ("معلّقة بانتظار المباشرة", "red", "⏳"))
    today = pd.Timestamp.today().normalize()
    received, due = row.get("تاريخ الاستلام"), row.get("تاريخ الإنجاز المتوقع")
    done = status == STATUS_DONE
    late = (not done) and pd.notna(due) and due < today
    days_left = int((due - today).days) if pd.notna(due) else None
    if done:
        remain = "أُنجزت"
    elif late:
        remain = f"متأخرة {abs(days_left)} يوماً"
    else:
        remain = f"متبقٍ {days_left} يوماً" if days_left is not None else "—"
    typical = _typical_days(df, dept)
    phone, mail = get_setting("CONTACT_PHONE"), get_setting("CONTACT_EMAIL")
    contact = " · ".join(x for x in [f"📞 {phone}" if phone else "", f"✉️ {mail}" if mail else ""] if x) \
        or "عبر مركز خدمة المستفيدين في الأمانة"
    esc = html.escape

    st.markdown(
        f'<div class="ai-card-glow"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px">'
        f'<b style="font-size:1.15rem">{esc(trx)}</b><span class="trk-badge trk-{cls}">{icon} {label}</span></div>'
        f'<div style="margin-top:8px;color:#e2e8f0">{esc(str(row["موضوع المعاملة"]))}</div>'
        f'<div class="trk-grid">'
        f'<div class="trk-cell"><span>الجهة المستلمة</span><b>{esc(str(row.get("اسم الجهة", "—")))}</b></div>'
        f'<div class="trk-cell"><span>القسم المختص</span><b>{esc(dept)}</b></div>'
        f'<div class="trk-cell"><span>الحي</span><b>{esc(str(row["الحي"]))}</b></div>'
        f'<div class="trk-cell"><span>تاريخ الاستلام</span><b>{_fmt_date(received)}</b></div>'
        f'<div class="trk-cell"><span>الإنجاز المتوقع</span><b>{_fmt_date(due)}</b></div>'
        f'<div class="trk-cell"><span>المدة</span><b>{remain}</b></div>'
        + (f'<div class="trk-cell"><span>المدة المعتادة في القسم (معاملات مشابهة)</span><b>≈ {typical} يوماً</b></div>'
           if typical else "")
        + '</div>', unsafe_allow_html=True)

    third = "done" if done else "cur"  # المرحلة الثالثة: جارية الآن (عمل أو انتظار مباشرة) أو مكتملة
    steps = [("📥", "استلام المعاملة", _fmt_date(received), "done"),
             ("🏢", f"توجيهها إلى {dept}", "", "done"),
             ("🛠️", "المباشرة والعمل" if status != STATUS_FIELD and not done else "قيد التنفيذ",
              "بانتظار المباشرة" if status not in (STATUS_FIELD, STATUS_DONE) else "", third),
             ("🏁", "الإنجاز", _fmt_date(due) if not done else "تمّ", "done" if done else "")]
    st.markdown('<ul class="trk-line">' + "".join(
        f'<li class="{state}"><b>{ic}</b>{esc(t)}<br><small>{esc(sub)}</small></li>' for ic, t, sub, state in steps)
        + '</ul><div style="color:#64748b;font-size:.75rem">المراحل تُستنتج من حالة المعاملة وتواريخها.</div>',
        unsafe_allow_html=True)

    reason = str(row.get("سبب عدم الإنجاز", "") or "")
    if late:
        card(f"🙏 <b>نعتذر منك بصدق على تأخّر معاملتك.</b> نقدّر صبرك علينا يا غالي، والجهة المختصة ({esc(dept)}) "
             f"تتابعها بأولوية.<br><b>سبب التأخير:</b> {esc(reason or 'قيد المتابعة الميدانية')}<br>"
             f"للاستفسار: {esc(contact)}. حيّاك الله وشكراً لتفهّمك.", "warn")
        speech = (f"نعتذر منك على تأخر معاملتك رقم {trx}. حالتها {label}، وتتابعها {dept} بأولوية. "
                  f"سبب التأخير {reason or 'قيد المتابعة الميدانية'}. شكراً لصبرك وتفهمك.")
    elif done:
        card("🎉 <b>تم إنجاز معاملتك بحمد الله.</b> شكراً لثقتك، ويسعدنا خدمتك دائماً.", "ok")
        speech = f"أبشر، معاملتك رقم {trx} منجزة. شكراً لثقتك بالأمانة."
    else:
        card(f"👍 معاملتك {label} وضمن المدة المتوقعة. للاستفسار: {esc(contact)}", "ai")
        speech = f"معاملتك رقم {trx} {label}، والموعد المتوقع لإنجازها {_fmt_date(due)}. للاستفسار {contact}."
    speak_button(speech, f"trk:{trx}")

    if done:  # تقييم رضا المستفيد بعد الإنجاز
        old = load_rating(trx)
        if old:
            st.caption(f"⭐ شكراً لتقييمك السابق ({old['stars']}/5).")
        else:
            pick = st.feedback("stars", key=f"fb:{trx}")
            if pick is not None:
                save_rating(trx, pick + 1)
                st.success("شكراً لتقييمك!")


def render_tracking(ctx: AuthContext, df_visible: pd.DataFrame) -> None:  # صفحة الزائر: أول تبويب، تعمل بلا تسجيل دخول وتعرض معاملات «عام» فقط للزائر
    """صفحة الزائر: أول تبويب، تعمل بلا تسجيل دخول وتعرض معاملات «عام» فقط للزائر."""
    st.markdown(recolor(_TRACK_CSS), unsafe_allow_html=True)
    st.markdown(
        '<div class="trk-hero"><h2>🔎 تتبّع معاملتك بثوانٍ</h2>'
        '<p>اكتب رقم معاملتك أو انطقه بصوتك، وتعرف جهتها وحالتها وموعد إنجازها.</p>'
        '<div class="trk-steps"><span>1️⃣ أدخل الرقم الكامل</span><span>2️⃣ اضغط بحث</span>'
        '<span>3️⃣ اطّلع على التفاصيل والخط الزمني</span></div></div>', unsafe_allow_html=True)

    with st.expander("🎙️ ابحث بصوتك (قل رقم المعاملة)"):
        audio = st.audio_input("اضغط وتحدّث", key="trk_audio", label_visibility="collapsed")
        if audio is not None:
            data = audio.getvalue()
            sig = hashlib.md5(data).hexdigest()
            if st.session_state.get("trk_sig") != sig:  # لا نعالج التسجيل نفسه مرتين
                with st.spinner("🎧 أستمع..."):
                    stt = transcribe_audio(data)
                st.session_state["trk_sig"] = sig
                found = _trx_from_speech(stt.get("text", ""))
                if found:
                    st.session_state["trk_q"] = found  # يملأ خانة البحث
                    st.session_state["trk_go"] = True
                    st.rerun()
                st.warning(stt.get("error") or "لم أسمع رقماً من 7 خانات بوضوح، أعد المحاولة ببطء أو اكتبه.")

    c1, c2 = st.columns([4, 1])
    q = c1.text_input("رقم المعاملة", key="trk_q", placeholder="مثال: TRX-JED-0755766", label_visibility="collapsed")
    go = c2.button("🔍 بحث", key="trk_btn", width="stretch") or st.session_state.pop("trk_go", False)
    if not (go or q):
        card("💡 أدخل رقم معاملتك الكامل في الخانة أعلاه ثم اضغط «بحث».", "glass")
        return

    trx = _normalize_trx(q)
    hit = df_visible[df_visible["رقم المعاملة"].astype(str) == trx]  # تطابق كامل فقط
    if hit.empty:
        card(f"🔎 {html.escape(_NOT_FOUND)}", "warn")  # رد موحّد: لا نكشف وجود معاملة سرية
        return
    audit("tracking_lookup", ctx, trx=trx)
    _tracking_result(hit.iloc[0], df_visible, ctx)
    _notify_box(ctx, hit.iloc[0])


def _notify_box(ctx: AuthContext, rec) -> None:  # للموظفين فقط: إرسال حالة المعاملة للمستفيد عبر SMS أو البريد (نص جاهز بلا بيان
    """للموظفين فقط: إرسال حالة المعاملة للمستفيد عبر SMS أو البريد (نص جاهز بلا بيانات سرية)."""
    if not ctx.can_write:
        return
    with st.expander("📣 إشعار المستفيد (SMS / بريد)"):
        trx = str(rec["رقم المعاملة"])
        exp = str(rec.get("التاريخ المتوقع للإنجاز", ""))[:10]
        msg = st.text_area("نص الإشعار", notifier.status_message(trx, str(rec["الحالة"]), exp),
                           key=f"nmsg:{trx}", height=90)
        to = st.text_input("جوال المستفيد (05XXXXXXXX) أو بريده", key=f"nto:{trx}")
        if st.button("إرسال الإشعار", key=f"nsend:{trx}", width="stretch"):
            ok, res = notifier.notify(to, "إشعار من أمانة جدة", msg, ctx)
            (st.success if ok else st.error)(res)
            audit("beneficiary_notified", ctx, trx=trx, ok=ok)  # لا نسجّل رقم الجوال


# ======================================================
# التبويب الثاني (عام): مشاريع الأمانة — عرض للجميع، إدخال وتحليل للمدير
# ======================================================
_PROJ_STATUSES = ["منفّذ", "قيد التنفيذ", "مقترح"]


_CONCEPT_TAG = "تصوّر ذكي"  # وسم إلزامي على أي صورة مولّدة بالذكاء الاصطناعي


def _pdate(v):  # تحويل نص إلى تاريخ بأمان
    try:
        return datetime.date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


def project_formula(p: dict):  # نسبة نجاح بمعادلة شفافة: التزام بالمدة 35 + الميزانية 25 + رضا المستفيدين 25 +
    """نسبة نجاح بمعادلة شفافة: التزام بالمدة 35 + الميزانية 25 + رضا المستفيدين 25 + انخفاض الشكاوى 15.
    تُحذف العناصر غير المتوفرة وتُعاد موازنة الأوزان. يرجع (النسبة, التفاصيل) أو (None, [])."""
    if p.get("status") == "مقترح":
        return None, []
    start, plan_end, act_end = _pdate(p.get("start")), _pdate(p.get("planned_end")), _pdate(p.get("actual_end"))
    parts = []
    if start and plan_end:
        planned = max((plan_end - start).days, 1)
        if act_end:
            sched = min(1.0, planned / max((act_end - start).days, 1)) * 100
        else:
            sched = 40 if datetime.date.today() > plan_end else 85
        parts.append(("الالتزام بالمدة", 35, sched))
    bud, spent = float(p.get("budget") or 0), float(p.get("spent") or 0)
    if bud > 0:
        parts.append(("الالتزام بالميزانية", 25, 100 if spent <= bud else max(0.0, 100 - (spent / bud - 1) * 200)))
    if p.get("satisfaction") is not None:
        parts.append(("رضا المستفيدين", 25, float(p["satisfaction"])))
    before, after = p.get("complaints_before"), p.get("complaints_after")
    if before and after is not None:
        red = (before - after) / before * 100
        parts.append(("انخفاض الشكاوى", 15, max(0.0, min(100.0, 50 + red / 2))))
    if not parts:
        return None, []
    total = sum(w for _, w, _ in parts)
    return round(sum(w * s for _, w, s in parts) / total), [(n, w, round(s)) for n, w, s in parts]


@st.cache_data(show_spinner=False)
def _thumb_uri(name: str, mtime: float) -> str:  # صورة مصغّرة base64 للشريط المتحرك (تُخزَّن مؤقتاً لتسريع الصفحة)
    """صورة مصغّرة base64 للشريط المتحرك (تُخزَّن مؤقتاً لتسريع الصفحة)."""
    from PIL import Image  # مثبّتة مع Streamlit
    img = Image.open(project_image_path(name)).convert("RGB")
    img.thumbnail((640, 420))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=72)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _proj_images(p: dict) -> list:  # [(اسم الملف, هل هو تصوّر ذكي)] — الصور الحقيقية أولاً
    """[(اسم الملف, هل هو تصوّر ذكي)] — الصور الحقيقية أولاً."""
    return [(n, False) for n in p.get("images", [])] + [(n, True) for n in p.get("concept_images", [])]


_GALLERY_HTML = """<!doctype html><html dir="rtl"><meta charset="utf-8"><!--keepdark--><style>
body{margin:0;font-family:'IBM Plex Sans Arabic',Tahoma,sans-serif;background:transparent}
.w{position:relative;height:300px;border-radius:22px;overflow:hidden;border:1px solid rgba(103,232,249,.3);box-shadow:0 16px 50px rgba(0,0,0,.4)}
.w img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transition:opacity 1s,transform 6s;transform:scale(1.06)}
.w img.on{opacity:1;transform:scale(1)}
.cap{position:absolute;bottom:0;left:0;right:0;padding:36px 18px 14px;background:linear-gradient(transparent,rgba(2,6,23,.92));color:#f8fafc}
.cap b{font-size:1.05rem}.cap span{display:block;font-size:.8rem;color:#94a3b8}
.tag{position:absolute;top:12px;right:12px;background:rgba(15,23,42,.8);color:#67e8f9;border:1px solid #22d3ee;border-radius:999px;padding:3px 12px;font-size:.75rem}
.dots{position:absolute;top:14px;left:14px;display:flex;gap:6px}.dots i{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,.35)}.dots i.on{background:#22d3ee}
</style><body><div class="w" id="w"><div class="tag" id="tag"></div><div class="dots" id="d"></div>
<div class="cap"><b id="n"></b><span id="m"></span></div></div><script>
const S=__DATA__,w=document.getElementById('w');let k=0;const im=[];
S.forEach((s,i)=>{const e=document.createElement('img');e.src=s.src;w.prepend(e);im.push(e);
 const d=document.createElement('i');document.getElementById('d').append(d)});
function go(){im.forEach((e,i)=>e.classList.toggle('on',i===k));
 [...document.getElementById('d').children].forEach((d,i)=>d.classList.toggle('on',i===k));
 document.getElementById('n').textContent=S[k].name;document.getElementById('m').textContent=S[k].meta;
 document.getElementById('tag').textContent=S[k].tag;k=(k+1)%S.length}
go();if(S.length>1)setInterval(go,4200);
</script></body></html>"""


def _gallery(projects: list) -> None:  # شريط متحرك بصور المشاريع (حقيقية أو تصوّر ذكي موسوم)
    """شريط متحرك بصور المشاريع (حقيقية أو تصوّر ذكي موسوم)."""
    slides = []
    for p in projects:
        for name, concept in _proj_images(p):
            path = project_image_path(name)
            if path.exists():
                slides.append({"src": _thumb_uri(name, path.stat().st_mtime), "name": p["name"],
                               "meta": f"{p.get('district', '')} · {p.get('status', '')}",
                               "tag": _CONCEPT_TAG if concept else ("بيانات تجريبية" if p.get("demo") else "صورة المشروع")})
            if len(slides) >= 14:
                break
    if not slides:
        card("🖼️ لا توجد صور بعد. يرفع المدير صور المشاريع المنفّذة من نموذج الإضافة، فتظهر هنا كشريط متحرك.", "glass")
        return
    data = json.dumps(slides, ensure_ascii=False).replace("</", "<\\/")
    _frame(_GALLERY_HTML.replace("__DATA__", data), 320)


_CAT_IMPORTANCE = (("طرق", 94), ("سفلتة", 94), ("تقاطع", 90), ("تصريف", 90), ("أمطار", 90), ("مياه", 86), ("إنارة", 80),
                   ("نظافة", 74), ("نفايات", 74), ("حدائق", 62), ("تجميل", 58), ("واجهة", 58))


def project_importance(p: dict):  # أهمية إنشاء المشروع (0–100) ومصدرها
    """أهمية إنشاء المشروع (0–100) ومصدرها. الطرق والبنية التحتية أعلى أولوية (الطرق متضررة وتمس السلامة ورؤية 2030)."""
    full = (p.get("full") or {}).get("importance")
    if full is not None:
        return float(full), "تحليل GPT-4o الكامل"
    if p.get("importance") is not None:
        return float(p["importance"]), "تقدير الذكاء الاصطناعي"
    text = f"{p.get('category', '')} {p.get('name', '')}"
    for key, val in _CAT_IMPORTANCE:
        if key in text:
            return float(val), "تقدير أولي حسب التصنيف"
    return 60.0, "تقدير أولي"


def _importance_label(v: float) -> str:  # نص ولون درجة أهمية المشروع
    return "حرجة" if v >= 90 else ("عالية" if v >= 75 else ("متوسطة" if v >= 55 else "منخفضة"))


def _is_road(p: dict) -> bool:  # هل المشروع من فئة الطرق؟ (أولوية قصوى)
    return any(k in f"{p.get('category', '')} {p.get('name', '')}" for k in ("طرق", "سفلتة", "تقاطع", "أسفلت"))


def _score_badges(p: dict) -> str:  # سطر نسبة النجاح (المعادلة + تقدير GPT) مع أهمية إنشاء المشروع، وتنبيه المراجعة
    """سطر نسبة النجاح (المعادلة + تقدير GPT) مع أهمية إنشاء المشروع، وتنبيه المراجعة عند الاختلاف الكبير."""
    f, _ = project_formula(p)
    ai = (p.get("ai") or {}).get("score")
    imp, _src = project_importance(p)
    bits = [f"🚦 أهمية المشروع: <b>{imp:.0f}% ({_importance_label(imp)})</b>"]
    if f is not None:
        bits.append(f"📐 نسبة النجاح (حسابياً): <b>{f}%</b>")
    if ai is not None:
        bits.append(f"🤖 تقدير الذكاء الاصطناعي: <b>{ai:.0f}%</b>")
    if f is not None and ai is not None and abs(f - ai) >= 15:
        bits.append('<span style="color:#fbbf24">⚠️ تحتاج مراجعة المدير (فارق كبير)</span>')
    return " · ".join(bits)


def _full_analysis_section(p: dict) -> None:  # يعرض التحليل الكامل المحفوظ للمشروع (إن وُجد) بتفاصيله
    """يعرض التحليل الكامل المحفوظ للمشروع (إن وُجد) بتفاصيله."""
    full = p.get("full")
    if not full:
        return
    esc = html.escape
    st.markdown("##### 🧠 التحليل الكامل للمشروع")
    c1, c2 = st.columns(2)
    c1.metric("أهمية إنشاء المشروع", f"{full.get('importance', 0):.0f}%")
    c2.metric("الأولوية", full.get("priority", "—"))
    for title, key in (("لماذا هو مهم؟", "importance_reason"), ("الارتباط برؤية 2030", "vision2030"), ("المستفيدون", "beneficiaries")):
        if full.get(key):
            st.markdown(f"**{title}** {esc(str(full[key]))}")
    for title, key in (("✅ الفوائد", "benefits"), ("⚠️ المخاطر", "risks"), ("💡 التوصيات", "recommendations"),
                       ("📏 مؤشرات قياس النجاح", "kpis"), ("➡️ الخطوات التالية", "next_steps")):
        if full.get(key):
            st.markdown(f"**{title}**")
            for x in full[key]:
                st.markdown(f"- {esc(str(x))}")


def _project_chat(p: dict, pid: str) -> None:  # اسأل المساعد عن هذا المشروع (نصاً أو صوتاً) فيجيب نصاً وصوتاً، وبسياق المشروع 
    """اسأل المساعد عن هذا المشروع (نصاً أو صوتاً) فيجيب نصاً وصوتاً، وبسياق المشروع فقط."""
    with st.expander("💬 اسأل المساعد عن هذا المشروع (اكتب أو تحدّث)"):
        with st.form(f"pq_form:{pid}", clear_on_submit=True):
            q = st.text_input("سؤالك", key=f"pq_t:{pid}", placeholder="مثال: ليش هذا المشروع مهم؟ وكم يتوقع ياخذ وقت؟")
            go = st.form_submit_button("إرسال", width="stretch")
        aud = st.audio_input("🎙️ أو تحدّث", key=f"pq_a:{pid}")
        question = q.strip() if go and q.strip() else None
        if aud is not None and not question:
            raw = aud.getvalue()
            sig = hashlib.md5(raw).hexdigest()
            if st.session_state.get(f"pq_sig:{pid}") != sig:
                st.session_state[f"pq_sig:{pid}"] = sig
                question = transcribe_audio(raw, "project.wav").get("text") or None
        if question:
            facts = json.dumps({k: p.get(k) for k in ("name", "district", "category", "status", "description", "budget", "spent",
                                                      "start", "planned_end", "actual_end", "satisfaction", "importance", "vision2030")},
                               ensure_ascii=False, default=str)
            full = json.dumps(p.get("full") or {}, ensure_ascii=False)[:1800]
            role = ("أنت مساعد أمانة محافظة جدة الذكي. أجب عن سؤال المستخدم عن هذا المشروع فقط، بلهجة سعودية بيضاء مهذبة وبإيجاز "
                    "(3 إلى 5 جمل)، اعتماداً على بيانات المشروع والتحليل التالي، ولا تخترع أرقاماً. الطرق متضررة بشدة وأهميتها كبيرة لرؤية 2030. "
                    "ممنوع ذكر تاريخ تدريبك. بيانات المشروع: " + facts + " التحليل: " + full)
            with st.spinner("لحظة…"):
                ans = ask_sovereign_ai(question, system_role=role)
            st.markdown(f"**أنت:** {question}")
            card(html.escape(ans).replace("\n", "<br>"), "ai")
            if not ans.startswith("❌") and st.session_state.get("speak_replies", True):
                try:
                    a = synthesize_speech(spoken_version(ans))
                    if a:
                        play_audio(a, autoplay=True)
                except Exception:
                    pass


def add_workdays(start: datetime.date, days: int) -> datetime.date:  # يضيف أيام عمل فعلية إلى تاريخ، مع استثناء الجمعة والسبت (أسبوع العمل في السعود
    """يضيف أيام عمل فعلية إلى تاريخ، مع استثناء الجمعة والسبت (أسبوع العمل في السعودية: الأحد–الخميس)."""
    d, n = start, 0
    while n < days:
        d += datetime.timedelta(days=1)
        if d.weekday() not in (4, 5):  # الجمعة=4، السبت=5
            n += 1
    return d


def cost_effort(est: dict, start: datetime.date):  # يحسب الجدول الزمني الدقيق والجهد والتكلفة من مراحل التقدير بمعادلة شفافة
    """يحسب الجدول الزمني الدقيق والجهد والتكلفة من مراحل التقدير بمعادلة شفافة.
    الجهد = أيام العمل × عدد الفريق؛ تكلفة العمالة = الجهد × الأجر اليومي؛ ثم المواد؛ ثم احتياطي 15% للمخاطر."""
    try:
        rate = float(get_setting("DAILY_LABOR_RATE_SAR", "900") or 900)
    except ValueError:
        rate = 900.0
    rows, cur, effort = [], start, 0
    for ph in est.get("phases", []):
        wd = max(1, round(float(ph["weeks"]) * 5))  # أسبوع العمل = 5 أيام
        end = add_workdays(cur, wd)
        pdays = wd * int(ph["team"])
        effort += pdays
        rows.append({"المرحلة": ph["name"], "تبدأ": f"{cur:%Y-%m-%d}", "تنتهي": f"{end:%Y-%m-%d}",
                     "أيام العمل": wd, "حجم الفريق": int(ph["team"]), "الجهد (يوم/رجل)": pdays})
        cur = end
    labor = effort * rate
    materials = float(est.get("materials_sar", 0) or 0)
    reserve = 0.15 * (labor + materials)
    total = labor + materials + reserve
    work_days = sum(r["أيام العمل"] for r in rows)
    return rows, {"effort": effort, "rate": rate, "labor": labor, "materials": materials, "reserve": reserve,
                  "total": total, "work_days": work_days, "end": cur, "calendar_days": (cur - start).days}


def _proj_visible(p: dict, ctx: AuthContext) -> bool:  # الزائر يرى المعتمد فقط؛ الموظف يرى المعتمد ومقترحاته؛ المدير يرى الكل
    """الزائر يرى المعتمد فقط؛ الموظف يرى المعتمد ومقترحاته؛ المدير يرى الكل."""
    if is_admin(ctx):
        return True
    if p.get("approval") in (None, "معتمد"):
        return True
    return bool(ctx.logged_in and p.get("created_by") == ctx.username)


def _cost_effort_section(p: dict, pid: str) -> None:  # قسم التكلفة والجهد والزمن (للمدير فقط)
    """قسم التكلفة والجهد والزمن (للمدير فقط)."""
    st.markdown("##### 💰 تقدير التكلفة والجهد والزمن (للمدير فقط)")
    est = p.get("estimate")
    if st.button("🧮 احسب التكلفة والجهد (GPT-4o + معادلة)", key=f"est:{pid}", width="stretch"):
        with st.spinner("يقدّر المراحل والفرق..."):
            res = estimate_cost_effort(p)
        if res.get("error"):
            st.error(res["error"])
        else:
            ctx = get_auth_context()
            p["estimate"] = res
            save_project_versioned(p, ctx.username or "-", ctx.role, "حساب تقدير التكلفة والجهد")
            audit("project_cost_estimate", ctx, project=pid)
            st.session_state["proj_speak_est"] = pid
            st.rerun(scope="fragment")
    if not est:
        st.caption("لم يُحسب التقدير بعد. اضغط الزر أعلاه.")
        return
    rows, tot = cost_effort(est, datetime.date.today())
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    c1, c2, c3 = st.columns(3)
    c1.metric("المدة (أيام عمل)", f"{tot['work_days']:,}", help="مجموع أيام عمل المراحل (الأحد–الخميس)")
    c2.metric("الجهد (يوم/رجل)", f"{tot['effort']:,}", help="أيام العمل × عدد الفريق لكل مرحلة")
    c3.metric("التكلفة التقديرية (ر.س)", f"{tot['total']:,.0f}")
    st.markdown(f"**موعد الانتهاء المتوقع:** {tot['end']:%Y-%m-%d} ({tot['calendar_days']} يوماً تقويمياً من اليوم، دون الجمعة والسبت).")
    st.dataframe(pd.DataFrame([
        {"البند": "عمالة", "كيف حُسب؟": f"{tot['effort']:,} يوم/رجل × {tot['rate']:,.0f} ر.س أجر يومي", "المبلغ (ر.س)": f"{tot['labor']:,.0f}"},
        {"البند": "مواد ومعدات", "كيف حُسب؟": "تقدير أولي من الذكاء الاصطناعي", "المبلغ (ر.س)": f"{tot['materials']:,.0f}"},
        {"البند": "احتياطي المخاطر", "كيف حُسب؟": "15% من (العمالة + المواد)", "المبلغ (ر.س)": f"{tot['reserve']:,.0f}"},
        {"البند": "الإجمالي", "كيف حُسب؟": "مجموع البنود الثلاثة", "المبلغ (ر.س)": f"{tot['total']:,.0f}"}]),
        hide_index=True, width="stretch")
    for k, title in (("assumptions", "الافتراضات"), ("risks", "المخاطر")):
        if est.get(k):
            st.markdown(f"**{title}:** " + "، ".join(html.escape(x) for x in est[k]))
    st.caption("تقدير أولي للتخطيط وليس عرض سعر. الأجر اليومي يُضبط من .env بالمتغير DAILY_LABOR_RATE_SAR (الافتراضي 900).")
    if st.session_state.get("proj_speak_est") == pid:
        st.session_state.pop("proj_speak_est", None)
        _speak_once(f"تقدير مشروع {p['name']}: المدة {tot['work_days']} يوم عمل، والجهد {tot['effort']} يوم رجل، "
                    f"والتكلفة التقديرية {tot['total']:,.0f} ريال، والانتهاء المتوقع {tot['end']:%Y-%m-%d}.", f"est:{pid}:{est.get('at', '')}")


def _workflow_section(p: dict, pid: str, ctx: AuthContext, admin: bool) -> None:  # سير الاعتماد: الموظف يعدّل ويرسل، والمدير يعتمد أو يعيد بملاحظات
    """سير الاعتماد: الموظف يعدّل ويرسل، والمدير يعتمد أو يعيد بملاحظات. كل خطوة تُسجَّل كنسخة."""
    state = p.get("approval") or "معتمد"
    st.markdown(f"**حالة الاعتماد:** {state}" + (f" — ملاحظة المراجعة: {html.escape(p.get('review_note', ''))}" if p.get("review_note") else ""),
                unsafe_allow_html=True)
    who = ctx.username or "-"
    mine = ctx.logged_in and p.get("created_by") == ctx.username and not admin
    if mine and state != "معتمد":  # الموظف يعدّل مقترحه قبل الاعتماد فقط
        with st.form(f"edit:{pid}"):
            desc = st.text_area("وصف المقترح", value=p.get("description", ""))
            cat = st.text_input("التصنيف", value=p.get("category", ""))
            note = st.text_input("ماذا عدّلت؟ (يُسجَّل في النسخ)")
            c1, c2 = st.columns(2)
            save_draft = c1.form_submit_button("💾 حفظ تعديل", width="stretch")
            send = c2.form_submit_button("📤 إرسال للاعتماد", width="stretch")
            if save_draft or send:
                p.update({"description": desc.strip(), "category": cat.strip(),
                          "approval": "بانتظار الاعتماد" if send else "مسودة", "review_note": ""})
                save_project_versioned(p, who, ctx.role, note or ("إرسال للاعتماد" if send else "تعديل"))
                audit("project_edited", ctx, project=pid, sent=bool(send))
                st.rerun(scope="fragment")
    if admin and state in ("بانتظار الاعتماد", "أُعيد بملاحظات", "مسودة"):
        note = st.text_input("ملاحظة المدير (إلزامية عند الإعادة)", key=f"rn:{pid}")
        a, b = st.columns(2)
        if a.button("✅ اعتماد", key=f"ok:{pid}", width="stretch"):
            p.update({"approval": "معتمد", "review_note": ""})
            save_project_versioned(p, who, ctx.role, note or "اعتماد")
            audit("project_approved", ctx, project=pid)
            st.rerun(scope="fragment")
        if b.button("↩️ إعادة بملاحظات", key=f"rt:{pid}", width="stretch"):
            if not note.strip():
                st.warning("اكتب ملاحظتك ليعرف الموظف ما المطلوب تعديله.")
            else:
                p.update({"approval": "أُعيد بملاحظات", "review_note": note.strip()})
                save_project_versioned(p, who, ctx.role, "إعادة بملاحظات: " + note.strip())
                audit("project_returned", ctx, project=pid)
                st.rerun(scope="fragment")


def _history_section(p: dict, pid: str, ctx: AuthContext, admin: bool) -> None:  # سجل النسخ: من عدّل ومتى وماذا تغيّر؛ للمدير زر استرجاع
    """سجل النسخ: من عدّل ومتى وماذا تغيّر؛ للمدير زر استرجاع. حقل التقدير المالي مخفي عن غير المدير."""
    hist = list(reversed(p.get("history", [])))
    if not hist or not ctx.logged_in:
        return
    with st.expander(f"🕘 سجل النسخ والتعديلات ({len(hist)})"):
        for h in hist:
            changes = {k: v for k, v in h.get("changes", {}).items() if admin or k != "estimate"}
            line = f"**النسخة {h['v']}** · {h['at']} · {html.escape(str(h['by']))} ({h['role']}) — {html.escape(h.get('note') or '')}"
            if changes:
                line += "<br>" + "؛ ".join(f"{html.escape(k)}: {html.escape(a)} ← {html.escape(b)}" for k, (a, b) in changes.items())
            st.markdown(line, unsafe_allow_html=True)
            if admin and h.get("snap") and st.button(f"↩️ استرجاع الحالة قبل النسخة {h['v']}", key=f"rv:{pid}:{h['v']}"):
                if revert_project(pid, h["v"], ctx.username or "-", ctx.role):
                    audit("project_reverted", ctx, project=pid, version=h["v"])
                    st.rerun(scope="fragment")


@st.dialog("تفاصيل المشروع", width="large")
def _project_dialog(pid: str, admin: bool) -> None:  # نافذة تفاصيل المشروع: تقدير ونجاح وتحليل ومحادثة
    p = next((x for x in load_projects() if x.get("id") == pid), None)
    if not p:
        st.warning("المشروع غير موجود.")
        return
    esc = html.escape
    st.markdown(f"### {esc(p['name'])}" + ("  🏷️ **بيانات تجريبية**" if p.get("demo") else ""))
    for name, concept in _proj_images(p):
        if project_image_path(name).exists():
            st.image(str(project_image_path(name)), caption=_CONCEPT_TAG if concept else "صورة المشروع", width="stretch")
    st.markdown(f"**الحي:** {esc(p.get('district', '—'))} · **التصنيف:** {esc(p.get('category', '—'))} · "
                f"**الحالة:** {esc(p.get('status', '—'))}")
    st.caption(esc(p.get("description", "")))
    if p.get("status") != "مقترح":
        st.markdown(f"**الميزانية:** {float(p.get('budget') or 0):,.0f} ر.س · **المصروف:** {float(p.get('spent') or 0):,.0f} ر.س<br>"
                    f"**البدء:** {p.get('start') or '—'} · **النهاية المخططة:** {p.get('planned_end') or '—'} · "
                    f"**الفعلية:** {p.get('actual_end') or '—'}", unsafe_allow_html=True)
    else:
        st.markdown(f"**الفكرة:** {esc(p.get('description', ''))}")
    card(_score_badges(p), "ai")
    imp_v, imp_src = project_importance(p)
    st.progress(min(imp_v, 100) / 100, text=f"أهمية إنشاء المشروع {imp_v:.0f}% — {_importance_label(imp_v)} ({imp_src})")
    if _is_road(p):
        card("🛣️ <b>أولوية قصوى:</b> الطرق متضررة ومتكسّرة وتمسّ السلامة وجودة الحياة وصورة المدينة، وهي من أهم مستهدفات رؤية 2030 للمدن.", "warn")
    if p.get("vision2030"):
        st.markdown(f"**🇸🇦 الارتباط برؤية 2030:** {esc(str(p['vision2030']))}")
    if st.button("🔊 اشرح لي المشروع صوتياً", key=f"say:{pid}", width="stretch"):  # شرح منطوق بدل قراءة الجداول
        score, _p = project_formula(p)
        say = (f"{p['name']}، في {p.get('district', 'جدة')}، تصنيفه {p.get('category', '')}، وحالته {p.get('status', '')}. "
               f"{p.get('description', '')} " + (f"ونسبة نجاحه {score:.0f} بالمئة." if score is not None else ""))
        with st.spinner("يجهّز الشرح الصوتي…"):
            try:
                audio = synthesize_speech(spoken_version(say))
            except Exception:
                audio = b""
        if audio:
            play_audio(audio, autoplay=True)
        else:
            st.warning("تعذّر الشرح الصوتي الآن (تحقق من اتصال الذكاء الاصطناعي).")
    _, parts = project_formula(p)
    if parts:
        meaning = {"الالتزام بالمدة": "هل انتهى في الوقت المخطط؟ (100 = في الموعد، أقل = تأخّر)",
                   "الالتزام بالميزانية": "هل التزم بالميزانية؟ (100 = لم يتجاوزها، أقل = تجاوزها)",
                   "رضا المستفيدين": "نسبة رضا السكان عن المشروع بعد تنفيذه",
                   "انخفاض الشكاوى": "هل قلّت شكاوى الحي بعد المشروع؟ (50 = لا تغيّر، 100 = اختفت)"}
        total_w = sum(w for _, w, _ in parts)
        rows = [{"المعيار": n, "ماذا يقيس؟": meaning.get(n, ""), "درجته من 100": sc,
                 "أهميته في النسبة": f"{w * 100 / total_w:.0f}%", "ما أضافه للنسبة": f"{sc * w / total_w:.1f}"}
                for n, w, sc in parts]
        st.markdown("##### 📐 كيف حُسبت نسبة النجاح؟")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption("الطريقة: لكل معيار درجة من 100، وكل معيار له أهمية (وزن). النسبة النهائية = مجموع «ما أضافه كل معيار». "
                   "مثال: معيار أهميته 35% ودرجته 90 يضيف 31.5 نقطة. المعايير غير المتوفرة تُحذف وتُوزَّع أهميتها على الباقي. "
                   "وتقدير GPT-4o رأي إضافي للمراجعة وليس قياساً رسمياً.")
    ai = p.get("ai") or {}
    if ai.get("summary"):
        st.markdown(f"**🤖 قراءة الذكاء الاصطناعي:** {esc(ai['summary'])}")
        if st.session_state.get("proj_speak") == pid:
            st.session_state.pop("proj_speak", None)
            _say = (p.get("full") or {}).get("spoken_summary") or f"{p['name']}. {ai['summary']} تقدير نجاح المشروع {ai.get('score', 0):.0f} بالمئة."
            _speak_once(_say, f"prj:{pid}:{ai.get('at','')}")
        for k, title in (("factors", "العوامل المؤثرة"), ("risks", "المخاطر والتوصيات")):
            if ai.get(k):
                st.markdown(f"**{title}:** " + "، ".join(esc(str(x)) for x in ai[k]))
    _full_analysis_section(p)
    _project_chat(p, pid)
    ctx = get_auth_context()
    if p.get("status") == "مقترح" or p.get("approval"):
        _workflow_section(p, pid, ctx, admin)
    if admin:
        _cost_effort_section(p, pid)
    _history_section(p, pid, ctx, admin)
    if admin:
        a, b, c = st.columns(3)
        if a.button("🤖 تحليل كامل بـ GPT-4o", key=f"an:{pid}", width="stretch"):
            with st.spinner("يحلّل المشروع بالكامل (النجاح + الأهمية + المخاطر + التوصيات)..."):
                res = estimate_project_success(p)
                full = analyze_project_full(p)
            if res.get("error"):
                st.error(res["error"])
            else:
                p["ai"] = res
                if not full.get("error"):
                    p["full"] = full
                    p["importance"] = full.get("importance")
                save_project(p)
                audit("project_ai_estimate", get_auth_context(), project=pid)
                st.session_state["proj_speak"] = pid  # ننطق النتيجة بعد إعادة رسم النافذة
                st.rerun(scope="fragment")  # يعيد رسم النافذة فقط فلا تُغلق
        if b.button("🖼️ ولّد تصوّراً ذكياً", key=f"img:{pid}", width="stretch"):
            with st.spinner("يرسم التصوّر..."):
                raw = generate_concept_image(f"{p['name']} {p.get('description', '')} {p.get('category', '')}")
            if raw:
                p.setdefault("concept_images", []).append(save_project_image(raw, "png"))
                save_project(p)
                st.rerun(scope="fragment")
            st.error("تعذّر توليد الصورة (تحقق من الرصيد/النموذج).")
        if c.button("🗑️ حذف المشروع", key=f"del:{pid}", width="stretch"):
            delete_projects(ids=[pid])
            audit("project_deleted", get_auth_context(), project=pid)
            st.rerun()


def _project_form() -> None:  # نموذج إدخال مشروع (للمدير): بيانات + صور حقيقية
    """نموذج إدخال مشروع (للمدير): بيانات + صور حقيقية."""
    with st.expander("➕ إضافة مشروع (للمدير)"):
        with st.form("proj_form", clear_on_submit=True):
            name = st.text_input("اسم المشروع الدقيق")
            c1, c2, c3 = st.columns(3)
            district = c1.selectbox("الحي", DISTRICTS)
            category = c2.text_input("التصنيف", value="طرق")
            status = c3.selectbox("الحالة", _PROJ_STATUSES)
            c4, c5 = st.columns(2)
            budget = c4.number_input("الميزانية (ر.س)", min_value=0.0, step=100000.0)
            spent = c5.number_input("المصروف (ر.س)", min_value=0.0, step=100000.0)
            d1, d2, d3 = st.columns(3)
            start = d1.date_input("تاريخ البدء", value=datetime.date.today() - datetime.timedelta(days=180))
            plan = d2.date_input("النهاية المخططة", value=datetime.date.today())
            actual = d3.date_input("النهاية الفعلية (اتركه إن لم ينتهِ)", value=None)
            e1, e2, e3 = st.columns(3)
            sat = e1.number_input("رضا المستفيدين % (0 = غير متوفر)", 0, 100, 0)
            cb = e2.number_input("الشكاوى قبل المشروع (0 = غير متوفر)", 0, 1_000_000, 0)
            ca = e3.number_input("الشكاوى بعده", 0, 1_000_000, 0)
            desc = st.text_area("وصف المشروع")
            files = st.file_uploader("صور حقيقية للمشروع (حتى 5)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            if st.form_submit_button("💾 حفظ المشروع", width="stretch"):
                if not name.strip():
                    st.error("اسم المشروع مطلوب.")
                else:
                    imgs = [save_project_image(f.getvalue(), f.name.rsplit(".", 1)[-1]) for f in (files or [])[:5]
                            if len(f.getvalue()) <= 5_000_000]
                    c_ = get_auth_context()
                    save_project_versioned({"name": name.strip(), "district": district, "category": category.strip(),
                                  "budget": budget, "spent": spent, "start": start.isoformat(),
                                  "planned_end": plan.isoformat(), "actual_end": actual.isoformat() if actual else None,
                                  "status": status, "satisfaction": sat or None, "complaints_before": cb or None,
                                  "complaints_after": ca if cb else None, "description": desc.strip(),
                                  "images": imgs, "concept_images": [], "demo": False, "ai": None,
                                  "approval": "معتمد", "created_by": c_.username}, c_.username or "-", c_.role, "إنشاء المشروع")
                    audit("project_added", get_auth_context(), name=name.strip()[:60])
                    st.success("تم حفظ المشروع.")
                    st.rerun()


def _proposal_form(ctx: AuthContext) -> None:  # نموذج اقتراح مشروع للموظف: يُحفظ «بانتظار الاعتماد» ولا يراه الزوار حتى يعتمده
    """نموذج اقتراح مشروع للموظف: يُحفظ «بانتظار الاعتماد» ولا يراه الزوار حتى يعتمده المدير."""
    with st.expander("💡 اقتراح مشروع جديد (للموظف)"):
        with st.form("prop_form", clear_on_submit=True):
            name = st.text_input("اسم المشروع المقترح")
            c1, c2 = st.columns(2)
            district = c1.selectbox("الحي", DISTRICTS)
            category = c2.text_input("التصنيف", value="طرق")
            desc = st.text_area("وصف الفكرة وفائدتها")
            files = st.file_uploader("صورة توضيحية (اختياري)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            if st.form_submit_button("📤 إرسال للاعتماد", width="stretch"):
                if not name.strip() or not desc.strip():
                    st.error("الاسم والوصف مطلوبان.")
                else:
                    imgs = [save_project_image(f.getvalue(), f.name.rsplit(".", 1)[-1]) for f in (files or [])[:3]
                            if len(f.getvalue()) <= 5_000_000]
                    save_project_versioned({"name": name.strip(), "district": district, "category": category.strip(),
                                            "status": "مقترح", "description": desc.strip(), "images": imgs,
                                            "concept_images": [], "demo": False, "ai": None, "approval": "بانتظار الاعتماد",
                                            "created_by": ctx.username}, ctx.username or "-", ctx.role, "اقتراح جديد")
                    audit("project_proposed", ctx, name=name.strip()[:60])
                    st.success("أُرسل مقترحك للمدير للاعتماد.")
                    st.rerun()


def _project_cards(projects: list, admin: bool, prefix: str) -> None:  # شبكة بطاقات المشاريع؛ زر «التفاصيل» يفتح نافذة
    """شبكة بطاقات المشاريع؛ زر «التفاصيل» يفتح نافذة."""
    cols = st.columns(3)
    for i, p in enumerate(projects):
        with cols[i % 3].container(border=True):
            imgs = [n for n, _ in _proj_images(p) if project_image_path(n).exists()]
            if imgs:
                st.image(str(project_image_path(imgs[0])), width="stretch",
                         caption=_CONCEPT_TAG if imgs[0] in p.get("concept_images", []) else None)
            st.markdown(f"**{html.escape(p['name'])}**" + ("  🏷️ تجريبي" if p.get("demo") else ""))
            st.caption(f"{p.get('district', '')} · {p.get('status', '')}"
                       + (f" · ⏳ {p['approval']}" if p.get("approval") not in (None, "معتمد") else ""))
            st.markdown(_score_badges(p), unsafe_allow_html=True)
            if st.button("🔎 التفاصيل", key=f"{prefix}:{p['id']}", width="stretch"):
                _project_dialog(p["id"], admin)


def render_projects(ctx: AuthContext, df_all: pd.DataFrame) -> None:  # مشاريع الأمانة: شريط صور حيّ، بطاقات المنفّذة وقيد التنفيذ، ثم المقترحة
    """مشاريع الأمانة: شريط صور حيّ، بطاقات المنفّذة وقيد التنفيذ، ثم المقترحة. للجميع؛ الإدخال والتحليل للمدير."""
    admin = is_admin(ctx)
    st.markdown(recolor(_TRACK_CSS), unsafe_allow_html=True)
    st.markdown('<div class="trk-hero"><h2>🏗️ مشاريع أمانة محافظة جدة</h2>'
                '<p>ما أُنجز خلال السنة وما قيد التنفيذ والمقترح، مع نسبة نجاح بمعادلة شفافة وقراءة بالذكاء الاصطناعي.</p></div>',
                unsafe_allow_html=True)
    projects = [x for x in load_projects() if _proj_visible(x, ctx)]  # الزائر يرى المعتمد فقط
    if any(p.get("demo") for p in projects):
        card("🏷️ <b>بيانات تجريبية:</b> المشاريع الموسومة «تجريبي» أمثلة لعرض الصفحة وليست مشاريع حقيقية.", "warn")
    _tech_numbers()  # شريط الإنجازات التقني (هنا فقط)
    _gallery(projects)
    if ctx.logged_in and not admin:
        _proposal_form(ctx)
    if admin:
        _project_form()
        if any(p.get("demo") for p in projects) and st.button("🧹 حذف كل المشاريع التجريبية", key="del_demo"):
            audit("projects_demo_deleted", ctx)
            delete_projects(demo_only=True)
            st.rerun()

    done_like = sorted([p for p in projects if p.get("status") != "مقترح"], key=lambda x: x.get("start", ""), reverse=True)
    if done_like:
        st.subheader("✅ المنفّذة وقيد التنفيذ")
        _project_cards(done_like, admin, "pc")
    st.subheader("🔮 مشاريع مقترحة")
    st.caption("اقتراحات بالذكاء الاصطناعي بناءً على احتياج الأحياء، وصورها «تصوّر ذكي» وليست مشاريع منفّذة.")
    if admin and st.button("🤖 اقترح مشاريع من بيانات المنصة", key="suggest_btn"):
        top = df_all[df_all["الحالة"] != STATUS_DONE]["الحي"].astype(str).value_counts().head(5).to_dict()
        with st.spinner("يحلّل احتياج الأحياء..."):
            ideas = suggest_projects(f"أكثر الأحياء معاملات مفتوحة: {top}. أقسام: {DEPARTMENTS}. "
                                     "ملاحظة الإدارة: الطرق متضررة ومتكسّرة للغاية وتؤثر على رؤية 2030؛ أعطها أولوية قصوى.")
        for s in ideas:
            save_project({"name": s["name"], "district": s.get("district", ""), "category": s.get("category", ""),
                          "status": "مقترح", "description": f"{s.get('idea', '')} — {s.get('why', '')}",
                          "approval": "معتمد", "created_by": ctx.username,
                          "importance": s.get("importance"), "priority": s.get("priority"), "vision2030": s.get("vision2030"),
                          "images": [], "concept_images": [], "demo": False,
                          "ai": {"score": float(s.get("expected_success", 0) or 0), "summary": s.get("why", ""),
                                 "factors": [], "risks": []}, "image_prompt": s.get("image_prompt", "")})
        audit("projects_suggested", ctx, n=len(ideas))
        st.rerun()
    proposed = sorted([p for p in projects if p.get("status") == "مقترح"], key=lambda x: project_importance(x)[0], reverse=True)  # الأهم أولاً
    if admin and proposed and st.button("🗑️ حذف كل المقترحات (لإعادة توليدها بالعربية)", key="del_prop"):
        delete_projects(ids=[p["id"] for p in proposed])
        audit("projects_proposals_deleted", ctx)
        st.rerun()
    if proposed:
        _project_cards(proposed, admin, "pp")
    else:
        st.info("لا توجد مقترحات بعد." + (" اضغط «اقترح مشاريع»." if admin else ""))


# ======================================================
# تبويب المساعدة والتدريب: أسئلة شائعة + جولة تعريفية + «بلّغ عن مشكلة»
# ======================================================
_FAQ = [
    ("كيف أتابع معاملتي؟", "من تبويب «تتبّع معاملتك» اكتب رقم المعاملة كاملاً (مثال TRX-JED-0755766) أو انطقه بصوتك، فتظهر جهتها وحالتها وموعد إنجازها."),
    ("لماذا لا أجد معاملتي؟", "تأكد من الرقم كاملاً. الزائر يرى المعاملات العامة فقط، وقد تكون معاملتك بمستوى سرية أعلى فتظهر للموظف المخوّل."),
    ("ما معنى «معلّقة بانتظار المباشرة»؟", "استُلمت المعاملة ووُجّهت للقسم المختص ولم يبدأ العمل عليها بعد."),
    ("ما الفرق بين الحالات؟", "جاري العمل = الفريق يعمل عليها الآن. معلّقة = بانتظار البدء. منجزة = اكتملت."),
    ("كيف أتحدث إلى المساعد الذكي؟", "من الشريط الجانبي اضغط زر التسجيل وتحدّث بلهجتك، وسيردّ عليك صوتاً ونصاً ضمن صلاحيتك."),
    ("ما معنى نسبة نجاح المشروع؟", "تجمع التزامه بالمدة والميزانية ورضا المستفيدين وانخفاض الشكاوى بأوزان معلنة، ويُضاف إليها تقدير الذكاء الاصطناعي للمقارنة. تفاصيلها في نافذة كل مشروع."),
    ("لماذا لا أرى بعض الصفحات؟", "صفحات التحليل والعمليات والحوكمة للمدير فقط، حمايةً للبيانات. الموظف يرى ما يخص عمله."),
    ("كيف أكبّر الواجهة أو أبسّطها؟", "فعّل «الوضع المبسّط» من الشريط الجانبي فتظهر لك الصفحات الأساسية فقط."),
]


_TOUR = {
    "guest": ["1️⃣ افتح «تتبّع معاملتك» واكتب رقم معاملتك.", "2️⃣ اطّلع على الحالة والمدة المتبقية والخط الزمني.",
              "3️⃣ شاهد «مشاريع الأمانة» لتعرف ما أُنجز في أحيائك.", "4️⃣ اسأل المساعد الصوتي من الشريط الجانبي."],
    "employee": ["1️⃣ سجّل الدخول من الشريط الجانبي.", "2️⃣ أدخل المعاملات من «إدخال البيانات» (يدوياً أو بصورة).",
                 "3️⃣ ارفع تنبيهاً من «العمليات» ليعتمده المدير.", "4️⃣ اقترح مشروعاً من «مشاريع الأمانة» وتابع ملاحظات المدير.",
                 "5️⃣ اصنع خطاباً رسمياً من «الخطابات الرسمية»."],
    "admin": ["1️⃣ راجع «لوحة التحليلات» والمتأخرات.", "2️⃣ تابع «غرفة العمليات» واعتمد التنبيهات.",
              "3️⃣ اعتمد المقترحات واحسب تكلفتها من «مشاريع الأمانة».", "4️⃣ أصدر التقرير التنفيذي الشهري من «الخطابات والتقارير».",
              "5️⃣ افحص «جودة البيانات» دورياً."],
}


def render_help(ctx: AuthContext) -> None:  # صفحة المساعدة: متاحة للجميع
    """صفحة المساعدة: متاحة للجميع."""
    st.subheader("🎓 المساعدة والتدريب")
    st.markdown("#### 🧭 جولة سريعة لدورك")
    for step in _TOUR.get(ctx.role, _TOUR["employee"] if ctx.logged_in else _TOUR["guest"]):
        st.markdown(f"- {step}")
    st.markdown("#### ❓ الأسئلة الشائعة")
    for q, a in _FAQ:
        with st.expander(q):
            st.write(a)
    st.markdown("#### 🛠️ بلّغ عن مشكلة أو اقتراح")
    with st.form("issue_form", clear_on_submit=True):
        cat = st.selectbox("نوع البلاغ", ["خطأ في المنصة", "معلومة غير صحيحة", "اقتراح تطوير", "صعوبة في الاستخدام", "أخرى"])
        text = st.text_area("اشرح ما حدث (ولا تكتب معلومات سرية)")
        if st.form_submit_button("📤 إرسال", width="stretch"):
            if len(text.strip()) < 10:
                st.error("اكتب وصفاً أوضح (10 أحرف على الأقل).")
            else:
                save_issue(cat, text, ctx.username or "زائر", ctx.role)
                audit("issue_reported", ctx, category=cat)
                st.success("شكراً لك، وصل بلاغك للمدير.")
    if is_admin(ctx):
        issues = load_issues()
        with st.expander(f"📥 البلاغات الواردة ({len(issues)})"):
            if issues:
                st.dataframe(pd.DataFrame(issues), hide_index=True, width="stretch")
            else:
                st.caption("لا توجد بلاغات.")


# ======================================================
# بيانات مفتوحة (عامة): مؤشرات مجمّعة من المعاملات «العامة» فقط
# ======================================================
_MIN_CELL = 10  # أي فئة أقل من هذا العدد تُخفى حمايةً للخصوصية


def render_open_data(df_all: pd.DataFrame) -> None:  # صفحة شفافية عامة: لا أرقام معاملات ولا نصوص ولا بيانات سرية، مؤشرات مجمّعة فقط
    """صفحة شفافية عامة: لا أرقام معاملات ولا نصوص ولا بيانات سرية، مؤشرات مجمّعة فقط."""
    import plotly.graph_objects as go
    from ui import style_fig
    st.subheader("📈 بيانات مفتوحة")
    pub = visible_transactions(df_all, GUEST)  # المستوى «عام» فقط مهما كانت صلاحية من يتصفح
    if pub.empty:
        st.info("لا توجد بيانات عامة بعد.")
        return
    done = pub["الحالة"] == STATUS_DONE
    today = pd.Timestamp.today().normalize()
    late = (~done) & (pub["تاريخ الإنجاز المتوقع"] < today)
    k1, k2, k3 = st.columns(3)
    k1.metric("معاملات عامة", f"{len(pub):,}")
    k2.metric("نسبة الإنجاز", f"{done.mean() * 100:.1f}%")
    k3.metric("تجاوزت موعدها", f"{late.mean() * 100:.1f}%")
    c1, c2 = st.columns(2)
    dept = (pub.assign(_d=done).groupby("القسم المكلف", observed=True)
            .agg(المعاملات=("رقم المعاملة", "count"), المنجز=("_d", "sum")).reset_index())
    dept = dept[dept["المعاملات"] >= _MIN_CELL]
    dept["نسبة الإنجاز %"] = (dept["المنجز"] / dept["المعاملات"] * 100).round(1)
    with c1:
        st.markdown("##### 🏢 نسبة الإنجاز حسب القسم")
        fig = go.Figure(go.Bar(x=dept["نسبة الإنجاز %"], y=dept["القسم المكلف"], orientation="h",
                               marker_color="#22d3ee", hovertemplate="%{y}: %{x}%<extra></extra>"))
        style_fig(fig)
        fig.update_layout(height=320, xaxis_range=[0, 100])
        st.plotly_chart(fig, width="stretch")
    monthly = pub.groupby(pub["تاريخ الاستلام"].dt.to_period("M")).size().tail(12)
    with c2:
        st.markdown("##### 📅 المعاملات المستلمة شهرياً")
        fig = go.Figure(go.Scatter(x=[str(p) for p in monthly.index], y=monthly.values, mode="lines+markers",
                                   line=dict(color="#e0b84c", width=3), fill="tozeroy"))
        style_fig(fig)
        fig.update_layout(height=320)
        st.plotly_chart(fig, width="stretch")
    dist = pub["الحي"].astype(str).value_counts()
    dist = dist[dist >= _MIN_CELL].rename_axis("الحي").reset_index(name="المعاملات")
    st.dataframe(dist, hide_index=True, width="stretch")
    st.download_button("⬇️ تنزيل المؤشرات CSV", csv_bytes(dept), file_name="open_data_departments.csv", mime="text/csv")
    st.caption(f"مؤشرات مجمّعة من المعاملات العامة فقط، لا تتضمن بيانات أفراد أو معاملات سرية، وتُخفى أي فئة أقل من {_MIN_CELL} معاملات.")


# ======================================================
# الترحيب الصوتي (مرة لكل جلسة) — المتصفح قد يمنع التشغيل التلقائي حتى أول نقرة
# ======================================================
def welcome_voice(ctx: AuthContext) -> None:  # الترحيب الصوتي مرة لكل جلسة
    if not st.session_state.get("speak_replies", True) or client is None:
        return
    if "greet_audio" not in st.session_state:
        h = datetime.datetime.now().hour
        part = "صباح الخير" if 4 <= h < 12 else ("مساء الخير" if h < 18 else "مساء النور")
        who = "ضيفنا الكريم"  # الزائر
        if ctx.logged_in:  # اسم الدخول الإنجليزي (admin مثلاً) يُنطق خطأً ويجعل النموذج يعيد صياغة الجملة فتتغيّر؛ فنستعمل الاسم فقط إن كان عربياً
            who = ctx.username if re.fullmatch(r"[؀-ۿ ]+", str(ctx.username or "")) else "زميلنا الكريم"
        text = (f"{part} يا {who}، حيّاك الله في منصة أمانة محافظة جدة الذكية. "
                "أنا مساعدك، أتابع لك معاملتك أو أعرّفك على المشاريع، وأمرّك على أي شيء تحتاجه. تفضّل.")
        try:
            st.session_state["greet_audio"] = synthesize_speech(spoken_version(text))
        except Exception:
            st.session_state["greet_audio"] = None
    audio = st.session_state.get("greet_audio")
    if audio:
        autoplay = not st.session_state.get("greet_played")
        st.session_state["greet_played"] = True  # يُشغَّل تلقائياً مرة واحدة فقط
        play_audio(audio, autoplay=autoplay, label="ترحيب")  # يُنطق تلقائياً مرة واحدة (إن سمح المتصفح)، وزر 🔊 للإعادة بلا شريط ولا مؤقّت


# ======================================================
# أرقام وإنجازات + روابط تهمك (أرقام مجمّعة غير حساسة فقط)
# ======================================================
_TAB_LINKS = [("t_tracking", "🔎", "تتبّع معاملتك", "تتبّع معاملتك"), ("t_projects", "🏗️", "مشاريع الأمانة", "مشاريع الأمانة"),
              ("t_opendata", "📈", "بيانات مفتوحة", "بيانات مفتوحة"), ("t_training", "🎓", "التدريب والدعم", "التدريب والدعم"),
              ("t_feedback", "💬", "رأيك يهمنا", "رأيك يهمنا"), ("t_privacy", "🔐", "الأمان والخصوصية", "الأمان والخصوصية")]  # (مفتاح، أيقونة، نص الزر، كلمة تحدد التبويب)


_EXTRA_TABS = [("t_dash", "لوحة التحليلات"), ("t_intake", "إدخال البيانات"), ("t_field", "الفرق الميدانية"), ("t_ops", "العمليات والإنذارات"),
               ("t_letters", "الخطابات الرسمية"), ("t_quality", "جودة البيانات"), ("t_ready", "جاهزية المشروع")]  # أزرار مخفية إضافية يضغطها الشخصيتان (للموظفين)


_DOCK_ITEMS = [("PG_home", "🏠", "الرئيسية"), ("PG_t_tracking", "🔎", "تتبّع معاملتك"), ("PG_assistant", "💬", "المساعد"),
               ("PG_services", "🧩", "خدماتي"), ("PG_t_projects", "🏗️", "مشاريع الأمانة"), ("PG_t_opendata", "📈", "بيانات مفتوحة"),
               ("PG_t_feedback", "⭐", "رأيك يهمنا"), ("PG_support", "🛟", "الدعم"), ("PG_faq", "❓", "الأسئلة الشائعة"),
               ("PG_t_training", "🎓", "التدريب"), ("PG_t_privacy", "🔐", "الأمان"), ("PG_access", "♿", "إمكانية الوصول")]  # (معرّف الزر المخفي، أيقونة، نص) — بهذا الترتيب يظهر الشريط السفلي


def _dock_active() -> str:  # يحدد الزر المميّز في الشريط السفلي حسب الصفحة المفتوحة الآن
    """يحدد الزر المميّز في الشريط السفلي حسب الصفحة المفتوحة الآن."""
    view = st.session_state.get("view")
    if not view:
        return "PG_home"
    if str(view).startswith("tab:"):
        word = str(view)[4:]
        for key, _, _, w in _TAB_LINKS:
            if w in word or word in w:
                return "PG_" + key
        return ""
    return "PG_" + str(view)


def render_quick_links() -> None:  # الشريط السفلي الثابت: كل الروابط المهمة تحت الشاشة دائماً، وتفتح صفحة مستقلة عبر أزرار مخفية حقيقية (مضمونة)
    """الشريط السفلي الثابت للروابط المهمة. كل زر يضغط زراً حقيقياً مخفياً (PG_xxx) فيفتح الصفحة المطلوبة."""
    pages = [("assistant",), ("services",), ("support",), ("faq",), ("access",)]
    with st.container(key="pg_hidden"):  # أزرار حقيقية لا تُرى؛ الشريط السفلي والشخصيتان يضغطانها (الاسم PG_xxx هو المعرّف)
        st.button("PG_home", key="qp_home", on_click=close_page)
        for (pg,) in pages:
            st.button(f"PG_{pg}", key=f"qp_{pg}", on_click=open_page, args=(pg,))
        for key, _, _, word in _TAB_LINKS:
            st.button(f"PG_{key}", key=f"qp_{key}", on_click=open_page, args=("tab:" + word,))
        for key, word in _EXTRA_TABS:
            st.button(f"PG_{key}", key=f"qp_{key}", on_click=open_page, args=("tab:" + word,))
    with st.container(key="dock"):
        dock_buttons(_DOCK_ITEMS, active=_dock_active())


_NUM_HTML = """<!doctype html><html dir="rtl" lang="ar"><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;font-family:'IBM Plex Sans Arabic',Tahoma,sans-serif;color:__T__;background:transparent}
.hd{display:flex;align-items:center;gap:10px;margin:2px 4px 10px;font-size:.9rem;letter-spacing:.5px;color:__T__}
.dot{width:9px;height:9px;border-radius:50%;background:__A__;animation:p 1.6s infinite}
@keyframes p{0%{box-shadow:0 0 0 0 __A__aa}70%{box-shadow:0 0 0 10px __A__00}100%{box-shadow:0 0 0 0 __A__00}}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.c{position:relative;overflow:hidden;border-radius:18px;padding:14px 14px 16px;border:1px solid __A__66;
 background:linear-gradient(160deg,__A__18,__B__10);box-shadow:inset 0 0 24px __A__10,0 0 18px __A__18}
.c:before{content:"";position:absolute;left:0;right:0;top:-40%;height:40%;background:linear-gradient(180deg,transparent,__A__22,transparent);
 animation:sc 4.5s linear infinite}@keyframes sc{to{top:140%}}
.c .l{font-size:.78rem;opacity:.85;margin-bottom:4px}.c .v{font-size:2rem;font-weight:800;color:__A__;text-shadow:0 0 14px __A__77;direction:ltr;text-align:right}
.c .v small{font-size:.9rem;opacity:.85;margin-right:4px;color:__T__}
.bar{height:5px;border-radius:99px;background:__T__22;margin-top:10px;overflow:hidden}
.bar i{display:block;height:100%;width:0;border-radius:99px;background:linear-gradient(90deg,__A__,__B__);transition:width 1.4s cubic-bezier(.2,.8,.2,1)}
.ft{margin:8px 4px 0;font-size:.75rem;opacity:.7}</style>
<div class="hd"><span class="dot"></span><b>مؤشرات المشاريع المعتمدة — مباشر</b></div>
<div class="g" id="g"></div><div class="ft">__NOTE__</div>
<script>
var D=__DATA__;var g=document.getElementById('g');
D.forEach(function(x,i){var c=document.createElement('div');c.className='c';
 c.innerHTML='<div class="l">'+x.ic+' '+x.l+'</div><div class="v"><span data-v="'+x.v+'" data-d="'+x.d+'">0</span><small>'+x.u+'</small></div><div class="bar"><i data-p="'+x.p+'"></i></div>';
 g.appendChild(c);});
function fmt(n,d){return n.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});}
document.querySelectorAll('[data-v]').forEach(function(e){var t=parseFloat(e.dataset.v),d=parseInt(e.dataset.d),s=null;
 if(isNaN(t)){e.textContent='—';return;}
 function st(ts){if(!s)s=ts;var k=Math.min((ts-s)/1300,1);e.textContent=fmt(t*(1-Math.pow(1-k,3)),d);if(k<1)requestAnimationFrame(st);}requestAnimationFrame(st);});
setTimeout(function(){document.querySelectorAll('[data-p]').forEach(function(b){b.style.width=Math.max(0,Math.min(100,parseFloat(b.dataset.p)||0))+'%';});},120);
</script></html>"""


def _tech_numbers() -> None:  # شريط إنجازات تقني متحرّك لصفحة المشاريع فقط (أرقام مجمّعة من المشاريع المعتمدة
    """شريط إنجازات تقني متحرّك لصفحة المشاريع فقط (أرقام مجمّعة من المشاريع المعتمدة)."""
    projs = [p for p in load_projects() if p.get("approval") in (None, "معتمد") and p.get("status") != "مقترح"]
    total = len(projs)
    done_p = sum(1 for p in projs if p.get("status") == "منفّذ")
    prog = sum(1 for p in projs if p.get("status") == "قيد التنفيذ")
    dists = len({p.get("district") for p in projs if p.get("district")})
    budget = sum(float(p.get("budget") or 0) for p in projs) / 1e6
    scores = [sc for sc, _ in (project_formula(p) for p in projs) if sc is not None]
    avg_sc = sum(scores) / len(scores) if scores else None
    stars = [e["stars"] for e in load_feedback() if e.get("stars")]
    sat = sum(stars) / len(stars) if stars else None
    items = [
        {"ic": "🏗️", "l": "مشروع معتمد", "v": total, "d": 0, "u": "", "p": 100 if total else 0},
        {"ic": "✅", "l": "مشروع منفّذ", "v": done_p, "d": 0, "u": "", "p": done_p / total * 100 if total else 0},
        {"ic": "🚧", "l": "قيد التنفيذ", "v": prog, "d": 0, "u": "", "p": prog / total * 100 if total else 0},
        {"ic": "📍", "l": "حيّاً مستفيداً", "v": dists, "d": 0, "u": f"/{len(DISTRICTS)}", "p": dists / max(len(DISTRICTS), 1) * 100},
        {"ic": "💰", "l": "إجمالي الميزانيات", "v": round(budget, 1), "d": 1, "u": "م.ر.س", "p": 100 if budget else 0},
        {"ic": "🎯", "l": "متوسط نسبة النجاح", "v": round(avg_sc, 1) if avg_sc is not None else "NaN", "d": 1, "u": "%", "p": avg_sc or 0},
        {"ic": "⭐", "l": "رضا المستخدمين", "v": round(sat, 2) if sat is not None else "NaN", "d": 2, "u": "/5", "p": (sat or 0) / 5 * 100},
    ]
    a, b, t = theme_palette()
    note = "تشمل المشاريع التجريبية الموسومة حتى يحذفها المدير." if any(p.get("demo") for p in projs) else "أرقام مجمّعة من المشاريع المعتمدة."
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    _frame(_NUM_HTML.replace("__A__", a).replace("__B__", b).replace("__T__", t).replace("__NOTE__", note)
           .replace("__DATA__", data), 250)


# ======================================================
# رأيك يهمنا: نموذج + متابعة + لوحة تحليل للمدير
# ======================================================
_FB_TOPICS = ["سهولة الاستخدام", "سرعة الأداء", "دقة المعلومات", "المساعد الذكي والصوت", "التصميم والمظهر",
              "الخصوصية والأمان", "التدريب والدعم", "المشاريع", "تتبّع المعاملات", "أخرى"]


_ROLE_AR = {"guest": "زائر", "employee": "موظف", "manager": "مدير إدارة", "reviewer": "مراجع", "admin": "مدير"}


def _submit_feedback(ctx: AuthContext, stars: int, nps, topics: list, comment: str, anon: bool, source: str) -> str:  # يحفظ الرأي ويُرجع رقمه
    """يحفظ الرأي ويُرجع رقمه. الاسم لا يُحفظ إن اختار المستخدم «بدون اسم»."""
    ref = save_feedback({"stars": stars, "nps": nps, "topics": topics, "comment": comment,
                         "role": ctx.role, "by": "" if anon or not ctx.logged_in else ctx.username, "source": source})
    audit("feedback_submitted", ctx, ref=ref, stars=stars)
    return ref


def _fb_form(ctx: AuthContext, df_all=None) -> None:  # نموذج تقييم المنصة (نجوم وملاحظات)
    st.caption("رأيك يصل للمدير مباشرة ويُستخدم لتحسين المنصة. لا تكتب معلومات سرية أو شخصية في التعليق.")
    if st.session_state.get("fbp_append"):  # نص الصوت يُدمج قبل إنشاء حقل التعليق (قيد Streamlit)
        st.session_state["fbp_comment"] = (st.session_state.get("fbp_comment", "") + " " + st.session_state.pop("fbp_append")).strip()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**كيف تقيّم تجربتك؟**")
        pick = st.feedback("stars", key="fbp_stars")
    nps = c2.slider("هل توصي أحداً بالمنصة؟ (0–10)", 0, 10, 8, key="fbp_nps")
    topics = st.multiselect("ما الذي تعلّق عليه؟", _FB_TOPICS, key="fbp_topics")
    comment = st.text_area("تعليقك أو فكرتك أو ما أزعجك", key="fbp_comment", height=110, max_chars=1500)
    if st.audio_input("🎙️ أو سجّل رأيك صوتياً (اختياري)", key="fbp_audio") is not None:
        aud = st.session_state["fbp_audio"]
        if st.button("✍️ حوّل الصوت إلى نص", key="fbp_stt"):
            res = transcribe_audio(aud.getvalue(), "feedback.wav")
            if res.get("text"):
                st.session_state["fbp_append"] = res["text"]
                st.rerun()
            else:
                st.warning(res.get("error") or "لم يُسمع كلام واضح، أعد المحاولة.")
    anon = st.checkbox("إرسال بدون اسمي", value=not ctx.logged_in, key="fbp_anon", disabled=not ctx.logged_in)
    if st.button("📤 أرسل رأيي", key="fbp_send", type="primary", width="stretch"):
        if pick is None and len(comment.strip()) < 5:
            st.error("اختر تقييماً بالنجوم أو اكتب تعليقاً قصيراً.")
        else:
            entry = {"stars": (pick or 0) + (1 if pick is not None else 0), "nps": nps, "topics": topics, "comment": comment}
            ref = _submit_feedback(ctx, entry["stars"], nps, topics, comment, anon or not ctx.logged_in, "page")
            st.session_state["fb_last"] = {"ref": ref, "reply": feedback_reply(entry)}
            st.rerun()
    last = st.session_state.get("fb_last")
    if last:
        card(f"✅ وصل رأيك، رقمه <b>{html.escape(last['ref'])}</b> (احفظه للمتابعة).<br>{html.escape(last['reply'])}", "ai")
        _speak_once(last["reply"], f"fb:{last['ref']}")


def _fb_follow() -> None:  # متابعة رأي برقمه المرجعي
    ref = st.text_input("تابع رأيك برقمه المرجعي", placeholder="FB-2026-0001", key="fb_ref")
    if ref:
        it = find_feedback(ref)
        if not it:
            st.info("لم نجد رأياً بهذا الرقم.")
        else:
            st.success(f"الحالة: **{it.get('status', 'جديد')}**" + (f" — ملاحظة الإدارة: {it['admin_note']}" if it.get("admin_note") else ""))


def _fb_admin(ctx: AuthContext) -> None:  # لوحة تحليل الآراء للمدير بالذكاء الاصطناعي
    items = load_feedback()
    if not items:
        st.info("لا توجد آراء بعد.")
        return
    df = pd.DataFrame(items)
    df["stars"] = pd.to_numeric(df.get("stars"), errors="coerce").fillna(0).astype(int)
    df["nps"] = pd.to_numeric(df.get("nps"), errors="coerce")
    rated = df[df["stars"] > 0]
    nps = df["nps"].dropna()
    nps_score = round(((nps >= 9).mean() - (nps <= 6).mean()) * 100) if len(nps) else None
    mood = df.apply(lambda r: feedback_mood(int(r["stars"]), None if pd.isna(r["nps"]) else r["nps"]), axis=1)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("عدد الآراء", len(df))
    k2.metric("متوسط التقييم", f"{rated['stars'].mean():.2f}/5" if len(rated) else "—")
    k3.metric("مؤشر التوصية NPS", f"{nps_score}" if nps_score is not None else "—")
    k4.metric("إيجابي", f"{(mood == 'إيجابي').mean() * 100:.0f}%")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### توزيع المشاعر")
        st.bar_chart(mood.value_counts())
    with c2:
        st.markdown("##### المحاور الأكثر ذكراً")
        tc = pd.Series([t for ts in df.get("topics", []) if isinstance(ts, list) for t in ts]).value_counts()
        st.bar_chart(tc) if len(tc) else st.caption("لا توجد محاور.")
    st.markdown("##### حسب الدور")
    st.dataframe(df.groupby(df["role"].map(_ROLE_AR).fillna("زائر"))["stars"].agg(["count", "mean"]).round(2)
                 .rename(columns={"count": "العدد", "mean": "متوسط النجوم"}), width="stretch")
    if st.button("🤖 حلّل الآراء بالذكاء الاصطناعي", key="fb_ai", width="stretch"):
        with st.spinner("يحلّل..."):
            st.session_state["fb_ai_res"] = analyze_feedback(items)
    res = st.session_state.get("fb_ai_res")
    if res:
        if res.get("error"):
            st.warning(res["error"])
        else:
            card(f"<b>الخلاصة:</b> {html.escape(str(res.get('overall', '')))}", "ai")
            for title, key in (("👏 الثناء", "praise"), ("⚠️ الشكاوى", "complaints"), ("💡 الاقتراحات", "suggestions")):
                if res.get(key):
                    st.markdown(f"**{title}**")
                    for x in res[key]:
                        st.markdown(f"- {x}")
            if res.get("actions"):
                st.markdown("**🎯 إجراءات مقترحة**")
                st.dataframe(pd.DataFrame(res["actions"]), hide_index=True, width="stretch")
    st.markdown("##### 📋 كل الآراء ومتابعتها")
    show = df[[c for c in ("ref", "at", "role", "stars", "nps", "comment", "status", "admin_note") if c in df.columns]]
    st.dataframe(show, hide_index=True, width="stretch")
    c1, c2, c3 = st.columns([2, 2, 3])
    ref = c1.selectbox("الرأي", [i["ref"] for i in items], key="fb_pick")
    stt = c2.selectbox("الحالة", ["جديد", "قيد الدراسة", "نُفّذ", "مغلق"], key="fb_status")
    note = c3.text_input("ملاحظة للمستخدم", key="fb_note")
    if st.button("💾 حفظ الحالة", key="fb_save"):
        update_feedback(ref, stt, note)
        audit("feedback_status", ctx, ref=ref, status=stt)
        st.rerun()
    export_bar("feedback", "تقرير آراء المستخدمين", ctx, df=show, classification="داخلي")


def render_feedback(ctx: AuthContext, df_all: pd.DataFrame = None) -> None:  # صفحة «رأيك يهمنا»
    st.subheader("💬 رأيك يهمنا — نسمعك")
    st.markdown("**زائر أو موظف أو مدير، رأيك يصنع الفرق.** قيّم، واكتب فكرتك، أو سجّلها بصوتك.")
    tabs = ["⭐ قيّم المنصة", "🔎 متابعة رأيي"] + (["📊 لوحة الانطباعات (مدير)"] if is_admin(ctx) else [])
    ts = st.tabs(tabs)
    with ts[0]:
        _fb_form(ctx, df_all)
    with ts[1]:
        _fb_follow()
    if is_admin(ctx):
        with ts[2]:
            _fb_admin(ctx)


# ======================================================
# المساعد العائم (أزرار سريعة + رأيك يهمنا) — يظهر في كل الصفحات
# ======================================================
_FAB_EXTRA = ("أنت الآن في نافذة المساعد العائم: أجب في جملتين إلى أربع، بلهجة سعودية بيضاء محترمة، "
              "وإن مازحك المستخدم فمازحه بخفة نظيفة ثم ساعده. إن سأل عن شيء يخص صفحة معيّنة فوجّهه لاسم التبويب. "
              "ممنوع أن تذكر تاريخ تدريبك أو أنك نموذج أو «مدرَّب حتى أكتوبر 2023»؛ ولا تعرّف بنفسك إلا إن سُئلت.")


def _fab_ask(q: str) -> None:  # يحفظ سؤال زر سريع ليُجاب في المساعد العائم
    st.session_state["fab_q"] = q


def render_fab(ctx: AuthContext, df_all: pd.DataFrame) -> None:  # المساعد العائم والشخصيتان توني وسعيدان في كل الصفحات
    companions(ctx.role if ctx.logged_in else "guest")  # توني وسعيدان يتحاوران فوق الزرين
    with st.container(key="fab_assistant"):
        with st.popover("💬 مساعدك"):
            st.button("🗖 افتح المساعد كاملاً", key="fab_open_full", on_click=open_page, args=("assistant",), width="stretch")
            t_chat, t_fb = st.tabs(["💬 اسألني", "⭐ رأيك يهمنا"])
            with t_chat:
                hello = "هلا والله! أنا مساعدك الرقمي، اختر من الأزرار أو اكتب سؤالك."
                st.markdown(f'<div class="fab-hello">{hello}</div>', unsafe_allow_html=True)
                role_k = "admin" if is_admin(ctx) else ("employee" if ctx.logged_in else "guest")
                for i, q in enumerate(_GUIDE_Q[role_k]):  # أسئلة تدريب سريعة حسب دورك
                    st.button("❓ " + q, key=f"chip{i}", on_click=_fab_ask, args=(q,), width="stretch")
                with st.form("fab_form", clear_on_submit=True):
                    typed = st.text_input("اكتب سؤالك", key="fab_text", label_visibility="collapsed", placeholder="اكتب سؤالك هنا…")
                    sent = st.form_submit_button("إرسال", width="stretch")
                q = st.session_state.pop("fab_q", None) or (typed.strip() if sent and typed else None)
                fa = st.audio_input("🎙️ أو تحدّث", key="fab_audio")
                if fa is not None and not q:
                    raw = fa.getvalue()
                    sig = hashlib.md5(raw).hexdigest()
                    if st.session_state.get("fab_audio_sig") != sig:  # لا نعالج نفس التسجيل مرتين
                        st.session_state["fab_audio_sig"] = sig
                        q = transcribe_audio(raw, "fab.wav").get("text") or None
                hist = st.session_state.setdefault("fab_hist", [])
                for m in hist[-4:]:  # المحادثة السابقة أولاً
                    st.markdown(("**أنت:** " if m["role"] == "user" else "**المساعد:** ") + m["content"])
                if q:  # الرد الجديد يظهر كلمة كلمة (أسرع إحساساً) ثم يُنطق
                    st.markdown("**أنت:** " + q)
                    with st.chat_message("assistant"):
                        ans = st.write_stream(ask_assistant_stream(
                            q, hist, ctx, df_all, extra_system=_FAB_EXTRA + " " + _GUIDE_EXTRA))
                    ans = ans if isinstance(ans, str) else "".join(map(str, ans))
                    hist += [{"role": "user", "content": q}, {"role": "assistant", "content": ans}]
                    del hist[:-10]
                    speak_now(ans)
            with t_fb:
                st.caption("تقييم سريع، وللتفاصيل افتح تبويب «رأيك يهمنا».")
                pick = st.feedback("stars", key="fab_stars")
                txt = st.text_input("كلمة تحب تقولها؟", key="fab_fbtxt", max_chars=300)
                if st.button("إرسال", key="fab_fbsend", width="stretch"):
                    if pick is None and len(txt.strip()) < 5:
                        st.error("اختر نجوماً أو اكتب كلمة.")
                    else:
                        ref = _submit_feedback(ctx, (pick + 1) if pick is not None else 0, None, [], txt, not ctx.logged_in, "fab")
                        st.success(f"شكراً لك! رقم رأيك {ref}")


# ======================================================
# الأمان والخصوصية (صياغة رسمية؛ كل بند يطابق ما هو مطبّق فعلاً في المنصة)
# ======================================================
def render_privacy(ctx: AuthContext) -> None:  # صفحة الأمان والخصوصية وحقوق المستخدم
    st.subheader("🔐 الأمان والخصوصية")
    card("<b>منصة تجريبية (Pilot)</b> لأمانة محافظة جدة لأغراض التقييم. هذه الصفحة تصف ما تطبّقه المنصة فعلياً اليوم، "
         "وتُراجَع صياغتها النهائية مع الجهات المختصة قبل أي إطلاق رسمي.", "banner")
    t1, t2, t3, t4 = st.tabs(["🛡️ ضوابط الأمان", "📜 سياسة الخصوصية", "🙋 حقوقك وطلباتك", "📑 الشروط والتصنيف"])
    with t1:
        rows = [("فلترة الصلاحيات في الخادم", "البيانات السرية لا تصل للواجهة ولا للمساعد الذكي إلا لمن يحق له (زائر: عام، موظف: عام وسري، مدير: الكل)."),
                ("حماية كلمات المرور", "تُخزَّن مشفّرة بخوارزمية PBKDF2 مع ملح، ولا تُحفظ نصاً صريحاً."),
                ("سجل تدقيق", "الدخول والخروج وأسئلة المساعد والتصدير وتغيير الحالات تُسجَّل للمراجعة."),
                ("انتهاء الجلسة", "تنتهي الجلسة تلقائياً بعد فترة خمول يحددها المدير."),
                ("حماية الخصوصية في النتائج", "الخلايا الصغيرة (أقل من 10) تُخفى في «البيانات المفتوحة»، والاستعلام عن معاملة غير عامة يعطي ردّاً موحّداً لا يكشف وجودها."),
                ("نسخ احتياطي", "نسخ تلقائي دوري محلي، ويوصى بحفظ نسخة إضافية خارج الجهاز."),
                ("هوية المطوّر", "لا تظهر بيانات شخصية للمطوّر في الواجهة؛ تظهر العلامة فقط.")]
        for a, b in rows:
            st.markdown(f"**✔ {a}:** {b}")
    with t2:
        st.markdown("""**ما الذي نجمعه؟** رقم المعاملة وبياناتها التشغيلية، وما تكتبه في الآراء والبلاغات، واسم المستخدم لمن سجّل دخوله (ويمكن إرسال الرأي بلا اسم).

**كيف نستخدمه؟** لتتبّع المعاملات وتحسين الخدمة وإعداد التقارير المجمّعة.

**الذكاء الاصطناعي:** عند استخدام المساعد أو الصوت أو تحليل الصور تُرسَل النصوص أو الملفات اللازمة إلى مزوّد الخدمة (OpenAI) لمعالجتها، بعد تطبيق فلترة الصلاحيات. لا تكتب معلومات سرية أو شخصية غير لازمة.

**أين تُحفظ البيانات؟** محلياً على خادم المنصة (قاعدة بيانات وملفات)، ولا تُباع ولا تُشارك لأغراض تسويقية.

**مدة الحفظ:** تحدَّد في الإطلاق الرسمي؛ في النسخة التجريبية يحذف المدير ما ينتهي الغرض منه.""")
    with t3:
        st.markdown("يمكنك طلب الاطلاع على بياناتك أو تصحيحها أو حذفها، أو الإبلاغ عن مخاوف أمنية. يصلك رقم مرجعي للمتابعة.")
        with st.form("prv_form", clear_on_submit=True):
            kind = st.selectbox("نوع الطلب", ["اطلاع على بياناتي", "تصحيح بياناتي", "حذف بياناتي", "بلاغ أمني أو تسريب"])
            txt = st.text_area("تفاصيل الطلب", max_chars=1500)
            contact = st.text_input("وسيلة تواصل للرد (اختياري)")
            if st.form_submit_button("📤 إرسال الطلب", width="stretch"):
                if len(txt.strip()) < 10:
                    st.error("اكتب تفاصيل أوضح.")
                else:
                    ref = save_ticket("خصوصية", kind, txt, ctx.username or "زائر", ctx.role, contact)
                    audit("privacy_request", ctx, ref=ref, kind=kind)
                    st.success(f"وصل طلبك، رقمه **{ref}**.")
        ref = st.text_input("تابع طلبك برقمه", placeholder="PRV-2026-0001", key="prv_ref")
        if ref:
            t = find_ticket(ref)
            st.info(f"الحالة: {t['status']}" + (f" — {t['reply']}" if t and t.get("reply") else "") if t else "لا يوجد طلب بهذا الرقم.")
    with t4:
        st.markdown("""**التصنيف:** عام (للجميع) • سري (للموظفين) • الأعلى (للمدير).

**شروط الاستخدام:** الاستخدام لأغراض التقييم والخدمة فقط، وعدم محاولة تجاوز الصلاحيات، وعدم إدخال بيانات غير صحيحة عمداً.

**مستوى الخدمة:** منصة تجريبية؛ تُحدَّد اتفاقية مستوى الخدمة (SLA) عند الإطلاق الرسمي.""")
    if is_admin(ctx):
        with st.expander("📥 طلبات الخصوصية والدعم الواردة (مدير)"):
            from data_layer import load_tickets, update_ticket
            tk = load_tickets()
            if tk:
                st.dataframe(pd.DataFrame(tk), hide_index=True, width="stretch")
                c1, c2, c3 = st.columns([2, 2, 3])
                r = c1.selectbox("التذكرة", [t["ref"] for t in tk], key="tk_pick")
                s2 = c2.selectbox("الحالة", ["جديدة", "قيد المعالجة", "تمت", "مغلقة"], key="tk_stat")
                rp = c3.text_input("الرد", key="tk_reply")
                if st.button("💾 حفظ", key="tk_save"):
                    update_ticket(r, s2, rp)
                    st.rerun()
            else:
                st.caption("لا توجد طلبات.")


# ======================================================
# مركز التدريب والتوجيه: المساعد يرشدك لاستخدام المنصة (أسئلة سريعة + نص + صوت) — بلا اختبارات
# ======================================================
_GUIDE_Q = {  # أسئلة سريعة حسب الدور (يضغطها المستخدم فيجيب المساعد ويوجّهه خطوة بخطوة)
    "guest": ["كيف أتابع معاملتي؟", "وين أشوف مشاريع الأمانة؟", "كيف أتكلم مع المساعد بصوتي؟",
              "كيف أقدّم رأيي أو شكوى؟", "كيف تحمون بياناتي؟"],
    "employee": ["كيف أسجّل دخولي وإيش اللي أشوفه؟", "كيف أدخل معاملة جديدة بصورة؟", "كيف أقترح مشروعاً؟",
                 "كيف أكتب خطاباً رسمياً؟", "كيف أرفع تقرير ميداني؟"],
    "admin": ["كيف أقرأ لوحة التحليلات؟", "كيف أعتمد مقترح مشروع وأحسب تكلفته؟", "كيف أحلّل آراء المستخدمين؟",
              "كيف أصدر التقرير التنفيذي الشهري؟", "كيف آخذ نسخة احتياطية وأراجع التدقيق؟"],
}


_ROLE_TITLE = {"guest": "مسار الزائر", "employee": "مسار الموظف", "admin": "مسار المدير"}


_GUIDE_EXTRA = ("وضع «المرشد التدريبي»: وظيفتك توجيه المستخدم لاستخدام المنصة. أجب بخطوات قصيرة مرقّمة (3 إلى 5) "
                "تذكر فيها اسم التبويب أو الزر بالضبط، بلهجة سعودية بيضاء ودودة، ثم اسأله إن كان يحتاج شرحاً لخطوة. "
                "تبويبات المنصة: تتبّع معاملتك، مشاريع الأمانة، بيانات مفتوحة، التدريب والدعم، رأيك يهمنا، الأمان والخصوصية، "
                "المساعد الذكي وصانع الخطابات، وللمدير: لوحة التحليلات، إدخال البيانات، العمليات، الفرق الميدانية، الخطابات الرسمية، "
                "التحليل التنبؤي (داخل تبويب الفرق الميدانية)، جودة البيانات، النظام والنسخ. ممنوع ذكر تاريخ تدريبك أو أنك نموذج.")


def _guide_ask(ctx: AuthContext, df_all: pd.DataFrame, q: str) -> None:  # يرسل سؤال المرشد التدريبي للمساعد
    hist = st.session_state.setdefault("guide_hist", [])
    with st.spinner("لحظة…"):
        ans = ask_assistant(q, hist, ctx, df_all, extra_system=_GUIDE_EXTRA)
    hist += [{"role": "user", "content": q}, {"role": "assistant", "content": ans}]
    del hist[:-12]
    st.session_state["guide_last"] = (q, ans)


def _render_guide(ctx: AuthContext, df_all: pd.DataFrame, role: str) -> None:  # واجهة المرشد التدريبي حسب الدور
    st.markdown(f"##### 🧭 {_ROLE_TITLE[role]} — اسأل المرشد، يوجّهك خطوة بخطوة")
    st.caption("اضغط سؤالاً سريعاً، أو اكتب، أو تحدّث بصوتك. المرشد يجيبك نصاً وصوتاً ويقول لك أي تبويب تفتح.")
    chosen = None
    for q in _GUIDE_Q[role]:  # الأسئلة السريعة
        if st.button("❓ " + q, key=f"gq:{role}:{q}", width="stretch"):
            chosen = q
    c1, c2 = st.columns([3, 2])
    with c1:
        with st.form("guide_form", clear_on_submit=True):
            typed = st.text_input("أو اكتب سؤالك", key="guide_text", placeholder="مثال: كيف أغيّر شكل المنصة؟")
            if st.form_submit_button("إرسال", width="stretch") and typed.strip():
                chosen = typed.strip()
    with c2:
        aud = st.audio_input("🎙️ أو تحدّث", key="guide_audio")
        if aud is not None:
            raw = aud.getvalue()
            sig = hashlib.md5(raw).hexdigest()
            if st.session_state.get("guide_audio_sig") != sig:  # لا نعالج نفس التسجيل مرتين
                st.session_state["guide_audio_sig"] = sig
                res = transcribe_audio(raw, "guide.wav")
                if res.get("text"):
                    chosen = res["text"]
                else:
                    st.warning(res.get("error") or "ما سمعتك بوضوح، أعد المحاولة.")
    if chosen:
        _guide_ask(ctx, df_all, chosen)
    last = st.session_state.get("guide_last")
    if last:
        st.markdown(f"**🧑 {last[0]}**")
        card(html.escape(last[1]).replace("\n", "<br>"), "ai")
        _speak_once(last[1], f"guide:{hashlib.md5((last[0] + last[1]).encode()).hexdigest()[:10]}")
    with st.expander("📚 دليل سريع مكتوب لهذا المسار"):
        for line in _TOUR.get(role, _TOUR["guest"]):
            st.markdown(f"- {line}")


def render_training(ctx: AuthContext, df_all: pd.DataFrame) -> None:  # مركز التدريب والدعم: مرشد صوتي/نصي حسب الدور، ثم الأسئلة الشائعة والبلاغات، ثم
    """مركز التدريب والدعم: مرشد صوتي/نصي حسب الدور، ثم الأسئلة الشائعة والبلاغات، ثم تذاكر الدعم."""
    st.subheader("🎓 التدريب والدعم")
    t1, t2, t3 = st.tabs(["🧭 المرشد (تدريب وتوجيه)", "❓ الأسئلة والبلاغات", "🛟 تذكرة دعم"])
    with t1:
        roles = ["guest"] + (["employee"] if ctx.logged_in else []) + (["admin"] if is_admin(ctx) else [])
        role = st.radio("المسار", roles, format_func=lambda k: _ROLE_TITLE[k], horizontal=True,
                        index=len(roles) - 1, key="trk_pick") if len(roles) > 1 else "guest"
        _render_guide(ctx, df_all, role)
    with t2:
        render_help(ctx)
    with t3:
        with st.form("sup_form", clear_on_submit=True):
            sub = st.text_input("الموضوع", max_chars=120)
            txt = st.text_area("المشكلة أو سؤالك", max_chars=1500)
            contact = st.text_input("وسيلة تواصل (اختياري)")
            if st.form_submit_button("📤 افتح تذكرة", width="stretch"):
                if len(txt.strip()) < 10 or not sub.strip():
                    st.error("اكتب الموضوع ووصفاً أوضح.")
                else:
                    ref = save_ticket("دعم", sub, txt, ctx.username or "زائر", ctx.role, contact)
                    audit("support_ticket", ctx, ref=ref)
                    st.success(f"فُتحت تذكرتك رقم **{ref}**.")
        ref = st.text_input("تابع تذكرتك", placeholder="SUP-2026-0001", key="sup_ref")
        if ref:
            t = find_ticket(ref)
            st.info(f"الحالة: {t['status']}" + (f" — {t['reply']}" if t and t.get("reply") else "") if t else "لا توجد تذكرة بهذا الرقم.")


