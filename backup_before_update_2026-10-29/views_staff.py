"""صفحات الموظفين: الإدخال، الفرق الميدانية والتحليل التنبؤي، الخطابات الرسمية، المساعد وصانع الخطابات، غرفة GIS."""
from views_common import *  # noqa: F401,F403  (الأسماء العامة + الاستيرادات)
from views_common import (  # noqa: F401  (أسماء خاصة لا يجلبها *)
    _admin_gate,
    _frame,
    _speak_once)


# ======================================================
# التبويب 2: إدخال البيانات والتحليل الذكي
# ======================================================
_SEVERITY_ICON = {"منخفضة": "🟢", "متوسطة": "🟡", "عالية": "🟠", "حرجة": "🔴"}


_RESULT_FILTERS = {
    "الكل": lambda d: d,
    "تخص البلدية": lambda d: d[d["تخص البلدية"] == "نعم"],
    "لا تخص البلدية": lambda d: d[d["تخص البلدية"] == "لا"],
    "تحتاج مراجعة": lambda d: d[d["حالة التحقق"] == "تحتاج مراجعة"],
    "مرفوضة": lambda d: d[d["حالة التحقق"] == "مرفوضة"],
}


def render_intake(ctx: AuthContext) -> None:  # صفحة إدخال البيانات (للموظفين)
    st.subheader("📝 إدخال البيانات والتحليل الذكي")
    if not ctx.logged_in:
        card("🔒 إدخال المعاملات والتحليل الذكي يتطلبان تسجيل الدخول.", "warn")
        return
    if not ctx.can_write:
        card("👁️ حسابك للمراجعة (قراءة فقط): لا يمكنك إدخال معاملات أو استيراد ملفات.", "warn")
        return
    tab_report, tab_files = st.tabs(["📷 بلاغ بصورة وإدخال يدوي", "📂 محلل الملفات"])
    with tab_report:
        _intake_report(ctx)
    with tab_files:
        _intake_files(ctx)

    summary = ("- صفحة إدخال المعاملات: بلاغ بصورة (تحليل بصري) وإدخال يدوي، ومحلل ملفات "
               "(CSV / Excel / PDF / TXT) يفرز المعاملات البلدية وغير البلدية ويتحقق منها قبل الإدراج.")
    st.divider()
    ai_panel("intake", "إدخال البيانات والتحليل الذكي", summary, None, ctx)
    st.divider()
    export_bar("intake", "تقرير إدخال المعاملات", ctx, text=summary)


def _intake_report(ctx: AuthContext) -> None:  # بلاغ بصورة مع تحليل بصري وإدخال يدوي
    analysis, image_ok = {}, True
    img = st.file_uploader("📷 إرفاق صورة الموقع الميداني للتحليل البصري",
                           type=["jpg", "jpeg", "png"], key="intake_img")
    if img is not None:
        st.image(img, caption="الصورة المرفقة", width=420)
        cache_key = f"vision2:{img.name}:{img.size}"
        if cache_key not in st.session_state:  # لا نعيد استدعاء الـ API مع كل إعادة تشغيل للصفحة
            with st.spinner("⏳ جاري تحليل الصورة..."):
                st.session_state[cache_key] = analyze_image_json(img.getvalue(), img.type or "image/jpeg", ctx)
        res = st.session_state[cache_key]
        if res.get("error"):
            st.error(res["error"])
        else:
            analysis = res
            _image_analysis_card(res)
            if res["relevant"] is False:
                _pink("⚠️ <b>تنبيه: يبدو أن هذه الصورة لا تخص شأناً بلدياً</b> وربما أُرفقت بالخطأ.<br>"
                      f"السبب: {html.escape(res['reason'] or '—')}<br>يرجى التأكيد قبل المتابعة.")
                image_ok = st.checkbox("أؤكد أن الصورة صحيحة وأرغب بالمتابعة", key=f"confirm:{cache_key}")

    default_subject = (analysis.get("issue") or analysis.get("summary") or "")[:80] if image_ok else ""
    with st.form("new_transaction_form"):
        st.markdown("### 📥 تسجيل معاملة جديدة أو بلاغ ميداني")
        a, b = st.columns(2)
        with a:
            trx_num = st.text_input("رقم المعاملة التلقائي",
                                    value=f"TRX-{datetime.datetime.now():%Y%m%d%H%M%S}")
            subject = st.text_input("موضوع المعاملة / البلاغ", value=default_subject)
            district = st.selectbox("الحي / المنطقة", DISTRICTS)
        with b:
            dept = st.selectbox("القسم المكلف المباشر", DEPARTMENTS)
            priority = st.selectbox("درجة الأهمية", PRIORITIES)
            level = st.selectbox("درجة السرية", ctx.visible_levels)  # لا يتجاوز صلاحيته
        override = st.checkbox("حفظ المعاملة حتى لو صُنّفت غير بلدية (بعد التأكد)")
        submitted = st.form_submit_button("🚀 اعتماد وتخزين المعاملة", width="stretch")

    if not submitted:
        return
    subject, trx_num = subject.strip(), trx_num.strip()
    if len(subject) < 5:
        st.error("موضوع المعاملة مطلوب (5 أحرف على الأقل).")
        return
    if img is not None and not image_ok:
        st.error("أكّد صحة الصورة أولاً أو أزل المرفق.")
        return
    if (load_all_transactions()["رقم المعاملة"] == trx_num).any():
        st.error(f"رقم المعاملة {trx_num} موجود مسبقاً.")
        return
    municipal = True if rule_municipal(subject) else classify_municipal_batch([subject])[0][0]
    if municipal is False and not override:
        _pink("⚠️ <b>تنبيه: تبدو هذه المعاملة غير بلدية.</b><br>إن كنت متأكداً فعلّم خيار "
              "«حفظ المعاملة حتى لو صُنّفت غير بلدية» ثم أعد الاعتماد.")
        return
    today = datetime.date.today()
    db.add_new_transaction({
        "رقم المعاملة": trx_num, "موضوع المعاملة": subject, "الحي": district,
        "نوع الجهة": "بلاغ ميداني ذكي", "اسم الجهة": "قطاع الخدمات والعمليات",
        "القسم المكلف": dept, "درجة الأهمية": priority, "السرية": level,
        "الحالة": STATUS_FIELD, "تاريخ التسجيل": str(today),
        "تاريخ الإغلاق المتوقع": str(today + datetime.timedelta(days=3)),
        "سبب عدم الإغلاق": "تحت المعالجة الميدانية",
    })
    audit("transaction_created", ctx, trx=trx_num, level=level, municipal=municipal)
    st.success(f"🎉 تم حفظ المعاملة رقم {trx_num}")


# ---------- محلل الملفات ----------
def _intake_files(ctx: AuthContext) -> None:  # محلل الملفات (CSV/Excel/PDF/TXT)
    st.markdown("#### 📂 محلل الملفات: استخراج المعاملات وفرزها والتحقق منها")
    st.caption("الجداول (CSV / Excel) تُقرأ مباشرة، والمستندات (PDF / TXT) يستخرج منها GPT-4o المعاملات. "
               "أسماء الأعمدة المقبولة: رقم المعاملة، الموضوع، الحي، القسم، الأهمية، السرية "
               "(الموضوع وحده هو المطلوب).")
    files = st.file_uploader("أرفق ملفاً أو أكثر", type=["csv", "xlsx", "pdf", "txt"],
                             accept_multiple_files=True, key="intake_files")
    key = f"import:{ctx.role}:{ctx.username}"
    if files and st.button("🔍 تحليل الملفات", key=f"{key}:go", width="stretch"):
        with st.spinner("⏳ جاري القراءة والتحقق والتصنيف..."):
            st.session_state[key] = _analyze_files(files, ctx)
        audit("files_analyzed", ctx, count=len(files))
    result = st.session_state.get(key)
    if result is not None:
        _show_import_result(result, ctx, key)


def _read_uploaded(f):  # يُرجع (جدول أو None, نص أو None)
    """يُرجع (جدول أو None, نص أو None)."""
    data, name = f.getvalue(), f.name.lower()
    if name.endswith(".csv"):
        for enc in ("utf-8-sig", "cp1256"):
            try:
                return pd.read_csv(io.BytesIO(data), encoding=enc), None
            except UnicodeDecodeError:
                continue
        raise ValueError("ترميز الملف غير مدعوم")
    if name.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(data)), None
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return None, "\n".join((p.extract_text() or "") for p in reader.pages[:30])
    for enc in ("utf-8-sig", "cp1256"):
        try:
            return None, data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("ترميز النص غير مدعوم")


