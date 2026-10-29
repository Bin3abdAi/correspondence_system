"""صفحات المدير: لوحة التحليلات، جودة البيانات، النظام والتدقيق، الحوكمة، الجاهزية."""
from views_common import *  # noqa: F401,F403  (الأسماء العامة + الاستيرادات)
from views_common import (  # noqa: F401  (أسماء خاصة لا يجلبها *)
    _admin_gate)


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


_PRIORITY_RANK = {"حرج للغاية": 0, "عاجل": 1, "هام": 2, "عادي": 3}  # الأصغر = الأخطر


_PAGE_SIZES = [100, 250, 500]  # عدد الصفوف في الصفحة الواحدة


def _filter_table(df: pd.DataFrame, query: str, status: str, priority: str, overdue: bool) -> pd.DataFrame:  # يطبّق بحث الجدول وفلاتره على كامل السجلات (لا على الصفحة المعروضة فقط)
    """يطبّق بحث الجدول وفلاتره على كامل السجلات (لا على الصفحة المعروضة فقط)."""
    view = df
    if query:
        q = query.strip()
        mask = (view["موضوع المعاملة"].astype(str).str.contains(q, case=False, regex=False, na=False)
                | view["رقم المعاملة"].astype(str).str.contains(q, case=False, regex=False, na=False))
        view = view[mask]
    if status != ALL_LABEL:
        view = view[view["الحالة"] == status]
    if priority != ALL_LABEL:
        view = view[view["درجة الأهمية"] == priority]
    if overdue and "تاريخ الإنجاز المتوقع" in view:
        today = pd.Timestamp.today().normalize()
        view = view[(view["الحالة"] != STATUS_DONE) & (view["تاريخ الإنجاز المتوقع"] < today)]
    return view


def _sort_table(view: pd.DataFrame, order: str) -> pd.DataFrame:  # ترتيب النتائج حسب اختيار المستخدم
    """ترتيب النتائج حسب اختيار المستخدم."""
    if order == "الأحدث استلاماً":
        return view.sort_values("تاريخ الاستلام", ascending=False)
    if order == "الأقرب موعداً":
        return view.sort_values("تاريخ الإنجاز المتوقع", ascending=True)
    rank = view["درجة الأهمية"].astype(str).map(_PRIORITY_RANK).fillna(9)  # الأعلى أهمية
    return view.assign(_r=rank).sort_values(["_r", "تاريخ الإنجاز المتوقع"]).drop(columns="_r")


def _transactions_table(df: pd.DataFrame, ctx: AuthContext) -> None:  # جدول تفاعلي: بحث + فلاتر + ترتيب + صفحات، ثم اضغط أي صف لتظهر أزرار التعامل مع
    """جدول تفاعلي: بحث + فلاتر + ترتيب + صفحات، ثم اضغط أي صف لتظهر أزرار التعامل معه."""
    st.divider()
    st.subheader("📋 جدول المعاملات التفاعلي")
    if ctx.logged_in:
        card(f"🔓 تم التوثيق: تُعرض المستويات {'، '.join(ctx.visible_levels)}.", "ok")
    else:
        card("🔒 تنبيه أمني: تُعرض المعاملات العامة فقط. سجّل الدخول لعرض المستويات الأعلى وللتعديل.", "warn")

    c1, c2, c3, c4 = st.columns([2.4, 1, 1, 1])
    query = c1.text_input("🔎 بحث بالرقم أو الموضوع", key="tbl_q", placeholder="مثال: حفرة، TRX-JED-0755766")
    status = c2.selectbox("الحالة", [ALL_LABEL, *STATUSES], key="tbl_status")
    priority = c3.selectbox("الأهمية", [ALL_LABEL, *PRIORITIES], key="tbl_priority")
    order = c4.selectbox("الترتيب", ["الأعلى أهمية", "الأحدث استلاماً", "الأقرب موعداً"], key="tbl_order")
    overdue = st.toggle("⏰ المتأخرة عن موعدها فقط", key="tbl_overdue")

    view = _sort_table(_filter_table(df, query, status, priority, overdue), order)
    n = len(view)
    if n == 0:
        st.info("لا توجد معاملات مطابقة للبحث.")
        return
    p1, p2 = st.columns([1, 1])
    size = p1.selectbox("عدد الصفوف في الصفحة", _PAGE_SIZES, index=1, key="tbl_size")
    pages = max(1, -(-n // size))  # تقريب لأعلى
    page = p2.number_input(f"الصفحة (من {pages:,})", min_value=1, max_value=pages, value=1, step=1, key="tbl_page")
    shown = view.iloc[(page - 1) * size: page * size][[c for c in _TABLE_COLS if c in view.columns]].reset_index(drop=True)

    event = st.dataframe(
        shown, width="stretch", height=420, hide_index=True,
        on_select="rerun", selection_mode="single-row", key="tbl_sel",
        column_config={
            "تاريخ الاستلام": st.column_config.DateColumn("تاريخ الاستلام", format="YYYY-MM-DD"),
            "تاريخ الإنجاز المتوقع": st.column_config.DateColumn("تاريخ الإنجاز المتوقع", format="YYYY-MM-DD"),
            "موضوع المعاملة": st.column_config.TextColumn("موضوع المعاملة", width="large"),
        })
    st.caption(f"النتائج: {n:,} معاملة — المعروض: {len(shown):,} (الصفحة {page} من {pages:,}). "
               "👆 اضغط على أي صف لتظهر أزرار التعامل معه.")
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
    full = df[df["رقم المعاملة"].astype(str) == trx]  # الصف الكامل من البيانات المسموحة للمستخدم فقط
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
