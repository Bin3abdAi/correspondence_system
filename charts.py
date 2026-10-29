"""الرسوم البيانية (Plotly) — تصميم تقني مبسّط وسهل القراءة.

وظيفة هذا الملف: ثلاث دوال فقط تُرجع رسماً جاهزاً، وviews.py هو من يعرضها ويشرحها:
  gauge(ind)              ← حلقة الإنجاز: الحلقة الخارجية = المعدل الحالي، الداخلية = المستهدف
  trend_chart(weekly, fc) ← اتجاه الإنجاز الأسبوعي + المتوسط المتحرك + التوقع ونطاق عدم اليقين
  dept_chart(dept)        ← أداء الأقسام مقابل المستهدف
"""
import numpy as np                 # حسابات رقمية (الانحراف المعياري لنطاق التوقع)
import plotly.graph_objects as go  # مكتبة الرسم
from plotly.subplots import make_subplots  # لتقسيم الرسم إلى لوحتين (المعدل فوق، الحجم تحت)

from config import TARGET_COMPLETION_RATE  # المستهدف (%)
from ui import PALETTE, chart_colors, style_fig  # ألوان وهوية موحّدة (ونصوص الرسم تتبع النمط: قاتمة على الفاتح وفاتحة على الداكن)

_GREEN, _AMBER, _RED = "#10b981", "#f59e0b", "#f43f5e"  # إيجابي / متوسط / سلبي
_CYAN, _GOLD, _VIOLET = PALETTE[0], PALETTE[1], PALETTE[2]
_TRACK = "rgba(100,116,139,.22)"  # لون الجزء الفارغ من الحلقة (يُرى على الفاتح والداكن)


def _status_color(rate: float, target: float) -> str:  # أخضر إن بلغ المستهدف، أصفر إن تجاوز نصفه، وإلا أحمر
    """أخضر إن بلغ المستهدف، أصفر إن تجاوز نصفه، وإلا أحمر."""
    return _GREEN if rate >= target else _AMBER if rate >= target / 2 else _RED