def _analyze_files(files, ctx: AuthContext) -> dict:  # يستخرج المعاملات من الملفات ويصنفها
    notes, frames = [], []
    for f in files:
        try:
            table, text = _read_uploaded(f)
            if table is not None:
                table = normalize_columns(table)
                if "موضوع المعاملة" not in table:
                    notes.append(f"❌ {f.name}: لم أجد عمود «موضوع المعاملة» (أو الموضوع / الوصف).")
                    continue
            else:
                items = extract_transactions_ai(text or "", ctx)
                if not items:
                    notes.append(f"⚠️ {f.name}: لم تُستخرج معاملات من النص.")
                    continue
                table = pd.DataFrame(items).rename(columns={"municipal": "_municipal", "reason": "_reason"})
            table["المصدر"] = f.name
            frames.append(table)
        except ImportError as e:
            notes.append(f"❌ {f.name}: مكتبة ناقصة ({e}). ثبّتها: pip install openpyxl pypdf")
        except Exception as e:
            notes.append(f"❌ {f.name}: تعذّرت القراءة ({e})")
    if not frames:
        return {"df": pd.DataFrame(), "notes": notes}
    raw = pd.concat(frames, ignore_index=True)
    if len(raw) > MAX_IMPORT_ROWS:
        notes.append(f"⚠️ تم تحليل أول {MAX_IMPORT_ROWS:,} صف فقط من {len(raw):,}.")
        raw = raw.head(MAX_IMPORT_ROWS)
    existing = set(load_all_transactions()["رقم المعاملة"].astype(str))
    clean = validate_import(raw, ctx.visible_levels, existing)
    return {"df": apply_municipal_flags(clean, classify_municipal_batch), "notes": notes}


def _show_import_result(result: dict, ctx: AuthContext, key: str) -> None:  # يعرض نتيجة الفحص قبل الإدراج
    for note in result["notes"]:
        st.warning(note)
    df = result["df"]
    if df.empty:
        st.info("لا توجد معاملات للتحليل.")
        return

    total = len(df)
    municipal = int((df["تخص البلدية"] == "نعم").sum())
    other = int((df["تخص البلدية"] == "لا").sum())
    unknown = total - municipal - other
    valid = int((df["حالة التحقق"] == "صالحة").sum())
    rejected = int((df["حالة التحقق"] == "مرفوضة").sum())
    cols = st.columns(5)
    cols[0].metric("إجمالي المعاملات", f"{total:,}")
    cols[1].metric("تخص البلدية ✅", f"{municipal:,}")
    cols[2].metric("لا تخص البلدية ⚠️", f"{other:,}")
    cols[3].metric("صالحة", f"{valid:,}")
    cols[4].metric("مرفوضة", f"{rejected:,}")
    if other:
        _pink(f"⚠️ <b>{other:,}</b> معاملة لا تخص البلدية وربما أُدرجت بالخطأ، وستُستبعد من الإدراج.")
    if unknown:
        st.info(f"{unknown:,} معاملة غير مصنّفة (تجاوزت حد التصنيف الذكي أو تعذّر الاتصال)، وستُستبعد من الإدراج.")

    choice = st.radio("عرض:", list(_RESULT_FILTERS), horizontal=True, key=f"{key}:view")
    shown = _RESULT_FILTERS[choice](df).drop(columns=["_municipal", "_reason"], errors="ignore")
    st.dataframe(shown, width="stretch", height=380)
    export_bar("intake_import", "تقرير تحليل ملفات المعاملات", ctx, df=shown,
               text=f"إجمالي {total:,} | بلدية {municipal:,} | غير بلدية {other:,} | صالحة {valid:,} | مرفوضة {rejected:,}")

    include_review = st.checkbox("إدراج المعاملات التي تحتاج مراجعة أيضاً", key=f"{key}:review")
    statuses = ["صالحة"] + (["تحتاج مراجعة"] if include_review else [])
    to_insert = df[(df["تخص البلدية"] == "نعم") & df["حالة التحقق"].isin(statuses)]
    st.markdown(f"سيتم إدراج **{len(to_insert):,}** معاملة (بلدية وسليمة).")
    confirmed = st.checkbox("راجعت النتائج وأؤكد الإدراج", key=f"{key}:confirm")
    if st.button("📥 إدراج المعاملات في النظام", key=f"{key}:insert", width="stretch",
                 disabled=not confirmed or to_insert.empty):
        added, failed = _insert_import_rows(to_insert, ctx)
        st.success(f"✅ تم إدراج {added:,} معاملة." + (f" تعذّر إدراج {failed:,}." if failed else ""))
        st.session_state[key] = None  # يمنع الإدراج المكرر عند الضغط مرة أخرى


def _insert_import_rows(df: pd.DataFrame, ctx: AuthContext) -> tuple:  # يدرج الصفوف السليمة في القاعدة
    today = datetime.date.today()
    added = failed = 0
    for rec in df.to_dict("records"):
        try:
            db.add_new_transaction({
                "رقم المعاملة": rec["رقم المعاملة"], "موضوع المعاملة": rec["موضوع المعاملة"],
                "الحي": rec["الحي"], "نوع الجهة": "استيراد ملف", "اسم الجهة": "قطاع الخدمات والعمليات",
                "القسم المكلف": rec["القسم المكلف"], "درجة الأهمية": rec["درجة الأهمية"],
                "السرية": rec["السرية"], "الحالة": STATUS_FIELD, "تاريخ التسجيل": str(today),
                "تاريخ الإغلاق المتوقع": str(today + datetime.timedelta(days=3)),
                "سبب عدم الإغلاق": "تحت المعالجة الميدانية",
            })
            added += 1
        except Exception:
            failed += 1
    audit("bulk_import", ctx, added=added, failed=failed)
    return added, failed


# ======================================================
# التبويب 3: غرفة العمليات والإنذارات (+ إرسال تنبيه باعتماد المدير)
# ======================================================
_ALERTS_FILE = Path("alerts.json")


_ALERT_SEVERITIES = ["منخفضة", "متوسطة", "عالية", "حرجة"]


_ALERT_PENDING, _ALERT_SENT, _ALERT_REJECTED = "بانتظار الاعتماد", "مُرسل", "مرفوض"


def _load_alerts() -> list:  # يقرأ الإنذارات المحفوظة
    try:
        return json.loads(_ALERTS_FILE.read_text(encoding="utf-8")) if _ALERTS_FILE.exists() else []
    except (ValueError, OSError):
        return []


def _save_alerts(items: list) -> None:  # يحفظ الإنذارات في الملف
    _ALERTS_FILE.write_text(json.dumps(items[-500:], ensure_ascii=False, indent=1), encoding="utf-8")


def _alert_html(a: dict) -> str:  # يبني بطاقة إنذار للعرض
    icon = _SEVERITY_ICON.get(a["severity"], "")
    return (f"{icon} <b>{html.escape(a['title'])}</b> — الجهة: {html.escape(a['target'])} | "
            f"الخطورة: {html.escape(a['severity'])}<br>{html.escape(a['message'])}<br>"
            f"<span style='opacity:.7'>بواسطة {html.escape(a['by'])} — {html.escape(a['at'])}</span>")


