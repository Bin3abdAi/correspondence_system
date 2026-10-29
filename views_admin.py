"""صفحات المدير: لوحة التحليلات، جودة البيانات، النظام والتدقيق، الحوكمة، الجاهزية."""
from views_common import *  # noqa: F401,F403  (الأسماء العامة + الاستيرادات)
from views_common import (  # noqa: F401  (أسماء خاصة لا يجلبها *)
    _admin_gate)

import numpy as np

import table_engine as te
from fields import combo_multi


# ======================================================
# التبويب 1: لوحة التحليلات
# ======================================================
def render_dashboard(df: pd.DataFrame, df_visible: pd.DataFrame, df_all: pd.DataFrame, ctx: AuthContext) -> None:  # صفحة لوحة التحليلات والتنفيذ (للمدير)
    st.subheader("📊 لوحة التحليلات والتنفيذ")
    if not _admin_gate(ctx, "لوحة التحليلات والتنفيذ"):
        return
    st.caption(f"السجلات المتاحة: {len(df_visible):,}")
    if df.empty:
        st.info("لا توجد معاملات مطابقة للفلاتر الحالية.")
        return

    weekly = an.weekly_series(df)
    fc, slope = an.forecast(weekly)
    ind = an.compute_indicator(df, weekly)
    dept = an.department_performance(df)
    target = TARGET_COMPLETION_RATE

    # ---- شريط الإنذار (إيجابي/سلبي) ----
    card(f"{'✅' if ind.positive else '🚨'} <b>{ind.title}</b><br>{ind.message}",
         "ok" if ind.positive else "warn")

    # ---- المؤشرات ----
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("إجمالي المعاملات", f"{ind.total:,}")
    c2.metric("المنجزة", f"{ind.done:,}")
    c3.metric("غير المنجزة", f"{ind.total - ind.done:,}")
    c4.metric("المتأخرة عن موعدها", f"{ind.overdue:,}")
    c5.metric("معدل الإنجاز", f"{ind.rate:.1f}%",
              delta=f"{ind.delta:+.1f} نقطة" if ind.delta is not None else None)

    # ---- حلقة الإنجاز + الاتجاه الأسبوعي (مع شرح الوظيفة وطريقة القراءة) ----
    left, right = st.columns([1, 2])
    gap = ind.rate - target
    with left:
        st.markdown("##### 🎯 حلقة الإنجاز مقابل المستهدف")
        st.plotly_chart(charts.gauge(ind), width="stretch")
        card("<b>وظيفتها:</b> تقارن إنجازكم الفعلي بالمستهدف في نظرة واحدة.<br>"
             f"<b>كيف تقرؤها:</b> الحلقة الخارجية الملوّنة = المعدل الحالي، والحلقة الذهبية الداخلية = المستهدف ({target:.0f}%). "
             "أخضر = حققتم المستهدف، أصفر = قريب منه، أحمر = بعيد عنه.<br>"
             f"<b>الآن:</b> {ind.rate:.1f}% — {'فوق' if gap >= 0 else 'دون'} المستهدف بـ {abs(gap):.1f} نقطة.", "glass")
    with right:
        st.markdown("##### 📈 اتجاه الإنجاز الأسبوعي والتوقّع")
        if weekly.empty:
            st.info("لا توجد أسابيع مكتملة كافية لرسم الاتجاه.")
        else:
            recent = weekly["rate"].tail(4).mean()
            prev = weekly["rate"].iloc[-8:-4].mean() if len(weekly) >= 8 else None
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("آخر أسبوع", f"{weekly['rate'].iloc[-1]:.1f}%")
            k2.metric("متوسط 4 أسابيع", f"{recent:.1f}%", delta=f"{recent - prev:+.1f}" if prev is not None else None)
            k3.metric("ميل الاتجاه", f"{slope:+.2f}")
            k4.metric("توقّع بعد 4 أسابيع", f"{fc['rate'].iloc[-1]:.1f}%" if fc is not None else "—")
            st.plotly_chart(charts.trend_chart(weekly, fc), width="stretch")
            best, worst = weekly.loc[weekly["rate"].idxmax()], weekly.loc[weekly["rate"].idxmin()]
            card("<b>🧭 ما وظيفته؟</b> يجيب عن <b>عدة أسئلة مهمة</b> في نظرة واحدة، اقرأه بخمس خطوات:<br>"
                 "1️⃣ <b>هل نتحسّن أم نتراجع؟</b> الخط الذهبي السميك = الاتجاه العام (متوسط 4 أسابيع): صعوده تحسّن وهبوطه تراجع.<br>"
                 "2️⃣ <b>هل حققنا المستهدف؟</b> النقطة 🟢 = أسبوع بلغ المستهدف، 🔴 = دونه (والخلفية الخضراء/الحمراء تؤكد ذلك).<br>"
                 "3️⃣ <b>هل الضغط مرتفع؟</b> اللوحة السفلية = عدد المعاملات التي وصلت كل أسبوع.<br>"
                 "4️⃣ <b>ماذا سيحدث قريباً؟</b> الخط البنفسجي المنقّط = التوقّع، والظل حوله = هامش الخطأ المحتمل.<br>"
                 "5️⃣ <b>أي فترة أراجع؟</b> أزرار «شهران / 6 أشهر / الكل»، وحرّك الفأرة فوق الرسم لقراءة القيم.<br>"
                 f"<b>أفضل أسبوع:</b> {best['rate']:.1f}% ({best['week']:%Y-%m-%d}) — "
                 f"<b>أضعف أسبوع:</b> {worst['rate']:.1f}% ({worst['week']:%Y-%m-%d}).", "glass")

    if fc is not None:
        direction = "إيجابي 📈" if slope > 0.1 else "سلبي 📉" if slope < -0.1 else "ثابت ➖"
        card(f"🔮 <b>توقّع تقديري (انحدار خطي):</b> إن استمر العمل بنفس الوتيرة سيصل معدل الإنجاز إلى "
             f"<b>{fc['rate'].iloc[-1]:.1f}%</b> بعد {len(fc)} أسابيع — الاتجاه {direction} "
             f"({slope:+.2f} نقطة/أسبوع).", "ai")

    # ---- أداء الأقسام ----
    if not dept.empty:
        st.markdown("##### 🏢 أداء الأقسام مقابل المستهدف (الأضعف في الأعلى)")
        st.plotly_chart(charts.dept_chart(dept), width="stretch")
        card("<b>ما وظيفته؟</b> يدلّك على <b>القسم الذي يحتاج تدخّلاً أولاً</b>.<br>"
             f"<b>كيف تقرؤه:</b> الخط الذهبي العمودي = المستهدف ({target:.0f}%). كل نقطة = قسم، "
             "وبُعدها عن الخط = الفرق عن المستهدف (الرقم بين القوسين بالنقاط). "
             "🟢 حقق المستهدف، 🟡 قريب منه، 🔴 بعيد عنه. "
             "حجم النقطة = عدد معاملات القسم (الأكبر = ضغط أكبر). الأضعف دائماً في الأعلى. "
             "مرّر الفأرة على النقطة لترى المنجز والإجمالي.", "glass")

    # ---- المساعد التقني ----
    delta_txt = f"{ind.delta:+.1f} نقطة" if ind.delta is not None else "غير متاح"
    summary = "\n".join([
        f"- إجمالي المعاملات المطابقة للفلاتر: {ind.total:,} (المنجزة {ind.done:,})",
        f"- معدل الإنجاز ({ind.basis}): {ind.rate:.1f}% | المستهدف: {target:.0f}%",
        f"- التغير عن الفترة السابقة: {delta_txt}",
        f"- المتأخرة عن موعدها: {ind.overdue:,}",
        f"- أضعف الأقسام: {dept.index[0]} ({dept['rate'].iloc[0]:.1f}%)" if not dept.empty else "- الأقسام: لا بيانات",
        f"- ميل الاتجاه الأسبوعي (انحدار خطي): {slope:+.2f} نقطة/أسبوع",
        f"- التقييم الآلي: {ind.title}",
    ])
    st.divider()
    ai_panel("dashboard", "لوحة التحليلات والتنفيذ", summary, df_all, ctx)

    # ---- الإصدار الرسمي ----
    st.divider()
    export_bar("dashboard", "تقرير لوحة التحليلات والتنفيذ", ctx, df=df,
               text=f"{ind.title}\n{summary}")

    # ---- جدول المعاملات ----
    _transactions_table(df, ctx)