def gauge(ind):  # حلقتان متداخلتان: الخارجية معدل الإنجاز الحالي، والداخلية المستهدف — الفرق بين
    """حلقتان متداخلتان: الخارجية معدل الإنجاز الحالي، والداخلية المستهدف — الفرق بينهما يُقرأ بلمحة."""
    target = TARGET_COMPLETION_RATE
    C = chart_colors()
    rate = max(0.0, min(100.0, float(ind.rate)))
    color = _status_color(rate, target)
    fig = go.Figure()
    fig.add_trace(go.Pie(  # الحلقة الخارجية = الواقع
        values=[rate, 100 - rate], labels=["منجز", "متبقٍ"], hole=0.80, sort=False, direction="clockwise",
        marker=dict(colors=[color, _TRACK], line=dict(width=0)), textinfo="none",
        hovertemplate="%{label}: %{value:.1f}%<extra>المعدل الحالي</extra>",
        domain=dict(x=[0, 1], y=[0, 1]), showlegend=False))
    fig.add_trace(go.Pie(  # الحلقة الداخلية = المستهدف
        values=[target, 100 - target], labels=["المستهدف", ""], hole=0.84, sort=False, direction="clockwise",
        marker=dict(colors=[_GOLD, "rgba(0,0,0,0)"], line=dict(width=0)), textinfo="none",
        hovertemplate="المستهدف: %{value:.0f}%<extra></extra>",
        domain=dict(x=[0.14, 0.86], y=[0.14, 0.86]), showlegend=False, opacity=0.9))
    arrow = "" if ind.delta is None else (f"▲ {ind.delta:+.1f} نقطة" if ind.delta >= 0 else f"▼ {ind.delta:+.1f} نقطة")
    gap = rate - target
    fig.add_annotation(text=f"<b>{rate:.1f}%</b>", x=0.5, y=0.58, showarrow=False,
                       font=dict(size=42, color=C["strong"]))
    fig.add_annotation(text="معدل الإنجاز", x=0.5, y=0.43, showarrow=False, font=dict(size=14, color=C["muted"]))
    fig.add_annotation(text=f"<span style='color:{color}'>{arrow}</span>" if arrow else "",
                       x=0.5, y=0.33, showarrow=False, font=dict(size=15, color=C["strong"]))
    fig.add_annotation(text=f"{'فوق' if gap >= 0 else 'دون'} المستهدف بـ {abs(gap):.1f} نقطة", x=0.5, y=0.22,
                       showarrow=False, font=dict(size=12, color=C["muted"]))
    style_fig(fig)  # الهوية أولاً ثم تفاصيل هذا الرسم
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def trend_chart(weekly, fc=None):  # لوحتان: العلوية معدل الإنجاز الأسبوعي (نقطة خضراء فوق المستهدف وحمراء دونه + ن
    """لوحتان: العلوية معدل الإنجاز الأسبوعي (نقطة خضراء فوق المستهدف وحمراء دونه + نطاقا الأداء + التوقع)،
    والسفلية حجم المعاملات المستلمة. أسهل في القراءة من دمجهما في رسم واحد."""
    target = TARGET_COMPLETION_RATE
    C = chart_colors()
    rates = weekly["rate"].astype(float)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.76, 0.24], vertical_spacing=0.05)
    # ---- ألوان النقاط: أخضر إن بلغ الأسبوع المستهدف، أحمر إن لم يبلغه ----
    dots = [_GREEN if r >= target else _RED for r in rates]
    ys = list(rates)
    if fc is not None and len(fc):
        ys += list(fc["rate"])
    lo, hi = max(0, min(ys + [target]) - 6), min(100, max(ys + [target]) + 6)  # تكبير النطاق لتظهر التغيّرات
    # ---- منطقتا الأداء: فوق المستهدف (خضراء باهتة) ودونه (حمراء باهتة) ----
    fig.add_hrect(y0=target, y1=hi, fillcolor="rgba(16,185,129,.07)", line_width=0, row=1, col=1)
    fig.add_hrect(y0=lo, y1=target, fillcolor="rgba(244,63,94,.06)", line_width=0, row=1, col=1)
    fig.add_trace(go.Scatter(  # خط معدل الإنجاز الأسبوعي
        x=weekly["week"], y=rates, name="معدل الإنجاز الأسبوعي", mode="lines+markers",
        line=dict(color=_CYAN, width=2.4, shape="spline", smoothing=0.45),
        marker=dict(color=dots, size=8, line=dict(color=C["edge"], width=1.4)),
        hovertemplate="%{y:.1f}%<extra>الأسبوعي</extra>"), row=1, col=1)
    ma = rates.rolling(4, min_periods=1).mean()  # متوسط 4 أسابيع يُظهر الاتجاه بلا ضجيج
    fig.add_trace(go.Scatter(x=weekly["week"], y=ma, name="الاتجاه (متوسط 4 أسابيع)", mode="lines",
                             line=dict(color=_GOLD, width=3), hovertemplate="%{y:.1f}%<extra>الاتجاه</extra>"),
                  row=1, col=1)
    fig.add_hline(y=target, line=dict(color=C["muted"], width=1.5, dash="dash"), row=1, col=1,
                  annotation_text=f"المستهدف {target:.0f}%", annotation_position="top left",
                  annotation_font=dict(color=C["strong"], size=12))
    if fc is not None and len(fc):
        spread = float(np.std(rates.tail(8))) or 1.0  # عرض نطاق عدم اليقين
        xs = [weekly["week"].iloc[-1], *fc["week"]]   # نبدأ من آخر نقطة حقيقية ليتصل الخط
        yv = [rates.iloc[-1], *fc["rate"]]
        upper = [min(100, v + spread) for v in yv]
        lower = [max(0, v - spread) for v in yv]
        fig.add_trace(go.Scatter(x=xs + xs[::-1], y=upper + lower[::-1], fill="toself", mode="none",
                                 fillcolor="rgba(139,92,246,.2)", name="نطاق عدم اليقين", hoverinfo="skip"),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=xs, y=yv, name="التوقّع القادم", mode="lines+markers",
                                 line=dict(color=_VIOLET, width=2.6, dash="dot"),
                                 marker=dict(size=8, symbol="diamond"),
                                 hovertemplate="%{y:.1f}%<extra>توقّع</extra>"), row=1, col=1)
    last_x, last_y = weekly["week"].iloc[-1], rates.iloc[-1]
    fig.add_annotation(x=last_x, y=last_y, text=f"آخر أسبوع {last_y:.1f}%", showarrow=True, arrowhead=2,
                       arrowcolor=_CYAN, ax=-40, ay=-45, font=dict(size=12, color=C["strong"]),
                       bgcolor=C["panel"], bordercolor=_CYAN, borderpad=4, row=1, col=1)
    fig.add_trace(go.Bar(  # اللوحة السفلية: حجم المعاملات
        x=weekly["week"], y=weekly["total"], name="حجم المعاملات المستلمة", marker=dict(color="rgba(34,211,238,.45)"),
        hovertemplate="%{y:,} معاملة<extra>الحجم</extra>"), row=2, col=1)
    style_fig(fig)  # الهوية أولاً ثم تفاصيل هذا الرسم
    fig.update_layout(
        height=470, hovermode="x unified", bargap=0.3, margin=dict(l=10, r=10, t=44, b=10),
        legend=dict(orientation="h", y=1.16, x=1, xanchor="right", font=dict(size=12, color=C["text"])))
    fig.update_yaxes(title_text="الإنجاز %", range=[lo, hi], ticksuffix="%", row=1, col=1)
    fig.update_yaxes(title_text="الحجم", row=2, col=1)
    fig.update_xaxes(tickformat="%b %Y", row=2, col=1)
    fig.update_xaxes(rangeselector=dict(  # أزرار تغيير النطاق الزمني
        buttons=[dict(count=2, label="شهران", step="month", stepmode="backward"),
                 dict(count=6, label="6 أشهر", step="month", stepmode="backward"),
                 dict(step="all", label="الكل")],
        bgcolor=C["panel"], activecolor="rgba(224,184,76,.95)", font=dict(color=C["strong"], size=12),
        x=0, y=1.14), row=1, col=1)
    return fig