def _alerts_center(ctx: AuthContext) -> list:  # مركز الإنذارات والاعتماد والإرسال
    st.markdown("#### 📣 مركز التنبيهات")
    alerts = _load_alerts()
    if not ctx.logged_in:
        card("🔒 عرض التنبيهات وإرسالها يتطلبان تسجيل الدخول.", "warn")
        return []

    for a in [x for x in alerts if x["status"] == _ALERT_SENT][-3:][::-1]:
        (_pink if a["severity"] in ("عالية", "حرجة") else lambda b: card(b, "banner"))(_alert_html(a))

    with st.form("alert_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        target = c1.selectbox("الجهة المستهدفة", DEPARTMENTS)
        severity = c2.selectbox("درجة الخطورة", _ALERT_SEVERITIES, index=1)
        title = st.text_input("عنوان التنبيه")
        message = st.text_area("نص التنبيه", height=80)
        submitted = st.form_submit_button("📨 رفع التنبيه للاعتماد", width="stretch")
    if submitted:
        if len(title.strip()) < 3 or len(message.strip()) < 5:
            st.error("اكتب عنواناً ونصاً واضحين للتنبيه.")
        else:
            alerts.append({"id": datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"),
                           "title": title.strip()[:100], "message": message.strip()[:600],
                           "target": target, "severity": severity, "by": ctx.username or "-",
                           "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                           "status": _ALERT_PENDING})
            _save_alerts(alerts)
            audit("alert_submitted", ctx, target=target, severity=severity)
            st.success("تم رفع التنبيه، ولن يُرسل قبل اعتماد المدير.")

    pending = [a for a in alerts if a["status"] == _ALERT_PENDING]
    if ctx.role == "admin":
        st.markdown(f"##### ✅ تنبيهات بانتظار اعتمادك ({len(pending)})")
        for a in pending:
            card(_alert_html(a), "warn")
            ok = st.checkbox("أؤكد صحة التنبيه واعتماده للإرسال", key=f"al_ok:{a['id']}")
            b1, b2 = st.columns(2)
            if b1.button("✅ اعتماد وإرسال", key=f"al_send:{a['id']}", disabled=not ok, width="stretch"):
                a.update(status=_ALERT_SENT, approved_by=ctx.username,
                         sent_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                _save_alerts(alerts)
                audit("alert_sent", ctx, target=a["target"], severity=a["severity"], id=a["id"])
                st.rerun()
            if b2.button("❌ رفض", key=f"al_rej:{a['id']}", width="stretch"):
                a["status"] = _ALERT_REJECTED
                _save_alerts(alerts)
                audit("alert_rejected", ctx, id=a["id"])
                st.rerun()
    elif pending:
        st.info(f"لديك/لدى الفريق {len(pending)} تنبيه بانتظار اعتماد المدير.")
    return alerts


def _hex_rgb(color: str) -> list:  # #rrggbb ← [r, g, b] (تحتاجها طبقات الخريطة)
    """#rrggbb ← [r, g, b] (تحتاجها طبقات الخريطة)."""
    return [int(color[i:i + 2], 16) for i in (1, 3, 5)]


def _map_legend() -> None:  # مفتاح ألوان الخريطة
    """مفتاح ألوان الخريطة."""
    st.markdown("".join(
        f'<span class="badge-status" style="background:{color}22;border:1px solid {color};color:{color};">● {label}</span>'
        for _k, label, color in _BUCKET_LEGEND), unsafe_allow_html=True)


_ESRI_IMG = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


_ESRI_LBL = "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"


_ESRI_ROAD = "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}"


def _sat_map(pts: pd.DataFrame, key: str, height: int, heat: bool) -> bool:  # خريطة أقمار صناعية عالية الدقة (صور Esri World Imagery + أسماء الشوارع والأحيا
    """خريطة أقمار صناعية عالية الدقة (صور Esri World Imagery + أسماء الشوارع والأحياء) بلا مفتاح.
    تلميح عند المرور، وبطاقة تفاصيل عند الضغط. ترجع False إن لم يدعمها إصدار plotly لتُستخدم الخريطة الداكنة."""
    import plotly.graph_objects as go
    new = hasattr(go, "Scattermap")  # plotly >= 5.24 (MapLibre) وإلا النسخة القديمة
    Scatter = go.Scattermap if new else go.Scattermapbox
    Density = getattr(go, "Densitymap", None) if new else getattr(go, "Densitymapbox", None)
    data = pts.copy()
    for col in ("trx", "subject", "district", "dept", "status", "priority"):
        data[col] = data[col].map(lambda x: html.escape(str(x)))  # نص آمن داخل التلميح
    layers = [{"below": "traces", "sourcetype": "raster", "source": [_ESRI_IMG], "sourceattribution": "Esri, Maxar, Earthstar Geographics"},
              {"below": "traces", "sourcetype": "raster", "source": [_ESRI_ROAD], "opacity": 0.85},
              {"below": "traces", "sourcetype": "raster", "source": [_ESRI_LBL]}]
    fig = go.Figure()
    if heat and Density is not None:
        fig.add_trace(Density(lat=data["lat"], lon=data["lon"], z=[1] * len(data), radius=26, opacity=0.8,
                              colorscale=[[0, "rgba(0,0,0,0)"], [0.25, "#22d3ee"], [0.55, "#fbbf24"], [1, "#f43f5e"]], showscale=False,
                              hoverinfo="skip"))
    else:
        crit = data[(data["bucket"] == "open") & (data["priority"] == "حرج للغاية")]
        if not crit.empty:  # هالة حمراء حول الحرج غير المنجز
            fig.add_trace(Scatter(lat=crit["lat"], lon=crit["lon"], mode="markers", marker=dict(size=24, color="#f43f5e", opacity=0.35),
                                  hoverinfo="skip", showlegend=False))
        for key_, label, color in _BUCKET_LEGEND:
            d = data[data["bucket"] == key_]
            if d.empty:
                continue
            hover = ("<b>" + d["trx"].astype(str) + "</b><br>" + d["subject"].astype(str).str.slice(0, 70) + "<br>📍 " +
                     d["district"].astype(str) + " · " + d["dept"].astype(str) + "<br>الحالة: " + d["status"].astype(str) +
                     " · الأهمية: " + d["priority"].astype(str))
            fig.add_trace(Scatter(lat=d["lat"], lon=d["lon"], mode="markers", name=label, marker=dict(size=10, color=color, opacity=0.95),
                                  text=hover, hovertemplate="%{text}<extra></extra>",
                                  customdata=d[["trx", "subject", "district", "dept", "status", "priority"]].values))
    geo = dict(style="white-bg", layers=layers, center=dict(lat=21.58, lon=39.17), zoom=10.4)
    fig.update_layout(**({"map": geo} if new else {"mapbox": geo}), height=height, margin=dict(l=0, r=0, t=0, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=0.01, x=0.01, bgcolor="rgba(5,12,24,.7)",
                                                                  font=dict(color="#e2e8f0")),
                      hoverlabel=dict(bgcolor="rgba(10,16,32,.96)", font=dict(color="#f1f5f9", size=13)))
    sel = None
    try:
        ev = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key=f"{key}:sat",
                             config={"scrollZoom": True, "displaylogo": False})
        pts_sel = (ev.selection.points if ev and ev.selection else None) or []
        if pts_sel and pts_sel[0].get("customdata"):
            c = pts_sel[0]["customdata"]
            sel = dict(zip(("trx", "subject", "district", "dept", "status", "priority"), c))
    except TypeError:
        st.plotly_chart(fig, width="stretch", config={"scrollZoom": True, "displaylogo": False})
    if sel:
        card(f"<b>📍 {html.escape(str(sel.get('trx', '')))}</b> — {html.escape(str(sel.get('subject', '')))}<br>"
             f"{html.escape(str(sel.get('district', '')))} · {html.escape(str(sel.get('dept', '')))}<br>"
             f"الحالة: <b>{html.escape(str(sel.get('status', '')))}</b> · الأهمية: <b>{html.escape(str(sel.get('priority', '')))}</b>", "ai")
    return True


def _geo_map(pts: pd.DataFrame, key: str, height: int = 540) -> None:  # خريطة تفاعلية (pydeck): تلميح عند المرور بالفأرة باسم المعاملة، وبطاقة تفاصيل 
    """خريطة تفاعلية (pydeck): تلميح عند المرور بالفأرة باسم المعاملة، وبطاقة تفاصيل عند الضغط، ونمط كثافة حرارية."""
    if pts.empty:
        st.info("لا توجد نقاط مطابقة للاختيار.")
        return
    import pydeck as pdk  # يأتي مع Streamlit

    data = pts.copy()
    for col in ("trx", "subject", "district", "dept", "status", "priority"):
        data[col] = data[col].map(html.escape)  # نص آمن داخل التلميح
    data["fill"] = data["color"].map(lambda c: [*_hex_rgb(c), 220])  # لون النقطة RGBA
    data["radius"] = data["bucket"].map({"open": 170, "progress": 150, "done": 130}).fillna(140)  # الأخطر أكبر
    c_a, c_b = st.columns(2)
    base = c_a.radio("الخريطة", ["🛰️ أقمار صناعية عالية الدقة", "🌑 مجسّمة داكنة (3D)"], horizontal=True, key=f"{key}:base")
    mode = c_b.radio("النمط", ["🔵 النقاط (مع التلميح)", "🔥 الكثافة الحرارية"], horizontal=True, key=f"{key}:mode")
    heat = mode.startswith("🔥")
    if base.startswith("🛰️"):
        try:
            if _sat_map(pts, key, height, heat):
                return
        except Exception as exc:  # إصدار plotly لا يدعمها أو لا اتصال بالإنترنت: نرجع للداكنة
            st.caption(f"تعذّر عرض الأقمار الصناعية ({exc.__class__.__name__}) — عُرضت الخريطة الداكنة.")
    if heat:
        layers = [pdk.Layer("HeatmapLayer", id="heat", data=data, get_position="[lon, lat]", get_weight=1,
                            radius_pixels=55, opacity=0.9)]
    else:
        layers = []
        crit = data[(data["bucket"] == "open") & (data["priority"] == html.escape("حرج للغاية"))]
        if not crit.empty:  # حلقة تنبيه حول الحرج غير المنجز
            layers.append(pdk.Layer("ScatterplotLayer", id="ring", data=crit, get_position="[lon, lat]",
                                    get_radius=420, stroked=True, filled=False, get_line_color=[244, 63, 94, 210],
                                    line_width_min_pixels=2, radius_min_pixels=9, radius_max_pixels=26))
        layers.append(pdk.Layer("ScatterplotLayer", id="pts", data=data, get_position="[lon, lat]",
                                get_fill_color="fill", get_radius="radius", radius_min_pixels=4, radius_max_pixels=13,
                                pickable=True, auto_highlight=True, highlight_color=[255, 255, 255, 235],
                                stroked=True, get_line_color=[10, 16, 32, 255], line_width_min_pixels=1))
    tooltip = None if heat else {
        "html": ("<div style='direction:rtl;text-align:right;line-height:1.7'>"
                 "<b style='color:#67e8f9'>{trx}</b><br/><b>{subject}</b><br/>"
                 "📍 {district} · {dept}<br/>الحالة: <b>{status}</b> · الأهمية: <b>{priority}</b></div>"),
        "style": {"backgroundColor": "rgba(10,16,32,.96)", "color": "#f1f5f9", "border": "1px solid #22d3ee",
                  "borderRadius": "12px", "fontFamily": "IBM Plex Sans Arabic, Tahoma, sans-serif",
                  "fontSize": "13px", "padding": "8px 12px", "maxWidth": "340px"}}
    deck = pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=21.60, longitude=39.17, zoom=10.2, pitch=35),
                    tooltip=tooltip, map_provider="carto", map_style="dark")
    selected = None
    try:  # الضغط على نقطة (يتطلب إصداراً حديثاً من Streamlit)
        event = st.pydeck_chart(deck, height=height, on_select="rerun", selection_mode="single-object", key=f"{key}:deck")
        objs = (event.selection.objects or {}).get("pts") if event and event.selection else None
        selected = objs[0] if objs else None
    except TypeError:
        st.pydeck_chart(deck, height=height)
    if selected:
        card(f"<b>📍 {selected.get('trx', '')}</b> — {selected.get('subject', '')}<br>"
             f"{selected.get('district', '')} · {selected.get('dept', '')}<br>"
             f"الحالة: <b>{selected.get('status', '')}</b> · الأهمية: <b>{selected.get('priority', '')}</b>", "ai")


_STRIP_HTML = """<!doctype html><html dir="rtl" lang="ar"><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;font-family:'IBM Plex Sans Arabic',Tahoma,sans-serif;color:#e2e8f0;background:transparent}
.bar{display:flex;justify-content:space-between;align-items:center;font-size:.85rem;color:#94a3b8;margin:2px 4px 10px}
.bar b{color:#e2e8f0}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#10b981;margin-left:8px;
animation:p 1.6s infinite}@keyframes p{0%{box-shadow:0 0 0 0 rgba(16,185,129,.7)}70%{box-shadow:0 0 0 10px rgba(16,185,129,0)}100%{box-shadow:0 0 0 0 rgba(16,185,129,0)}}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:10px}
.c{border-radius:16px;padding:12px 14px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05)}
.c span{display:block;font-size:.78rem;color:#94a3b8}.c b{font-size:1.9rem;font-weight:800;letter-spacing:.5px}
.danger{border-color:rgba(244,63,94,.5)}.danger b{color:#fb7185}.warn{border-color:rgba(245,158,11,.5)}.warn b{color:#fbbf24}
.info{border-color:rgba(34,211,238,.5)}.info b{color:#67e8f9}.ok{border-color:rgba(16,185,129,.5)}.ok b{color:#34d399}
.row{display:grid;grid-template-columns:auto 1.2fr 2fr 1.4fr;gap:10px;align-items:center;padding:9px 12px;margin-bottom:7px;
border-radius:14px;border:1px solid rgba(255,255,255,.1);background:rgba(15,23,42,.7);font-size:.85rem;animation:in .5s ease}
@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.badge{padding:2px 10px;border-radius:999px;font-size:.75rem;font-weight:700;white-space:nowrap}
.red{background:rgba(244,63,94,.18);color:#fda4af;border:1px solid rgba(244,63,94,.5)}
.amb{background:rgba(245,158,11,.18);color:#fcd34d;border:1px solid rgba(245,158,11,.5)}
.grn{background:rgba(16,185,129,.18);color:#6ee7b7;border:1px solid rgba(16,185,129,.5)}
.sub{color:#94a3b8}.meter{height:6px;border-radius:6px;background:rgba(255,255,255,.1);margin-top:5px;overflow:hidden}
.meter i{display:block;height:100%;background:linear-gradient(90deg,#22d3ee,#10b981)}
@media(max-width:700px){.grid{grid-template-columns:repeat(2,1fr)}.row{grid-template-columns:1fr}}
</style><body>
<div class="bar"><span><span class="dot"></span><b id="t"></b></span><span>آخر تحديث <b id="clk">--:--:--</b> · يتجدد تلقائياً</span></div>
<div class="grid" id="g"></div><div id="r"></div>
<script>
const D=__DATA__;document.getElementById('t').textContent=D.title;
const g=document.getElementById('g');
D.kpis.forEach(k=>{const c=document.createElement('div');c.className='c '+k.k;
 const l=document.createElement('span');l.textContent=k.label;const b=document.createElement('b');c.append(l,b);g.append(c);
 const end=Number(k.val),t0=performance.now();(function f(n){const q=Math.min(1,(n-t0)/900);
 b.textContent=Math.round(end*q).toLocaleString('en-US')+(k.suf||'');if(q<1)requestAnimationFrame(f)})(t0)});
const R=document.getElementById('r'),N=D.rows.length;let o=0;
function show(){R.textContent='';for(let i=0;i<Math.min(D.show,N);i++){const x=D.rows[(o+i)%N];
 const w=document.createElement('div');w.className='row';
 const bd=document.createElement('span');bd.className='badge '+x.cls;bd.textContent=x.badge;
 const a=document.createElement('div');const ab=document.createElement('b');ab.textContent=x.title;a.append(ab);
 if(x.pct!=null){const m=document.createElement('div');m.className='meter';const iI=document.createElement('i');iI.style.width=Math.max(2,x.pct)+'%';m.append(iI);a.append(m)}
 const c=document.createElement('div');c.textContent=x.sub;const d=document.createElement('div');d.className='sub';d.textContent=x.meta;
 w.append(bd,a,c,d);R.append(w)}o=(o+D.show)%Math.max(N,1)}
if(N){show();setInterval(show,D.every*1000)}
setInterval(()=>{document.getElementById('clk').textContent=new Date().toLocaleTimeString('en-GB')},1000);
</script></body></html>"""


def _live_strip(title: str, kpis: list, rows: list, show: int = 5, every: int = 5) -> None:  # شريط حيّ يعمل بالكامل في المتصفح (JavaScript): يدوّر الصفوف ويحدّث الساعة دون 
    """شريط حيّ يعمل بالكامل في المتصفح (JavaScript): يدوّر الصفوف ويحدّث الساعة دون أي إعادة تشغيل للصفحة.
    ملاحظة: هذا بديل st.fragment(run_every) الذي كان يقاطع تسجيل المساعد الصوتي."""
    data = json.dumps({"title": title, "kpis": kpis, "rows": rows, "show": show, "every": every},
                      ensure_ascii=False).replace("</", "<\\/")
    height = 150 + min(show, max(len(rows), 1)) * 58
    _frame(_STRIP_HTML.replace("__DATA__", data), height)


def _live_ops(df: pd.DataFrame) -> None:  # مؤشرات غرفة العمليات الحية: تُحسب من البيانات الحقيقية ثم تُعرض في شريط حيّ
    """مؤشرات غرفة العمليات الحية: تُحسب من البيانات الحقيقية ثم تُعرض في شريط حيّ."""
    is_open = df["الحالة"] != STATUS_DONE
    today = pd.Timestamp.today().normalize()
    crit = int((is_open & (df["درجة الأهمية"] == "حرج للغاية")).sum())
    breached = int((is_open & (df["تاريخ الإنجاز المتوقع"] < today)).sum())
    urgent = df[is_open & df["درجة الأهمية"].isin(["عاجل", "حرج للغاية"])]
    hot = urgent["الحي"].astype(str).value_counts()
    hot_name, hot_n = (hot.index[0], int(hot.iloc[0])) if len(hot) else ("—", 0)
    kpis = [{"k": "danger", "label": "🔴 بلاغات حرجة مفتوحة", "val": crit},
            {"k": "warn", "label": "⏱️ تجاوزت مهلة SLA", "val": breached},
            {"k": "info", "label": f"📍 أكثر حي ضغطاً: {hot_name}", "val": hot_n},
            {"k": "ok", "label": "👷 فرق جاهزة بالميدان", "val": len(DEPARTMENTS) * an.TEAMS_PER_DEPT}]
    rows = []
    for r in an.urgent_open(df, limit=60).to_dict("records"):
        due = r.get("تاريخ الإنجاز المتوقع")
        late = f"متأخرة {(today - due).days} يوم" if pd.notna(due) and due < today else "ضمن المهلة"
        crit_row = r.get("درجة الأهمية") == "حرج للغاية"
        rows.append({"badge": str(r.get("درجة الأهمية", "")), "cls": "red" if crit_row else "amb",
                     "title": str(r.get("رقم المعاملة", "")), "sub": str(r.get("موضوع المعاملة", ""))[:70],
                     "meta": f"📍 {r.get('الحي', '')} · {late}"})
    _live_strip("غرفة العمليات — بث مباشر", kpis, rows)


def _teams_live(df: pd.DataFrame, team: pd.Series, stats: pd.DataFrame) -> None:  # شريط الفرق الحيّ: إنجازات كل فريق ومتأخراته وبيئة عمله (الأحياء التي يغطيها وح
    """شريط الفرق الحيّ: إنجازات كل فريق ومتأخراته وبيئة عمله (الأحياء التي يغطيها وحِمله)."""
    if stats.empty:
        return
    today = pd.Timestamp.today().normalize()
    late_mask = (df["الحالة"] != STATUS_DONE) & (df["تاريخ الإنجاز المتوقع"] < today)
    key = df["القسم المكلف"].astype(str) + "|" + team.astype(str)
    late = late_mask.groupby(key).sum()  # متأخرات كل فريق
    area = df.groupby(key)["الحي"].agg(lambda x: x.astype(str).value_counts().index[0])  # حيّه الأبرز
    n_dist = df.groupby(key)["الحي"].nunique()  # عدد الأحياء التي يغطيها
    rows = []
    for _, r in stats.iterrows():
        k = f"{r['القسم المكلف']}|{r['الفريق']}"
        pct = float(r["نسبة الإنجاز"])
        rows.append({"badge": f"{pct:.0f}%", "cls": "grn" if pct >= TARGET_COMPLETION_RATE else "amb" if pct >= TARGET_COMPLETION_RATE / 2 else "red",
                     "title": str(r["اسم الفريق"]), "pct": round(pct, 1),
                     "sub": f"🌍 بيئة العمل: {area.get(k, '—')} + {max(int(n_dist.get(k, 1)) - 1, 0)} أحياء أخرى · حِمل مفتوح {int(r['مفتوحة']):,}",
                     "meta": f"✅ منجز {int(r['منجزة']):,} · ⏰ متأخر {int(late.get(k, 0)):,}"})
    done = int(stats["منجزة"].sum())
    kpis = [{"k": "ok", "label": "✅ إجمالي المنجز", "val": done},
            {"k": "danger", "label": "⏰ إجمالي المتأخر", "val": int(late_mask.sum())},
            {"k": "warn", "label": "📂 معاملات مفتوحة", "val": int(stats["مفتوحة"].sum())},
            {"k": "info", "label": "👷 فرق نشطة", "val": len(stats)}]
    _live_strip("الفرق الميدانية — بث مباشر للأداء والمتأخرات", kpis, rows, show=4, every=5)


def render_gis(df: pd.DataFrame) -> None:  # صفحة العمليات وغرفة GIS
    ctx = get_auth_context()
    st.subheader("🚨 غرفة العمليات والإنذارات الميدانية وخريطة GIS")
    admin = is_admin(ctx)
    if not admin:
        _admin_gate(ctx, "غرفة العمليات الحية وخريطة GIS")
    elif df.empty:
        st.info("لا توجد معاملات مطابقة للفلاتر الحالية.")
    else:
        _live_ops(df)
        pts = an.map_points(df, limit=3500, focus_urgent=True)
        _map_legend()
        st.caption("🗺️ مرّر الفأرة على أي نقطة لترى اسم المعاملة، واضغط عليها لعرض تفاصيلها. "
                   "الحلقة الحمراء حول النقطة = معاملة «حرجة للغاية» غير منجزة. المواقع تقريبية داخل كل حي.")
        _geo_map(pts, "gis")

    st.divider()
    alerts = _alerts_center(ctx)
    if not admin:
        return  # الموظف يرفع التنبيهات فقط؛ التحليل والتصدير للمدير

    top = df["الحي"].value_counts().head(3).to_dict() if not df.empty else {}
    summary = (f"- المعاملات المطابقة للفلاتر: {len(df):,}\n"
               f"- أكثر الأحياء ازدحاماً: {top or 'لا بيانات'}\n"
               f"- التنبيهات المُرسلة: {sum(a['status'] == _ALERT_SENT for a in alerts)} | "
               f"بانتظار الاعتماد: {sum(a['status'] == _ALERT_PENDING for a in alerts)}")
    st.divider()
    ai_panel("gis", "غرفة العمليات والإنذارات", summary, None, ctx)
    st.divider()
    export_bar("gis", "تقرير غرفة العمليات والتنبيهات", ctx, text=summary,
               df=pd.DataFrame(alerts) if alerts else None)


# ======================================================
# التبويب 4: المساعد الذكي (واعٍ بالصلاحيات)
# ======================================================
def render_assistant(df_all: pd.DataFrame, ctx: AuthContext) -> None:  # صفحة المساعد الذكي وصانع الخطابات
    st.subheader("💬 المساعد الذكي وصانع الخطابات")
    if ctx.logged_in:
        card(f"🔓 أنت مسجّل باسم <b>{html.escape(ctx.username)}</b> — "
             f"يصل المساعد إلى المستويات: {'، '.join(ctx.visible_levels)}.", "ok")
    else:
        card("🔒 أنت زائر: يصل المساعد إلى المعاملات العامة فقط.", "warn")

    history = st.session_state.setdefault("chat_history", [])
    for i, m in enumerate(history):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                speak_button(m["content"], key=f"chat_hist_{i}")

    if question := st.chat_input("اسأل عن المعاملات أو اطلب صياغة خطاب رسمي..."):
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("جاري التحليل..."):
                reply = ask_assistant(question, history, ctx, df_all)
            if reply.startswith(("❌", "⚠️")):
                st.error(reply)
            else:
                show_reply(reply, key=f"chat_new_{len(history)}")  # نص + صوت
        history += [{"role": "user", "content": question},
                    {"role": "assistant", "content": reply}]

    if history and st.button("🗑️ مسح المحادثة"):
        st.session_state["chat_history"] = []
        st.rerun()

    last = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), "")
    st.divider()
    if last and not last.startswith(("❌", "⚠️")):
        export_bar("assistant", "خطاب / رد المساعد الذكي", ctx, text=last)
    else:
        st.caption("اطلب من المساعد صياغة خطاب أو تقرير، وستظهر هنا أزرار الطباعة والتنزيل والإرسال الرسمي.")