_TABLE_COLS = ["رقم المعاملة", "موضوع المعاملة", "الحي", "القسم المكلف", "درجة الأهمية", "الحالة",
               "السرية", "تاريخ الاستلام", "تاريخ الإنجاز المتوقع"]  # الأعمدة المعروضة (نخفي lat/lon وغيرها)


_PAGE_SIZES = [100, 250, 500, 1000]  # عدد الصفوف في الصفحة الواحدة
_STATUS_ICON = {"منجزة": "🟢", "قيد المعالجة الميدانية": "🟠", "غير منجزة": "🔴"}  # لون الحالة بلمحة (مثل لوحات المطار)
_PRIO_ICON = {"حرج للغاية": "🔴", "عاجل": "🟠", "هام": "🟡", "عادي": "⚪"}
_PRIO_ORDER = ["حرج للغاية", "عاجل", "هام", "عادي"]
_SUBJECT_HINTS = ["حفرة", "إنارة", "نظافة", "تصريف", "رصيف", "ترخيص", "أرض", "مخلفات", "صيانة", "أمطار"]  # اقتراحات فقط؛ اكتب أي كلمة
_TQ_LISTS = ["trx", "subject", "district", "dept", "priority", "status", "level", "sender"]  # خانات القوائم في الاستعلام
_TQ_DATES = ["recv_from", "recv_to", "due_from", "due_to"]                                 # خانات التواريخ


def _tq_reset() -> None:  # زر «مسح»: يعيد كل خانات الاستعلام لوضعها الفارغ (يعمل كـ callback قبل رسم الودجت)
    for k in _TQ_LISTS:
        st.session_state[f"tq_{k}"] = []
    for k in _TQ_DATES:
        st.session_state[f"tq_{k}"] = None
    st.session_state["tq_overdue"] = False
    st.session_state["tbl_page"] = 1