def dept_chart(dept):  # مخطط «مصاصة» متباعد: خط ذهبي عمودي = المستهدف، وكل قسم نقطة على مسافتها منه؛ ح
    """مخطط «مصاصة» متباعد: خط ذهبي عمودي = المستهدف، وكل قسم نقطة على مسافتها منه؛ حجم النقطة = عدد معاملات القسم.
    الأضعف في الأعلى. النطاق مكبَّر حول المستهدف حتى تظهر الفروق الصغيرة."""
    target = TARGET_COMPLETION_RATE
    C = chart_colors()
    d = dept.sort_values("rate", ascending=True)  # الأضعف أولاً (يظهر في الأعلى بعد عكس المحور)
    names = [str(i) for i in d.index]
    rates = d["rate"].astype(float).tolist()
    totals = d["total"].astype(float)
    sizes = (14 + 26 * np.sqrt(totals / totals.max())).tolist()  # حجم النقطة يتناسب مع الحجم
    colors = [_status_color(r, target) for r in rates]
    diffs = [r - target for r in rates]
    fig = go.Figure()
    sx, sy = [], []  # الخطوط الواصلة بين المستهدف والنقطة (ساق المصاصة)
    for n, r in zip(names, rates):
        sx += [target, r, None]
        sy += [n, n, None]
    fig.add_trace(go.Scatter(x=sx, y=sy, mode="lines", line=dict(color="rgba(100,116,139,.6)", width=3),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=rates, y=names, mode="markers+text", marker=dict(color=colors, size=sizes, line=dict(color=C["edge"], width=2)),
        text=[f"{r:.1f}%  ({df_:+.1f})" for r, df_ in zip(rates, diffs)], textposition="middle right",
        textfont=dict(color=C["strong"], size=13),
        customdata=np.stack([d["done"], d["total"]], axis=-1),
        hovertemplate="<b>%{y}</b><br>معدل الإنجاز: %{x:.1f}%<br>منجز %{customdata[0]:,} من %{customdata[1]:,}<extra></extra>",
        showlegend=False))
    fig.add_vline(x=target, line=dict(color=_GOLD, width=2, dash="dash"),
                  annotation_text=f"المستهدف {target:.0f}%", annotation_font=dict(color=C["strong"], size=12))
    pad = max(3.0, (max(rates + [target]) - min(rates + [target])) * 0.35)
    style_fig(fig)  # الهوية أولاً ثم تفاصيل هذا الرسم
    fig.update_layout(height=max(300, 62 * len(d) + 90), margin=dict(l=10, r=70, t=34, b=10), showlegend=False)
    fig.update_xaxes(range=[min(rates + [target]) - pad, max(rates + [target]) + pad], ticksuffix="%")
    fig.update_yaxes(autorange="reversed", showgrid=False)  # الأول (الأضعف) في الأعلى
    return fig