# ======================================================
# التبويب 5: مركز قيادة الفرق الميدانية
# ======================================================
_BUCKET_LEGEND = (("done", "منجزة", "#10b981"), ("progress", "تحت التنفيذ", "#f59e0b"),
                  ("open", "غير منجزة", "#ef4444"))


def _pink(body: str) -> None:  # الشريط الأحمر الوردي؛ يرجع للأحمر العادي إن لم يُحدَّث ui.py
    """الشريط الأحمر الوردي؛ يرجع للأحمر العادي إن لم يُحدَّث ui.py."""
    try:
        card(body, "pink")
    except KeyError:
        card(body, "warn")


def _image_analysis_card(res: dict) -> None:  # بطاقة نتيجة التحليل البصري
    icon = _SEVERITY_ICON.get(res["severity"], "")
    body = (f"<b>الوصف:</b> {html.escape(res['summary'] or '—')}<br>"
            f"<b>التصنيف:</b> {html.escape(res['category'] or '—')} | "
            f"<b>الخطورة:</b> {icon} {html.escape(res['severity'] or '—')} | "
            f"<b>الثقة:</b> {res['confidence']}%")
    if res["issue"]:
        body += f"<br><b>المشكلة:</b> {html.escape(res['issue'])}"
    card(f"<b>مخرجات التحليل البصري:</b><br>{body}", "ai")
    spoken = (f"{res['summary'] or ''}. التصنيف {res['category'] or 'غير محدد'}، الخطورة {res['severity'] or 'غير محددة'}. "
              f"{('المشكلة: ' + res['issue']) if res['issue'] else ''}")
    _speak_once(spoken, "vis:" + hashlib.md5(spoken.encode()).hexdigest()[:10])  # الرد صوتياً بعد التحليل