def _tq_goto(where: str) -> None:  # أزرار التنقل بين الصفحات (أولى/سابقة/تالية/أخيرة) — callback
    pages = int(st.session_state.get("_tq_pages", 1) or 1)
    cur = int(st.session_state.get("tbl_page", 1) or 1)
    st.session_state["tbl_page"] = {"first": 1, "prev": max(1, cur - 1), "next": min(pages, cur + 1), "last": pages}[where]


def _unique_opts(df: pd.DataFrame, col: str, order=None) -> list:  # خيارات الخانة من البيانات المرئية للمستخدم فقط
    if col not in df.columns or df.empty:
        return []
    vals = [str(v) for v in pd.unique(df[col].dropna())]
    if order:
        return [v for v in order if v in vals] + sorted(v for v in vals if v not in order)
    return sorted(vals)


def _data_version() -> tuple:  # بصمة القاعدة الرخيصة (عدد + آخر رقم + عدّاد التعديلات)؛ تتغير عند أي إضافة أو تعديل حالة
    try:
        return tuple(db.data_version())
    except Exception:  # noqa: BLE001
        return (0, 0, 0)


def _result_stats(df: pd.DataFrame, pos: "np.ndarray") -> dict:  # أرقام سريعة عن نتيجة الاستعلام (منجزة/متأخرة)
    if len(pos) == 0:
        return {"done": 0, "late": 0}
    status = df["الحالة"].iloc[pos]
    done = int((status == STATUS_DONE).sum())
    late = 0
    if "تاريخ الإنجاز المتوقع" in df.columns:
        today = pd.Timestamp.today().normalize()
        due = df["تاريخ الإنجاز المتوقع"].iloc[pos]
        late = int(((status != STATUS_DONE) & (due < today)).sum())
    return {"done": done, "late": late}


def _decorate(shown: pd.DataFrame) -> pd.DataFrame:  # يضيف أيقونات لونية للحالة والأهمية وعمود «المهلة» (للصفحة المعروضة فقط)
    out = shown.copy()
    st_txt = out["الحالة"].astype(str)
    late = pd.Series(False, index=out.index)
    if "تاريخ الإنجاز المتوقع" in out.columns:
        late = (st_txt != STATUS_DONE) & (out["تاريخ الإنجاز المتوقع"] < pd.Timestamp.today().normalize())
    out["الحالة"] = st_txt.map(lambda v: f"{_STATUS_ICON.get(v, '⚪')} {v}")
    out["درجة الأهمية"] = out["درجة الأهمية"].astype(str).map(lambda v: f"{_PRIO_ICON.get(v, '⚪')} {v}")
    out["المهلة"] = np.where(st_txt == STATUS_DONE, "✔ منجزة", np.where(late, "⏰ متأخرة", "⏳ ضمن المهلة"))
    return out


def _tq_counters(total: int, n: int, stats: dict) -> None:  # بطاقات الأرقام الحية فوق النتائج (ألوانها من النمط فتُقرأ في كل الأنماط)
    st.markdown(
        '<div class="ops-grid">'
        f'<div class="ops-card info"><span>نطاق الاستعلام (المتاح لك)</span><b>{total:,}</b></div>'
        f'<div class="ops-card info"><span>نتائج الاستعلام</span><b>{n:,}</b></div>'
        f'<div class="ops-card ok"><span>منجزة ضمن النتائج</span><b>{stats["done"]:,}</b></div>'
        f'<div class="ops-card danger"><span>متأخرة ضمن النتائج</span><b>{stats["late"]:,}</b></div>'
        '</div>', unsafe_allow_html=True)