def render_field_teams(df: pd.DataFrame, df_all: pd.DataFrame, ctx: AuthContext) -> None:  # صفحة الفرق الميدانية (4 تبويبات)
    st.subheader("👷 مركز قيادة الفرق الميدانية")
    flash = st.session_state.pop("field_flash", None)
    if flash:
        st.success(flash)
    if df.empty:
        st.info("لا توجد معاملات مطابقة للفلاتر الحالية.")
        return

    assignments = load_assignments()
    team = an.assign_teams(df, assignments)
    stats = an.team_stats(df, team)
    if not is_admin(ctx):  # غير المدير: التقرير الميداني فقط، دون خريطة أو أداء أو تكليف
        _admin_gate(ctx, "خريطة الفرق وأداؤها والتكليف")
        st.markdown("#### 📷 التقرير الميداني")
        _field_report(stats, ctx)
        return
    _teams_live(df, team, stats)  # الشريط العلوي الحيّ للفرق
    tab_map, tab_dispatch, tab_report, tab_pred = st.tabs(
        ["🗺️ الخريطة والأداء", "📋 التكليف الذكي", "📷 التقرير الميداني", "🔥 التحليل التنبؤي"])
    with tab_map:
        _field_overview(df, team, stats)
    with tab_dispatch:
        _field_dispatch(df, stats, assignments, ctx)
    with tab_report:
        _field_report(stats, ctx)
    with tab_pred:
        render_predictive(ctx, df_all)  # التبويب الرابع: الاحتياج وخطر التأخر

    # ---- المساعد التقني ----
    counts = an.status_bucket(df["الحالة"]).value_counts()
    urgent_total = int(((df["الحالة"] != STATUS_DONE) & df["درجة الأهمية"].isin(["عاجل", "حرج للغاية"])).sum())
    weakest, strongest = stats.iloc[0], stats.iloc[-1]
    summary = "\n".join([
        f"- عدد الفرق: {len(stats)} | المعاملات: منجزة {int(counts.get('done', 0)):,}، "
        f"تحت التنفيذ {int(counts.get('progress', 0)):,}، غير منجزة {int(counts.get('open', 0)):,}",
        f"- أضعف فريق: {weakest['اسم الفريق']} ({weakest['نسبة الإنجاز']:.1f}%)",
        f"- أقوى فريق: {strongest['اسم الفريق']} ({strongest['نسبة الإنجاز']:.1f}%)",
        f"- المعاملات العاجلة والحرجة المفتوحة: {urgent_total:,}",
        f"- التكليفات المحفوظة: {len(assignments):,}",
    ])
    st.divider()
    ai_panel("field", "الفرق الميدانية", summary, df_all, ctx)
    st.divider()
    export_bar("field", "تقرير الفرق الميدانية", ctx, text=summary,
               df=stats[["اسم الفريق", "الإجمالي", "منجزة", "قيد التنفيذ", "غير المنجزة", "نسبة الإنجاز"]])


def _field_overview(df: pd.DataFrame, team: pd.Series, stats: pd.DataFrame) -> None:  # نظرة عامة على أداء الفرق
    counts = an.status_bucket(df["الحالة"]).value_counts()
    c = st.columns(5)
    c[0].metric("الفرق العاملة", f"{len(stats)}")
    c[1].metric("منجزة 🟢", f"{int(counts.get('done', 0)):,}")
    c[2].metric("تحت التنفيذ 🟡", f"{int(counts.get('progress', 0)):,}")
    c[3].metric("غير منجزة 🔴", f"{int(counts.get('open', 0)):,}")
    c[4].metric("أقل نسبة إنجاز", f"{stats.iloc[0]['نسبة الإنجاز']:.1f}%")
    st.caption(f"أضعف فريق حالياً: {stats.iloc[0]['اسم الفريق']}")

    f1, f2 = st.columns(2)
    dept_sel = f1.selectbox("القسم", [ALL_LABEL, *DEPARTMENTS], key="field_dept")
    team_sel = f2.selectbox("الفريق", [ALL_LABEL, *range(1, an.TEAMS_PER_DEPT + 1)], key="field_team")
    pts = an.map_points(df, team, dept=None if dept_sel == ALL_LABEL else dept_sel,
                        team_no=None if team_sel == ALL_LABEL else int(team_sel))
    st.markdown("".join(
        f'<span class="badge-status" style="background:{color}22;border:1px solid {color};color:{color};">'
        f"● {label}: {int(counts.get(key, 0)):,}</span>" for key, label, color in _BUCKET_LEGEND),
        unsafe_allow_html=True)
    if pts.empty:
        st.info("لا توجد نقاط مطابقة للاختيار.")
    else:
        st.caption("🗺️ مرّر الفأرة على أي نقطة (🟢 منجزة / 🟡 تحت التنفيذ / 🔴 غير منجزة) لترى اسم المعاملة، واضغط عليها لعرض تفاصيلها.")
        _geo_map(pts, "field")
        st.caption(f"تعرض الخريطة {len(pts):,} نقطة (عينة ثابتة عند الكثرة)، والمواقع تقريبية داخل كل حي. "
                   "الأعداد أعلاه إجمالية لكل المعاملات.")

    st.markdown("#### 📊 أداء الفرق (من الأضعف إلى الأقوى)")
    st.dataframe(
        stats[["اسم الفريق", "الإجمالي", "منجزة", "قيد التنفيذ", "غير المنجزة", "نسبة الإنجاز"]],
        width="stretch", hide_index=True,
        column_config={"نسبة الإنجاز": st.column_config.ProgressColumn(
            "نسبة الإنجاز", min_value=0, max_value=100, format="%.1f%%")})
    st.caption("توزيع المعاملات على الفرق تجريبي تلقائي إلى أن يُضاف حقل «الفريق» لقاعدة البيانات؛ "
               "والتكليفات التي تحفظها من تبويب «التكليف الذكي» تُطبَّق فوراً.")


def _field_dispatch(df: pd.DataFrame, stats: pd.DataFrame, assignments: dict, ctx: AuthContext) -> None:  # تكليف الفرق بالمعاملات
    if not ctx.logged_in:
        card("🔒 تكليف الفرق يتطلب تسجيل الدخول.", "warn")
        return
    urgent = an.urgent_open(df)
    if urgent.empty:
        st.success("لا توجد معاملات عاجلة أو حرجة مفتوحة 🎉")
    else:
        rows = {f"{r['رقم المعاملة']} — {str(r['موضوع المعاملة'])[:55]}": r for r in urgent.to_dict("records")}
        rec = rows[st.selectbox("المعاملات العاجلة المفتوحة (الأخطر أولاً)", list(rows), key="field_trx")]
        trx, dept = str(rec["رقم المعاملة"]), str(rec["القسم المكلف"])
        card(f"<b>{html.escape(str(rec['موضوع المعاملة']))}</b><br>"
             f"الحي: {html.escape(str(rec['الحي']))} | القسم: {html.escape(dept)} | "
             f"الأهمية: {html.escape(str(rec['درجة الأهمية']))}")
        current = assignments.get(trx)
        if current:
            st.info(f"مكلّف حالياً: {an.team_name(dept, current['team'])} "
                    f"(بواسطة {current['by']} — {current['at']})")
        suggestion = an.suggest_team(stats, dept)
        if suggestion:
            card(f"🤖 <b>الفريق الأنسب:</b> {html.escape(an.team_name(dept, suggestion[0]))} — "
                 f"الأقل حِملاً بين فرق القسم ({suggestion[1]:,} مهمة مفتوحة).", "ai")
        default = suggestion[0] if suggestion else 1
        pick = st.selectbox("الفريق المكلّف", list(range(1, an.TEAMS_PER_DEPT + 1)), index=default - 1,
                            format_func=lambda n: an.team_name(dept, n), key=f"field_pick:{trx}")
        note = st.text_input("ملاحظة للفريق (اختياري)", key=f"field_note:{trx}")
        if st.button("✅ تكليف الفريق", key=f"field_assign:{trx}", width="stretch", disabled=not ctx.can_write):
            save_assignment(trx, pick, dept, note, ctx.username or "-")
            audit("field_assignment", ctx, trx=trx, team=pick)
            st.session_state["field_flash"] = f"تم تكليف {an.team_name(dept, pick)} بالمعاملة {trx}."
            st.rerun()
    if assignments:
        st.markdown("#### 🗂️ آخر التكليفات")
        recent = [{"المعاملة": t, "الفريق": an.team_name(a["dept"], a["team"]), "الملاحظة": a["note"],
                   "بواسطة": a["by"], "الوقت": a["at"]} for t, a in list(assignments.items())[-8:]][::-1]
        st.dataframe(pd.DataFrame(recent), width="stretch", hide_index=True)


def _field_report(stats: pd.DataFrame, ctx: AuthContext) -> None:  # رفع التقرير الميداني بالصورة
    if not ctx.logged_in:
        card("🔒 التقارير الميدانية وتحليل الصور يتطلبان تسجيل الدخول.", "warn")
        return
    source = st.radio("مصدر الصورة", ["📷 التقاط صورة حية", "🖼️ رفع من الجهاز"],
                      horizontal=True, key="field_src")
    live = source.startswith("📷")
    img = (st.camera_input("التقط صورة ميدانية", key="field_cam") if live
           else st.file_uploader("ارفع صورة من الجهاز", type=["jpg", "jpeg", "png"], key="field_up"))

    analysis, image_ok, data, mime = {}, True, None, "image/jpeg"
    if img is not None:
        data, mime = img.getvalue(), img.type or "image/jpeg"
        if not live:
            st.image(img, width=420)
        cache_key = f"vision3:{hashlib.md5(data).hexdigest()}"
        if cache_key not in st.session_state:  # يُحلَّل تلقائياً مرة واحدة لكل صورة
            with st.spinner("⏳ جاري التحليل البصري..."):
                st.session_state[cache_key] = analyze_image_json(data, mime, ctx)
        res = st.session_state[cache_key]
        if res.get("error"):
            st.error(res["error"])
        else:
            analysis = res
            _image_analysis_card(res)
            if res["relevant"] is False:
                _pink("⚠️ <b>غير متعلق بالعمل البلدي</b><br>"
                      f"ما ظهر في الصورة: {html.escape(res['summary'] or '—')}<br>"
                      f"السبب: {html.escape(res['reason'] or '—')} | ثقة التحليل: {res['confidence']}%<br>"
                      "ربما أُرفقت بالخطأ، يرجى التأكيد قبل الحفظ.")
                image_ok = st.checkbox("أؤكد أن الصورة صحيحة وأرغب بالمتابعة", key=f"confirm:{cache_key}")

    with st.form("field_report_form"):
        team_pick = st.selectbox("الفريق", sorted(stats["اسم الفريق"]))
        trx = st.text_input("رقم المعاملة المرتبطة (اختياري)")
        note = st.text_area("ملاحظات الفريق", height=80)
        submitted = st.form_submit_button("💾 حفظ التقرير الميداني", width="stretch")
    if submitted:
        if not ctx.can_write:
            st.error("حسابك للقراءة فقط ولا يمكنه حفظ التقارير.")
        elif data is None:
            st.error("أرفق صورة أولاً.")
        elif not image_ok:
            st.error("أكّد صحة الصورة أولاً أو استبدلها.")
        else:
            name = save_field_report(data, "png" if mime.endswith("png") else "jpg", {
                "team": team_pick, "trx": trx.strip(), "note": note.strip()[:500], "by": ctx.username,
                "relevant": analysis.get("relevant"), "category": analysis.get("category", ""),
                "severity": analysis.get("severity", ""), "summary": analysis.get("summary", "")})
            audit("field_report", ctx, team=team_pick, trx=trx.strip(), file=name)
            st.success(f"✅ تم حفظ التقرير ({name}).")

    reports = load_field_reports()
    if reports:
        st.markdown("#### 🗂️ آخر التقارير الميدانية")
        for col, rep in zip(st.columns(4), reports[:4]):
            path = Path("field_reports") / rep["file"]
            if path.exists():
                col.image(str(path), width="stretch")
            col.caption(f"{rep.get('team', '')} | {rep.get('trx') or '—'}\n{str(rep.get('summary', ''))[:60]}")