def _transactions_table(df: pd.DataFrame, ctx: AuthContext) -> None:  # جدول استعلام بأسلوب لوحات المطار: كل خانة تُختار أو يُبحث فيها أو تُكتب قيمتها يدوياً، ثم اضغط أي صف لتظهر أزرار التعامل معه
    """جدول استعلام متقدم على كل السجلات المتاحة للمستخدم (مئات الآلاف). الاستعلام يعمل داخل الذاكرة بمصفوفات رقمية
    (table_engine) فيبقى سريعاً، والنتيجة تُحفظ في الجلسة حتى لا يُعاد حسابها عند تقليب الصفحات."""
    st.divider()
    st.subheader("📋 جدول المعاملات — استعلام متقدم")
    if ctx.logged_in:
        card(f"🔓 تم التوثيق: تُعرض المستويات {'، '.join(ctx.visible_levels)}.", "ok")
    else:
        card("🔒 تنبيه أمني: تُعرض المعاملات العامة فقط. سجّل الدخول لعرض المستويات الأعلى وللتعديل.", "warn")

    total, vis = len(df), list(ctx.visible_levels)
    with st.form("tq_form"):
        st.markdown("**🔎 اكتب للبحث، أو اختر من القائمة، أو أضف قيمتك بنفسك ثم Enter.** "
                    "في الخانة الواحدة عدة قيم تعمل بمعنى «أو»، والخانات معاً بمعنى «و».")
        a1, a2 = st.columns(2)
        trx = combo_multi("🔢 رقم المعاملة (أو جزء منه)", [], key="tq_trx", target=a1, placeholder="مثال: TRX-JED-0755766")
        subject = combo_multi("📝 موضوع المعاملة", _SUBJECT_HINTS, key="tq_subject", target=a2, placeholder="اختر كلمة أو اكتب أي كلمة")
        b1, b2, b3, b4 = st.columns(4)
        district = combo_multi("📍 الحي", _unique_opts(df, "الحي"), key="tq_district", target=b1)
        dept = combo_multi("🏢 القسم المكلف", _unique_opts(df, "القسم المكلف"), key="tq_dept", target=b2)
        priority = combo_multi("⚡ درجة الأهمية", _unique_opts(df, "درجة الأهمية", _PRIO_ORDER), key="tq_priority", target=b3)
        status = combo_multi("📌 الحالة", _unique_opts(df, "الحالة", STATUSES), key="tq_status", target=b4)
        c1, c2, c3, c4 = st.columns(4)
        level = combo_multi("🔐 السرية", vis, key="tq_level", target=c1)
        sender = combo_multi("🏛️ نوع الجهة", _unique_opts(df, "نوع الجهة"), key="tq_sender", target=c2)
        recv_from = c3.date_input("📥 استُلمت من تاريخ", value=None, key="tq_recv_from", format="YYYY/MM/DD")
        recv_to = c4.date_input("📥 إلى تاريخ", value=None, key="tq_recv_to", format="YYYY/MM/DD")
        d1, d2, d3, d4 = st.columns(4)
        due_from = d1.date_input("⏰ الموعد المتوقع من", value=None, key="tq_due_from", format="YYYY/MM/DD")
        due_to = d2.date_input("⏰ الموعد المتوقع إلى", value=None, key="tq_due_to", format="YYYY/MM/DD")
        order = d3.selectbox("↕️ الترتيب", te.ORDERS, key="tq_order")
        overdue = d4.toggle("⏰ المتأخرة عن موعدها فقط", key="tq_overdue")
        go1, go2 = st.columns([3, 1])
        go1.form_submit_button("🔍 بحث", type="primary", width="stretch")
        go2.form_submit_button("↺ مسح الخانات", on_click=_tq_reset, width="stretch")

    q = {"trx": trx, "subject": subject, "district": district, "dept": dept, "priority": priority, "status": status,
         "level": level, "sender": sender, "recv_from": recv_from, "recv_to": recv_to, "due_from": due_from,
         "due_to": due_to, "overdue": overdue}
    first, last = (int(df.index[0]), int(df.index[-1])) if total else (0, 0)
    scope = (_data_version(), total, first, last, ctx.role, ctx.department)  # يتغير عند تغيّر البيانات أو الصلاحية أو فلاتر الشريط الجانبي
    sig = (scope, te.signature(q, order))
    cache = st.session_state.get("_tq_cache")
    if not cache or cache["sig"] != sig:
        if cache and cache["sig"][1] != sig[1]:  # تغيّر الاستعلام نفسه: نعود للصفحة الأولى
            st.session_state["tbl_page"] = 1
        pos = te.query_positions(df, q, order, vocabs={"level": vis}, done_label=STATUS_DONE)
        cache = {"sig": sig, "pos": pos, "stats": _result_stats(df, pos)}
        st.session_state["_tq_cache"] = cache
    pos, n = cache["pos"], len(cache["pos"])

    _tq_counters(total, n, cache["stats"])
    desc = te.describe_query(q)
    st.caption(f"الاستعلام الحالي: {desc}" if desc else "بلا شروط: تُعرض كل المعاملات المتاحة لك.")
    if n == 0:
        st.info("لا توجد معاملات مطابقة للاستعلام. خفّف الشروط أو اضغط «مسح الخانات».")
        return

    p1, p2, p3 = st.columns([1, 1, 2])
    size = p1.selectbox("عدد الصفوف في الصفحة", _PAGE_SIZES, index=1, key="tbl_size")
    pages = max(1, -(-n // size))  # تقريب لأعلى
    st.session_state["_tq_pages"] = pages
    st.session_state["tbl_page"] = min(max(int(st.session_state.get("tbl_page", 1) or 1), 1), pages)  # لا نتجاوز آخر صفحة بعد تضييق الاستعلام
    page = int(p2.number_input(f"الصفحة (من {pages:,})", min_value=1, max_value=pages, step=1, key="tbl_page"))
    with p3:
        n1, n2, n3, n4 = st.columns(4)
        n1.button("⏮ الأولى", key="tq_first", on_click=_tq_goto, args=("first",), width="stretch")
        n2.button("◀ السابقة", key="tq_prev", on_click=_tq_goto, args=("prev",), width="stretch")
        n3.button("التالية ▶", key="tq_next", on_click=_tq_goto, args=("next",), width="stretch")
        n4.button("الأخيرة ⏭", key="tq_last", on_click=_tq_goto, args=("last",), width="stretch")

    a = (page - 1) * size
    sub = df.iloc[pos[a:a + size]]  # الصفحة المعروضة فقط تُنسخ (لا كل النتائج)
    shown = _decorate(sub[[c for c in _TABLE_COLS if c in sub.columns]].reset_index(drop=True))
    event = st.dataframe(
        shown, width="stretch", height=420, hide_index=True,
        on_select="rerun", selection_mode="single-row", key="tbl_sel",
        column_config={
            "تاريخ الاستلام": st.column_config.DateColumn("تاريخ الاستلام", format="YYYY-MM-DD"),
            "تاريخ الإنجاز المتوقع": st.column_config.DateColumn("تاريخ الإنجاز المتوقع", format="YYYY-MM-DD"),
            "موضوع المعاملة": st.column_config.TextColumn("موضوع المعاملة", width="large"),
        })
    st.caption(f"النتائج: {n:,} معاملة من أصل {total:,} — المعروض: {len(shown):,} (الصفحة {page} من {pages:,}). "
               "👆 اضغط على أي صف لتظهر أزرار التعامل معه. البيانات تجريبية لأغراض العرض.")
    st.download_button("⬇️ تنزيل الصفحة المعروضة (CSV)", data=csv_bytes(sub[[c for c in _TABLE_COLS if c in sub.columns]]),
                       file_name=f"transactions_page{page}.csv", mime="text/csv", key="tq_dl")
    rows = event.selection.rows if event and event.selection else []
    if rows and rows[0] < len(shown):
        _row_actions(shown.iloc[rows[0]], df, ctx)


_ROW_ACTIONS = {"details": "🔎 التفاصيل", "ai": "🤖 حلّل بالذكاء", "assign": "👷 كلّف فريقاً",
                "status": "✅ غيّر الحالة", "report": "📄 تقرير"}


def _row_actions(rec: pd.Series, df: pd.DataFrame, ctx: AuthContext) -> None:  # أزرار التعامل مع المعاملة المختارة
    """أزرار التعامل مع المعاملة المختارة. الإجراء المختار يُحفظ في الجلسة حتى لا يختفي عند إعادة الرسم."""
    trx = str(rec["رقم المعاملة"])
    st.markdown(f'<div class="ai-card-glow"><b>المعاملة المختارة: {html.escape(trx)}</b><br>'
                f'{html.escape(str(rec["موضوع المعاملة"]))}<br>'
                f'<span style="color:#94a3b8">{html.escape(str(rec["الحي"]))} | {html.escape(str(rec["القسم المكلف"]))} | '
                f'{html.escape(str(rec["درجة الأهمية"]))} | {html.escape(str(rec["الحالة"]))}</span></div>',
                unsafe_allow_html=True)
    act_key = "row_act"
    cols = st.columns(len(_ROW_ACTIONS))
    for col, (key, label) in zip(cols, _ROW_ACTIONS.items()):
        if col.button(label, key=f"rowbtn:{key}:{trx}", width="stretch"):
            st.session_state[act_key] = (trx, key)
    chosen = st.session_state.get(act_key)
    if not chosen or chosen[0] != trx:
        st.caption("اختر أحد الأزرار أعلاه.")
        return
    act = chosen[1]
    col = df["رقم المعاملة"]
    full = df[(col if col.dtype == object else col.astype(str)) == trx]  # الصف الكامل من البيانات المسموحة للمستخدم فقط (بلا تحويل مكلف لمئات الآلاف)
    if full.empty:
        st.error("المعاملة خارج صلاحياتك.")
        return
    row = full.iloc[0]

    if act == "details":
        today = pd.Timestamp.today().normalize()
        age = (today - row["تاريخ الاستلام"]).days if pd.notna(row.get("تاريخ الاستلام")) else None
        late = (row["الحالة"] != STATUS_DONE and pd.notna(row.get("تاريخ الإنجاز المتوقع"))
                and row["تاريخ الإنجاز المتوقع"] < today)
        info = {"الحقل": [], "القيمة": []}
        for k in [*_TABLE_COLS, "سبب عدم الإنجاز", "نوع الجهة", "اسم الجهة"]:
            if k in row.index:
                info["الحقل"].append(k)
                info["القيمة"].append(str(row[k])[:200])
        info["الحقل"] += ["عمر المعاملة (يوم)", "متأخرة؟"]
        info["القيمة"] += [str(age) if age is not None else "—", "نعم ⏰" if late else "لا"]
        st.dataframe(pd.DataFrame(info), width="stretch", hide_index=True)

    elif act == "ai":
        cache = st.session_state.setdefault("row_ai", {})
        ck = f"{trx}:{ctx.role}"
        if ck not in cache:
            fields = "\n".join(f"- {k}: {row[k]}" for k in [*_TABLE_COLS, "سبب عدم الإنجاز"] if k in row.index)
            with st.spinner("⏳ يحلّل المعاملة..."):
                cache[ck] = ask_assistant(
                    "حلّل هذه المعاملة: ما وضعها؟ هل هي متأخرة ولماذا قد تتأخر؟ ما الإجراء الأنسب والفريق/القسم "
                    f"المناسب والمدة المتوقعة؟\n{fields}", [], ctx, load_all_transactions())
        show_reply(cache[ck], key=f"rowai:{ck}")

    elif act == "assign":
        if not ctx.logged_in:
            card("🔒 تكليف الفرق يتطلب تسجيل الدخول.", "warn")
            return
        dept = str(row["القسم المكلف"])
        assignments = load_assignments()
        sub = df[df["القسم المكلف"] == dept]  # فرق هذا القسم فقط (أسرع)
        stats = an.team_stats(sub, an.assign_teams(sub, assignments))
        sug = an.suggest_team(stats, dept)
        if sug:
            card(f"🤖 <b>الفريق الأنسب:</b> {html.escape(an.team_name(dept, sug[0]))} — الأقل حِملاً ({sug[1]:,} مهمة مفتوحة).", "ai")
        pick = st.selectbox("الفريق المكلّف", list(range(1, an.TEAMS_PER_DEPT + 1)),
                            index=(sug[0] - 1) if sug else 0, format_func=lambda k: an.team_name(dept, k),
                            key=f"rowteam:{trx}")
        note = st.text_input("ملاحظة للفريق (اختياري)", key=f"rownote:{trx}")
        if st.button("✅ اعتماد التكليف", key=f"rowassign:{trx}", width="stretch", disabled=not ctx.can_write):
            save_assignment(trx, pick, dept, note, ctx.username or "-")
            audit("field_assignment", ctx, trx=trx, team=pick)
            st.success(f"تم تكليف {an.team_name(dept, pick)} بالمعاملة {trx}.")

    elif act == "status":
        if not ctx.logged_in:
            card("🔒 تغيير الحالة يتطلب تسجيل الدخول.", "warn")
            return
        new = st.selectbox("الحالة الجديدة", STATUSES, index=STATUSES.index(str(row["الحالة"])) if str(row["الحالة"]) in STATUSES else 0,
                           key=f"rowstatus:{trx}")
        sure = st.checkbox("أؤكد تغيير الحالة", key=f"rowsure:{trx}")
        if st.button("💾 حفظ الحالة", key=f"rowsave:{trx}", width="stretch", disabled=not sure):
            changed = db.update_transaction_status(trx, new)
            if changed:
                audit("status_changed", ctx, trx=trx, old=str(row["الحالة"]), new=new)
                st.success("✅ تم تحديث الحالة. ستنعكس الأرقام عند إعادة تحميل البيانات.")
                st.rerun()
            else:
                st.warning("هذه معاملة تجريبية غير مخزّنة في قاعدة البيانات، لذلك لا يمكن تعديلها.")

    elif act == "report":
        one = full[[c for c in _TABLE_COLS if c in full.columns]]
        d1, d2 = st.columns(2)
        d1.download_button("⬇️ CSV للمعاملة", csv_bytes(one), file_name=f"{trx}.csv", mime="text/csv",
                           width="stretch", key=f"rowcsv:{trx}")
        try:
            pdf = pdf_bytes(f"تقرير معاملة {trx}", f"TRX-{trx}", ctx,
                            text=f"{row['موضوع المعاملة']}\nالحالة: {row['الحالة']} | الأهمية: {row['درجة الأهمية']}",
                            df=one)
            d2.download_button("⬇️ PDF رسمي", pdf, file_name=f"{trx}.pdf", mime="application/pdf",
                               width="stretch", key=f"rowpdf:{trx}")
        except Exception as exc:
            d2.warning(f"تعذّر إنشاء PDF: {exc}")


# ======================================================
# التبويب 6: الحوكمة
# ======================================================
def render_governance(ctx: AuthContext) -> None:  # صفحة الحوكمة والامتثال والرقابة
    st.subheader("⚖️ لوحة الحوكمة والامتثال والسياسات الأمنية")
    if not _admin_gate(ctx, "الحوكمة والامتثال وسجل التدقيق"):
        return
    policies = ("• البيانات السرية تُفلتر في الخادم قبل وصولها للواجهة أو للمودل.\n"
                "• كل دخول وخروج وسؤال للمساعد وإنشاء معاملة وتصدير وتنبيه يُسجَّل في سجل التدقيق.\n"
                "• الالتزام بسياسات منظومة أمانة محافظة جدة.")
    card("<b>🛡️ معايير الأمن السيبراني والحوكمة المؤسسية:</b><br>"
         + html.escape(policies).replace("\n", "<br>"))
    if ctx.role == "admin":
        st.markdown("#### 🧾 آخر أحداث التدقيق")
        log = Path("audit.log")
        lines = log.read_text(encoding="utf-8").splitlines()[-50:] if log.exists() else []
        st.code("\n".join(reversed(lines)) or "لا توجد أحداث بعد.", language="text")

    st.divider()
    ai_panel("governance", "الحوكمة والامتثال", policies, None, ctx)
    st.divider()
    export_bar("governance", "تقرير الحوكمة والامتثال", ctx, text=policies)


# ======================================================
# التبويب 7: الجاهزية (فحوصات حقيقية)
# ======================================================
def render_readiness(df_all: pd.DataFrame) -> None:  # صفحة جاهزية المشروع والتدقيق الشامل
    ctx = get_auth_context()
    st.subheader("🚀 تقرير جاهزية المشروع والتدقيق الشامل")
    if not _admin_gate(ctx, "تقرير الجاهزية والتدقيق الشامل"):
        return
    checks = [
        (f"قاعدة البيانات: {len(df_all):,} سجل", len(df_all) > 0),
        ("مفتاح OpenAI مضبوط", client is not None),
        ("كلمات المرور مضبوطة (hash)", bool(get_setting("ADMIN_PASSWORD_HASH"))),
        ("المساعد الصوتي محمّل", VOICE_AVAILABLE),
        ("البريد الرسمي مضبوط (SMTP)", bool(get_setting("SMTP_HOST") and get_setting("SMTP_USER"))),
        ("أصوات ElevenLabs مضبوطة (اختياري)", bool(get_setting("ELEVENLABS_API_KEY") and get_setting("ELEVENLABS_VOICE_ID"))),
        ("فلترة السرية مفعّلة على المساعد", True),
    ]
    for col, (text, ok) in zip(st.columns(len(checks)), checks):
        (col.success if ok else col.error)(f"{'✅' if ok else '❌'} {text}")

    summary = "\n".join(f"- {'✅' if ok else '❌'} {text}" for text, ok in checks)
    st.divider()
    ai_panel("readiness", "جاهزية المشروع", summary, df_all, ctx)
    st.divider()
    export_bar("readiness", "تقرير جاهزية المشروع", ctx, text=summary)


# ======================================================
# تبويب جودة البيانات (للمدير)
# ======================================================
_DORMANT_DAYS = 180  # معاملة مفتوحة أقدم من هذا تُعدّ راكدة


def _quality_issues(df: pd.DataFrame) -> dict:  # يرجع {وصف المشكلة: الصفوف المتأثرة}
    """يرجع {وصف المشكلة: الصفوف المتأثرة}."""
    today = pd.Timestamp.today().normalize()
    rec, exp = df["تاريخ الاستلام"], df["تاريخ الإنجاز المتوقع"]
    blank = lambda c: df[c].isna() | (df[c].astype(str).str.strip() == "")
    return {
        "موضوع ناقص أو قصير جداً": df[df["موضوع المعاملة"].astype(str).str.strip().str.len() < 8],
        "حي غير محدد": df[blank("الحي")],
        "قسم غير محدد": df[blank("القسم المكلف")],
        "تاريخ استلام أو إنجاز ناقص": df[rec.isna() | exp.isna()],
        "موعد الإنجاز قبل الاستلام": df[exp < rec],
        "مكررة (نفس الموضوع والحي والقسم)": df[df.duplicated(subset=["موضوع المعاملة", "الحي", "القسم المكلف"], keep=False)],
        "رقم معاملة مكرر": df[df["رقم المعاملة"].duplicated(keep=False)],
        f"راكدة: مفتوحة منذ أكثر من {_DORMANT_DAYS} يوماً": df[(df["الحالة"] != STATUS_DONE) & ((today - rec).dt.days > _DORMANT_DAYS)],
    }


def render_quality(ctx: AuthContext, df_all: pd.DataFrame) -> None:  # لوحة جودة البيانات: تكشف الناقص والمكرر والراكد وتعطي درجة جودة
    """لوحة جودة البيانات: تكشف الناقص والمكرر والراكد وتعطي درجة جودة."""
    st.subheader("🧪 لوحة جودة البيانات")
    if not _admin_gate(ctx, "لوحة جودة البيانات"):
        return
    key = ("q", len(df_all))
    if st.button("🔄 إعادة الفحص", key="q_rerun") or st.session_state.get("_q_key") != key:
        with st.spinner("يفحص السجلات..."):
            st.session_state["_q_issues"] = _quality_issues(df_all)
            st.session_state["_q_key"] = key
    issues = st.session_state["_q_issues"]
    n = max(len(df_all), 1)
    bad = pd.concat([v.index.to_series() for v in issues.values()]).nunique() if any(len(v) for v in issues.values()) else 0
    score = 100 * (1 - bad / n)
    k1, k2, k3 = st.columns(3)
    k1.metric("درجة جودة البيانات", f"{score:.1f}%", help="نسبة السجلات التي لا تحمل أي مشكلة من المشكلات أدناه")
    k2.metric("سجلات بها ملاحظات", f"{bad:,}")
    k3.metric("إجمالي السجلات", f"{n:,}")
    table = pd.DataFrame([{"المشكلة": k, "العدد": len(v), "النسبة من الكل %": round(len(v) / n * 100, 2)} for k, v in issues.items()])
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={"النسبة من الكل %": st.column_config.ProgressColumn("النسبة من الكل %", min_value=0, max_value=100, format="%.2f")})
    st.caption("درجة الجودة = نسبة السجلات الخالية من كل المشكلات. المكررة قد تكون مشروعة (بلاغان من مواطنين) فراجعها قبل الحذف.")
    pick = st.selectbox("اعرض أمثلة من مشكلة", [k for k, v in issues.items() if len(v)] or ["—"], key="q_pick")
    if pick in issues and len(issues[pick]):
        sample = issues[pick][[c for c in _TABLE_COLS if c in issues[pick].columns]].head(300)
        st.dataframe(sample, hide_index=True, width="stretch")
        st.download_button("⬇️ CSV لهذه المشكلة", csv_bytes(sample), file_name="quality_issue.csv", mime="text/csv", key="q_dl")


# ======================================================
# النظام: النسخ الاحتياطي + حالة النظام + التحديثات + سجل التدقيق القابل للتصدير
# ======================================================
_APP_START = datetime.datetime.now()  # لحساب مدة التشغيل


def render_system(ctx: AuthContext) -> None:  # صفحة النظام: النسخ الاحتياطي وسجل التدقيق والفحوص
    st.subheader("🛡️ النظام: النسخ الاحتياطي والتدقيق والتحديثات")
    if not _admin_gate(ctx, "النظام والنسخ والتدقيق"):
        return
    import shutil
    # ---- حالة النظام ----
    backups = sx.list_backups()
    disk = shutil.disk_usage(".")
    items = [("🗄️ قاعدة البيانات", f"{Path(db.DB_FILE).stat().st_size / 1e6:,.1f} MB" if Path(db.DB_FILE).exists() else "—"),
             ("💾 آخر نسخة", datetime.datetime.fromtimestamp(backups[0].stat().st_mtime).strftime("%Y-%m-%d %H:%M") if backups else "لا توجد"),
             ("🧠 مفتاح OpenAI", "مضبوط" if client else "غير مضبوط"),
             ("⏱️ مدة التشغيل", f"{(datetime.datetime.now() - _APP_START).seconds // 3600} س {(datetime.datetime.now() - _APP_START).seconds // 60 % 60} د"),
             ("💽 مساحة القرص الحرة", f"{disk.free / 1e9:,.1f} GB")]
    for col, (t, v) in zip(st.columns(len(items)), items):
        col.metric(t, v)
    t_bk, t_up, t_au = st.tabs(["💾 النسخ الاحتياطي", "🔔 تحديثات المكتبات", "🧾 سجل التدقيق"])
    with t_bk:
        st.caption("تُؤخذ نسخة تلقائية كل 24 ساعة عند تشغيل المنصة، وتُحفظ آخر 10 نسخ في مجلد backups. النسخة تضم القاعدة والمشاريع والصور وسجل التدقيق، ولا تضم ملف .env.")
        if st.button("💾 خذ نسخة احتياطية الآن", key="bk_now", width="stretch"):
            path = sx.make_backup()
            audit("backup_created", ctx, file=path.name)
            st.success(f"تمت النسخة: {path.name}")
            backups = sx.list_backups()
        if backups:
            st.dataframe(pd.DataFrame([{"الملف": b.name, "الحجم (MB)": round(b.stat().st_size / 1e6, 2),
                                        "التاريخ": datetime.datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
                                       for b in backups]), hide_index=True, width="stretch")
            st.download_button("⬇️ تنزيل آخر نسخة", backups[0].read_bytes(), file_name=backups[0].name, mime="application/zip", key="bk_dl")
            st.warning("احفظ نسخة خارج الجهاز (OneDrive أو قرص خارجي) دورياً؛ النسخ المحلية وحدها لا تحمي من تلف الجهاز.")
    with t_up:
        st.caption("يقارن إصدارات المكتبات المثبّتة بآخر إصدار على PyPI. لا يفحص الثغرات نفسها، لكن التقادم أهم مؤشر على تفويت إصلاحات أمنية.")
        if st.button("🔍 افحص التحديثات", key="upd", width="stretch"):
            with st.spinner("يتصل بـ PyPI..."):
                st.session_state["_upd"] = sx.check_updates()
            audit("update_check", ctx)
        rows = st.session_state.get("_upd")
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            old = [r["المكتبة"] for r in rows if r["الحالة"] in ("تحديث متاح", "تحديث رئيسي متاح")]
            if old:
                card("🔔 <b>تحديثات متاحة.</b> نفّذ في الطرفية (بعد أخذ نسخة احتياطية):<br><code>pip install --upgrade "
                     + " ".join(old) + "</code>", "warn")
            else:
                card("✅ كل المكتبات المفحوصة محدّثة.", "ok")
    with t_au:
        log = sx.parse_audit()
        if log.empty:
            st.info("لا توجد أحداث بعد.")
            return
        c1, c2, c3 = st.columns(3)
        ev = c1.multiselect("الحدث", sorted(log["الحدث"].unique()), key="au_ev")
        us = c2.multiselect("المستخدم", sorted(log["المستخدم"].unique()), key="au_us")
        q = c3.text_input("بحث في التفاصيل", key="au_q")
        view = log
        if ev:
            view = view[view["الحدث"].isin(ev)]
        if us:
            view = view[view["المستخدم"].isin(us)]
        if q:
            view = view[view["التفاصيل"].str.contains(q, case=False, regex=False)]
        st.caption(f"{len(view):,} حدثاً من {len(log):,}. محاولات الدخول الفاشلة: {int((log['الحدث'] == 'login_failed').sum()):,}")
        st.dataframe(view.head(1000), hide_index=True, width="stretch")
        d1, d2 = st.columns(2)
        d1.download_button("⬇️ تصدير CSV", csv_bytes(view), file_name="audit_log.csv", mime="text/csv", key="au_csv", width="stretch")
        try:
            d2.download_button("⬇️ تصدير PDF", pdf_bytes("سجل التدقيق", f"AUDIT-{datetime.date.today():%Y%m%d}", ctx,
                                                       text=f"عدد الأحداث المعروضة: {len(view):,} (أحدث 300 في الجدول)",
                                                       df=view.head(300), classification="سري"),
                               file_name="audit_log.pdf", mime="application/pdf", key="au_pdf", width="stretch")
        except Exception as exc:
            d2.warning(f"تعذّر إنشاء PDF: {exc}")