# ======================================================
# تبويب الخطابات الرسمية + التقرير التنفيذي الشهري
# ======================================================
_LETTER_TYPES = {
    "إشعار بإنجاز معاملة": "إشعار رسمي بإنجاز المعاملة",
    "اعتذار عن تأخير معاملة": "خطاب اعتذار مهذب عن التأخير مع بيان السبب وموعد الإنجاز الجديد إن ذُكر",
    "رد على استفسار": "رد رسمي على استفسار مستفيد",
    "إحالة لجهة مختصة": "خطاب إحالة معاملة إلى جهة مختصة لاتخاذ اللازم",
    "خطاب مخصص": "خطاب رسمي حسب النقاط المعطاة",
}


_LETTER_ROLE = ("أنت كاتب خطابات رسمية في أمانة محافظة جدة. اكتب الخطاب بالعربية الفصحى الرسمية السعودية: ابدأ بـ«السلام عليكم "
                "ورحمة الله وبركاته» بعد صيغة المخاطبة، ثم الموضوع في فقرات قصيرة، واختم بـ«وتقبلوا خالص تحياتي وتقديري». "
                "استخدم المعلومات المعطاة فقط، ولا تخترع أرقاماً أو تواريخ أو أسماء. لا تكتب الترويسة ولا الرقم ولا التاريخ "
                "(تضاف تلقائياً)، ولا التوقيع، اكتب نص الخطاب فقط.")


def _month_stats(df: pd.DataFrame, year: int, month: int) -> dict:  # أرقام الشهر: المستلم والمنجز والمتأخر وأداء الأقسام وأكثر الأحياء
    """أرقام الشهر: المستلم والمنجز والمتأخر وأداء الأقسام وأكثر الأحياء."""
    rec = df["تاريخ الاستلام"]
    m = df[(rec.dt.year == year) & (rec.dt.month == month)]
    today = pd.Timestamp.today().normalize()
    done = m["الحالة"] == STATUS_DONE
    late = (~done) & (m["تاريخ الإنجاز المتوقع"] < today)
    dept = (m.assign(_d=done, _l=late).groupby("القسم المكلف", observed=True)
            .agg(المستلم=("رقم المعاملة", "count"), المنجز=("_d", "sum"), المتأخر=("_l", "sum")).reset_index())
    dept["نسبة الإنجاز %"] = (dept["المنجز"] / dept["المستلم"] * 100).round(1)
    return {"received": len(m), "done": int(done.sum()), "late": int(late.sum()),
            "critical": int((m["درجة الأهمية"] == "حرج للغاية").sum()), "dept": dept.sort_values("نسبة الإنجاز %"),
            "districts": m["الحي"].astype(str).value_counts().head(5).to_dict(),
            "backlog": int((df["الحالة"] != STATUS_DONE).sum())}


def render_official(ctx: AuthContext, df_all: pd.DataFrame) -> None:  # الخطابات الرسمية (موظف ومدير) والتقرير التنفيذي الشهري (مدير)
    """الخطابات الرسمية (موظف ومدير) والتقرير التنفيذي الشهري (مدير)."""
    st.subheader("📨 الخطابات الرسمية والتقارير")
    if not ctx.logged_in:
        card("🔒 هذه الصفحة للموظفين والمدير. سجّل الدخول من الشريط الجانبي.", "warn")
        return
    t_letter, t_month = st.tabs(["✉️ خطاب رسمي", "📊 التقرير التنفيذي الشهري"])
    with t_letter:
        c1, c2 = st.columns(2)
        ltype = c1.selectbox("نوع الخطاب", list(_LETTER_TYPES), key="lt_type")
        to = c2.text_input("الجهة المخاطبة", placeholder="مثال: سعادة مدير إدارة التراخيص", key="lt_to")
        subject = st.text_input("الموضوع", key="lt_subject")
        trx = st.text_input("رقم المعاملة المرتبطة (اختياري)", key="lt_trx")
        points = st.text_area("النقاط الأساسية (المعلومات الصحيحة فقط)", key="lt_points", height=120)
        s1, s2 = st.columns(2)
        signer = s1.text_input("اسم الموقِّع", value=ctx.username or "", key="lt_signer")
        title = s2.text_input("صفته الوظيفية", key="lt_title")
        if st.button("🤖 صياغة الخطاب", key="lt_gen", width="stretch"):
            if not (to.strip() and subject.strip() and points.strip()):
                st.warning("أكمل الجهة والموضوع والنقاط.")
            else:
                with st.spinner("يصيغ الخطاب..."):
                    body = ask_sovereign_ai(f"نوع الخطاب: {_LETTER_TYPES[ltype]}\nالمخاطَب: {to}\nالموضوع: {subject}\n"
                                            f"رقم المعاملة: {trx or 'لا يوجد'}\nالنقاط:\n{points}", "", _LETTER_ROLE)
                st.session_state["lt_body"] = body
        body = st.text_area("نص الخطاب (يمكنك تعديله قبل الإصدار)", key="lt_body", height=260)
        if body and not body.startswith(("❌", "⚠️")) and st.button("🧾 إصدار برقم صادر وتصدير PDF", key="lt_issue", width="stretch"):
            no = next_outgoing_no()
            today = datetime.date.today()
            head = (f"الرقم: {no}\nالتاريخ: {hijri_text(today)} (تقريبي) الموافق {today:%Y-%m-%d}م\n"
                    f"إلى: {to}\nالموضوع: {subject}\n" + (f"المعاملة: {trx}\n" if trx else "") + "\n")
            tail = f"\n\n{signer}\n{title}"
            try:
                st.session_state["lt_pdf"] = (no, pdf_bytes(f"خطاب رسمي — {subject}", no, ctx, text=head + body + tail,
                                                            classification="رسمي"))
                audit("letter_issued", ctx, number=no)
            except Exception as exc:
                st.error(f"تعذّر إنشاء PDF: {exc}")
        if st.session_state.get("lt_pdf"):
            no, data = st.session_state["lt_pdf"]
            st.success(f"صدر الخطاب برقم {no}")
            st.download_button("⬇️ تحميل الخطاب PDF", data, file_name=f"letter_{no.replace('/', '-')}.pdf",
                               mime="application/pdf", key="lt_dl")
    with t_month:
        if not is_admin(ctx):
            _admin_gate(ctx, "التقرير التنفيذي الشهري")
            return
        today = datetime.date.today()
        c1, c2 = st.columns(2)
        year = c1.number_input("السنة", 2020, today.year, today.year, key="mr_year")
        month = c2.selectbox("الشهر", list(range(1, 13)), index=today.month - 1, key="mr_month")
        stats = _month_stats(df_all, int(year), int(month))
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("المستلم", f"{stats['received']:,}")
        k2.metric("المنجز", f"{stats['done']:,}")
        k3.metric("المتأخر", f"{stats['late']:,}")
        k4.metric("حرجة للغاية", f"{stats['critical']:,}")
        st.dataframe(stats["dept"], hide_index=True, width="stretch")
        if st.button("🤖 صياغة الملخص التنفيذي", key="mr_gen", width="stretch"):
            ctx_txt = (f"الشهر {int(month)}/{int(year)}: مستلم {stats['received']}، منجز {stats['done']}، متأخر {stats['late']}، "
                       f"حرجة {stats['critical']}، المتراكم الكلي المفتوح {stats['backlog']}.\nأكثر الأحياء: {stats['districts']}\n"
                       f"أداء الأقسام:\n{stats['dept'].to_string(index=False)}")
            with st.spinner("يكتب الملخص..."):
                st.session_state["mr_text"] = ask_sovereign_ai(
                    "اكتب ملخصاً تنفيذياً رسمياً للمحافظ بالعربية: أبرز المؤشرات، الأقسام الأقوى والأضعف، المخاطر، "
                    "وثلاث توصيات عملية. التزم بالأرقام المعطاة ولا تخترع غيرها.", ctx_txt)
        txt = st.text_area("الملخص التنفيذي (قابل للتعديل)", key="mr_text", height=240)
        if txt and not txt.startswith(("❌", "⚠️")):
            try:
                pdf = pdf_bytes(f"التقرير التنفيذي — {int(month)}/{int(year)}", f"RPT-{int(year)}{int(month):02d}", ctx,
                                text=f"التاريخ: {hijri_text(today)} (تقريبي) الموافق {today:%Y-%m-%d}م\n\n{txt}",
                                df=stats["dept"], classification="سري")
                st.download_button("⬇️ تحميل التقرير PDF", pdf, file_name=f"report_{int(year)}_{int(month):02d}.pdf",
                                   mime="application/pdf", key="mr_dl")
            except Exception as exc:
                st.error(f"تعذّر إنشاء PDF: {exc}")


# ======================================================
# التحليل التنبؤي (للمدير): خريطة حرارية + أحياء الاحتياج + مخاطر التأخر
# ======================================================
def _need_ranking(df: pd.DataFrame) -> pd.DataFrame:  # ترتيب الأحياء بالاحتياج: توقع الشهر القادم 40% + المتراكم المفتوح 30% + نسبة ا
    """ترتيب الأحياء بالاحتياج: توقع الشهر القادم 40% + المتراكم المفتوح 30% + نسبة المتأخر 30% (كل عنصر مُطبَّع 0–1)."""
    import numpy as np
    today = pd.Timestamp.today().normalize()
    months = pd.period_range(end=today.to_period("M") - 1, periods=6, freq="M")  # آخر 6 أشهر مكتملة
    rows = []
    for dist, g in df.groupby("الحي", observed=True):
        counts = g.groupby(g["تاريخ الاستلام"].dt.to_period("M")).size().reindex(months, fill_value=0).values
        slope, icpt = np.polyfit(range(6), counts, 1)
        forecast = max(0.0, slope * 6 + icpt)
        open_ = g[g["الحالة"] != STATUS_DONE]
        rows.append({"الحي": str(dist), "توقع الشهر القادم": round(forecast), "الاتجاه": "↑" if slope > 0.5 else "↓" if slope < -0.5 else "→",
                     "المتراكم المفتوح": len(open_),
                     "نسبة المتأخر %": round((open_["تاريخ الإنجاز المتوقع"] < today).mean() * 100, 1) if len(open_) else 0.0})
    t = pd.DataFrame(rows)
    norm = lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0
    t["درجة الاحتياج"] = (100 * (0.4 * norm(t["توقع الشهر القادم"]) + 0.3 * norm(t["المتراكم المفتوح"])
                                  + 0.3 * norm(t["نسبة المتأخر %"]))).round(1)
    return t.sort_values("درجة الاحتياج", ascending=False).reset_index(drop=True)


def _delay_risk(df: pd.DataFrame, horizon: int = 14):  # خطر التأخر للمعاملات المفتوحة التي يحل موعدها خلال horizon يوماً
    """خطر التأخر للمعاملات المفتوحة التي يحل موعدها خلال horizon يوماً.
    يتعلم من الماضي: بين المعاملات التي حلّ موعدها، كم نسبة التي لم تُنجَز؟ (بالقسم+الأهمية وبالحي، مع تنعيم إحصائي).
    تقريب: البيانات لا تحمل تاريخ الإنجاز الفعلي. يرجع (جدول المخاطر, المعدل العام)."""
    today = pd.Timestamp.today().normalize()
    open_ = df["الحالة"] != STATUS_DONE
    passed = df["تاريخ الإنجاز المتوقع"] < today
    fail = passed & open_
    g_rate = float(fail.sum() / max(passed.sum(), 1))
    k = 50  # قوة التنعيم: المجموعات الصغيرة تقترب من المعدل العام

    def rate(keys):  # يحسب معدل الفشل لكل مجموعة بتنعيم إحصائي
        t = pd.DataFrame({"n": passed.values, "f": fail.values}, index=df.index).join(df[keys]).groupby(keys, observed=True).sum()
        t["r"] = (t["f"] + k * g_rate) / (t["n"] + k)
        return df[keys].merge(t["r"].reset_index(), on=keys, how="left")["r"].fillna(g_rate).values

    cand_mask = open_ & (df["تاريخ الإنجاز المتوقع"] >= today) & (df["تاريخ الإنجاز المتوقع"] <= today + pd.Timedelta(days=horizon))
    r_dp = pd.Series(rate(["القسم المكلف", "درجة الأهمية"]), index=df.index)
    r_d = pd.Series(rate(["الحي"]), index=df.index)
    c = df[cand_mask].copy()
    base = 0.6 * r_dp[cand_mask] + 0.4 * r_d[cand_mask]
    c["الأيام المتبقية"] = (c["تاريخ الإنجاز المتوقع"] - today).dt.days
    c["خطر التأخر %"] = (100 * (base * (1 + (horizon - c["الأيام المتبقية"]) / horizon * 0.5)).clip(upper=0.99)).round(1)
    return c.sort_values("خطر التأخر %", ascending=False), g_rate


def render_predictive(ctx: AuthContext, df_all: pd.DataFrame) -> None:  # التحليل التنبؤي ومخاطر التأخر
    import plotly.graph_objects as go
    from ui import style_fig
    st.subheader("🔥 التحليل التنبؤي: الشكاوى والاحتياج وخطر التأخر")
    if not _admin_gate(ctx, "التحليل التنبؤي"):
        return
    # ---- 1) خريطة حرارية: الحي × الشهر ----
    st.markdown("##### 🗓️ خريطة حرارية: عدد الشكاوى لكل حي في كل شهر")
    months = pd.period_range(end=pd.Timestamp.today().to_period("M"), periods=12, freq="M")
    pivot = (df_all.assign(_m=df_all["تاريخ الاستلام"].dt.to_period("M"))
             .pivot_table(index="الحي", columns="_m", values="رقم المعاملة", aggfunc="count", observed=True, fill_value=0)
             .reindex(columns=months, fill_value=0))
    fig = go.Figure(go.Heatmap(z=pivot.values, x=[str(m) for m in months], y=[str(i) for i in pivot.index],
                               colorscale=[[0, "#0b1220"], [.5, "#0e7490"], [1, "#f43f5e"]],
                               hovertemplate="%{y} — %{x}: %{z} شكوى<extra></extra>"))
    style_fig(fig)
    fig.update_layout(height=380)
    st.plotly_chart(fig, width="stretch")
    card("<b>كيف تقرؤها؟</b> كل مربع = عدد المعاملات المستلمة في حي (صف) خلال شهر (عمود). الأحمر = ضغط عالٍ، الداكن = هادئ. "
         "ابحث عن صف أحمر مستمر (مشكلة مزمنة) أو مربع مفاجئ (حادثة).", "glass")
    # ---- 2) الأحياء الأكثر احتياجاً ----
    st.markdown("##### 🎯 الأحياء الأكثر احتياجاً (توقع)")
    need = _need_ranking(df_all)
    st.dataframe(need, hide_index=True, width="stretch",
                 column_config={"درجة الاحتياج": st.column_config.ProgressColumn("درجة الاحتياج", min_value=0, max_value=100, format="%.1f")})
    st.caption("درجة الاحتياج = توقع شكاوى الشهر القادم (اتجاه خطي لآخر 6 أشهر) 40% + المتراكم المفتوح 30% + نسبة المتأخر 30%.")
    # ---- 3) خطر تأخر المعاملات ----
    st.markdown("##### ⚠️ معاملات مهدَّدة بالتأخر خلال 14 يوماً")
    risk, g_rate = _delay_risk(df_all)
    high = int((risk["خطر التأخر %"] >= 60).sum()) if len(risk) else 0
    k1, k2, k3 = st.columns(3)
    k1.metric("معاملات يقترب موعدها", f"{len(risk):,}")
    k2.metric("خطر مرتفع (≥ 60%)", f"{high:,}")
    k3.metric("معدل التعثر التاريخي", f"{g_rate * 100:.1f}%", help="من المعاملات التي حلّ موعدها: نسبة التي لم تُنجَز")
    cols = [c for c in ["رقم المعاملة", "موضوع المعاملة", "الحي", "القسم المكلف", "درجة الأهمية", "الأيام المتبقية", "خطر التأخر %"] if c in risk.columns]
    top = risk[cols].head(300)
    st.dataframe(top, hide_index=True, width="stretch",
                 column_config={"خطر التأخر %": st.column_config.ProgressColumn("خطر التأخر %", min_value=0, max_value=100, format="%.1f")})
    st.download_button("⬇️ CSV للمعاملات المهدّدة", csv_bytes(top), file_name="delay_risk.csv", mime="text/csv", key="risk_dl")
    card("<b>كيف يتعلم النموذج؟</b> يحسب من الماضي نسبة تعثّر كل (قسم + أهمية) وكل حي بين المعاملات التي حلّ موعدها، ثم يرفع الخطر كلما اقترب الموعد. "
         "هو تقريب مفيد للتحذير المبكر وليس يقيناً، لأن البيانات الحالية لا تحمل تاريخ الإنجاز الفعلي. وكلما أُدخلت تواريخ فعلية تحسّنت دقته.", "ai")