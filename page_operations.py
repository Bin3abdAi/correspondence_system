from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from ai_service import analyze_site_image_vision, render_global_ai_copilot_widget
from vision_engine import render_vision_analysis_widget

def render_operations_page(df):
    st.title("🚜 مركز إدارة العمليات والفرق الميدانية MML")
    st.caption(
        "منظومة التتبع الميداني الحي، وتوزيع الفرق التشغيلية، وإدارة البلاغات"
        " الطارئة بأمانة محافظة جدة."
    )

    # --- 1. تهيئة بيانات جغرافية وتشغيلية محاكاة للمواقع الميدانية في جدة ---
    district_coords = {
        "بلدية أبحر الفرعية": {"lat": 21.7532, "lon": 39.1254, "code": "OBS"},
        "بلدية الصفا الفرعية": {"lat": 21.5812, "lon": 39.2014, "code": "SAF"},
        "بلدية جدة التاريخية": {"lat": 21.4858, "lon": 39.1823, "code": "HIS"},
        "بلدية الجامعة الفرعية": {"lat": 21.4921, "lon": 39.2451, "code": "UNI"},
    }

    # دمج الإحداثيات التقريبية بالبيانات لعرضها على الخريطة
    df_ops = df.copy()
    df_ops["lat"] = df_ops["الحي"].map(
        lambda x: district_coords.get(x, {}).get("lat", 21.5433)
        + np.random.uniform(-0.02, 0.02)
    )
    df_ops["lon"] = df_ops["الحي"].map(
        lambda x: district_coords.get(x, {}).get("lon", 39.1728)
        + np.random.uniform(-0.02, 0.02)
    )

# --- إضافة محرك تحليل المستندات والصور بالرؤية الحاسوبية ---
    with st.expander("📁 رفع وتحليل المستندات بالرؤية الحاسوبية (Vision AI)", expanded=False):
        render_vision_analysis_widget()
    
    st.markdown("---")
    # --- 2. أدوات الفلترة والتحكم الميداني السريع ---
    with st.expander("🎛️ لوحة التكليف والتصفية الميدانية", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            dist_list = (
                ["الكل"] + list(df_ops["الحي"].unique())
                if "الحي" in df_ops.columns
                else ["الكل"]
            )
            sel_district = st.selectbox("البلدية الفرعية / الحي:", dist_list)
        with col_f2:
            status_list = (
                ["الكل"] + list(df_ops["حالة_المعاملة"].unique())
                if "حالة_المعاملة" in df_ops.columns
                else ["الكل"]
            )
            sel_status = st.selectbox("حالة التكليف الميداني:", status_list)
        with col_f3:
            prio_list = (
                ["الكل"] + list(df_ops["درجة الأهمية"].unique())
                if "درجة الأهمية" in df_ops.columns
                else ["الكل"]
            )
            sel_prio = st.selectbox("مستوى أولوية التكليف:", prio_list)
        with col_f4:
            sel_team = st.selectbox(
                "تصفية حسب فرقة الصيانة:",
                [
                    "الكل",
                    "فرقة التدخل السريع 01",
                    "فرقة الطوارئ 02",
                    "فرقة النظافة والبيئة 03",
                    "فرقة الطرق والسلامة 04",
                ],
            )

    # تطبيق أدوات التصفية
    if sel_district != "الكل":
        df_ops = df_ops[df_ops["الحي"] == sel_district]
    if sel_status != "الكل":
        df_ops = df_ops[df_ops["حالة_المعاملة"] == sel_status]
    if sel_prio != "الكل":
        df_ops = df_ops[df_ops["درجة الأهمية"] == sel_prio]

    # --- 3. مؤشرات الأداء الميداني KPIs ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "إجمالي البلاغات الميدانية",
            f"{len(df_ops):,}",
            delta="تحديث حي",
        )
    with m2:
        pending_cnt = (
            len(df_ops[df_ops["حالة_المعاملة"] == "قيد المعالجة"])
            if "حالة_المعاملة" in df_ops.columns
            else 0
        )
        st.metric(
            "البلاغات قيد المباشرة الآن",
            f"{pending_cnt:,}",
            delta="⏳ جارٍ المعالجة",
            delta_color="off",
        )
    with m3:
        st.metric("الفرق الميدانية النشطة", "18 فرقة", delta="94% طاقة تشغيلية")
    with m4:
        st.metric("متوسط زمن الاستجابة للموقع (ETA)", "18.5 دقيقة", delta="-4 دقائق")

    st.divider()

    # --- 4. التوزيع الجغرافي الخارطي للبلاغات الميدانية ---
    st.subheader("🗺️ التوزيع الجغرافي الخارطي لمواقع البلاغات الميدانية")

    if not df_ops.empty:
        fig_map = px.scatter_mapbox(
            df_ops,
            lat="lat",
            lon="lon",
            color="درجة الأهمية",
            size="ساعات_الإنجاز" if "ساعات_الإنجاز" in df_ops.columns else None,
            hover_name="رقم_المعاملة",
            hover_data=[
                "الحي",
                "القسم المكلف",
                "حالة_المعاملة",
                "درجة الأهمية",
            ],
            color_discrete_map={
                "عاجل": "#ef4444",
                "هام": "#f59e0b",
                "عادي": "#3b82f6",
            },
            zoom=10,
            height=450,
            title="مواقع البلاغات الميدانية المسجلة حالياً على خريطة جدة",
        )
        fig_map.update_layout(
            mapbox_style="carto-darkmatter",
            margin=dict(l=10, r=10, t=40, b=10),
            font=dict(color="#f8fafc", family="Cairo"),
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("لا توجد بلاغات تطابق شروط التصفية لعرضها على الخريطة.")

    st.divider()

    # --- 5. نظام إسناد وتكليف الفرق الميدانية العاجلة ---
    col_dispatch, col_teams = st.columns([1, 1.2])

    with col_dispatch:
        st.subheader("⚡ مركز الإسناد المباشر للبلاغات العاجلة")
        with st.form("dispatch_form", clear_on_submit=True):
            task_id = st.text_input(
                "رقم البلاغ / المعاملة الميدانية:", value="MML-2026-0089"
            )
            target_district = st.selectbox(
                "الموقع / الحي المستهدف:", list(district_coords.keys())
            )
            assigned_team = st.selectbox(
                "تعيين الفرقة الميدانية المكلفة:",
                [
                    "فرقة التدخل السريع 01 - (أبحر)",
                    "فرقة الطوارئ 02 - (الصفا)",
                    "فرقة الرقابة والبيئة 03 - (التاريخية)",
                    "فرقة الطرق والجسور 04 - (الجامعة)",
                ],
            )
            urgency_level = st.radio(
                "مستوى أولوية التوجيه:",
                ["🔴 حرج جداً (تدخل خلال 30 دقيقة)", "🟡 عاجل", "🔵 عادي"],
                horizontal=True,
            )
            dispatch_notes = st.text_area(
                "توجيهات المباشرة وملاحظات غرفة العمليات:",
                placeholder="أدخل الملاحظات الميدانية الموجهة لقائد الفرقة...",
            )

            submitted = st.form_submit_button("🚨 إرسال أمر التكليف الميداني المباشر")
            if submitted:
                st.success(
                    f"✅ تم إرسال التكليف الميداني بنجاح للفرقة **({assigned_team})**"
                    f" لمباشرة البلاغ **{task_id}** في **{target_district}**."
                )
                st.toast("🚨 تم إرسال إشعار لحظي لجهاز قائد الفرقة الميدانية!")

    with col_teams:
        st.subheader("👥 حالة الفرق الميدانية وجاهزية الكوادر")

        teams_data = pd.DataFrame({
            "رمز الفرقة": ["TEAM-01", "TEAM-02", "TEAM-03", "TEAM-04"],
            "قائد الفرقة": [
                "م. خالد الغامدي",
                "أ. فهد الحربي",
                "م. سلطان الشهري",
                "أ. عبدالمجيد الزهراني",
            ],
            "النطاق الميداني": [
                "أبحر الفرعية",
                "الصفا الفرعية",
                "جدة التاريخية",
                "الجامعة الفرعية",
            ],
            "حالة الجاهزية": [
                "🟢 متاحة للمباشرة",
                "🔴 بانتظار إغلاق بلاغ",
                "🟢 متاحة للمباشرة",
                "🟡 في الطريق لموقع",
            ],
            "البلاغات المنجزة اليوم": [12, 8, 15, 9],
        })

        st.dataframe(
            teams_data,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-right: 5px solid #10b981; padding: 14px; border-radius: 10px; margin-top: 15px;">
                <b style="color:#34d399;">💡 توجيه الكفاءة التشغيلية:</b><br>
                تظهر البيانات جاهزية عالية لـ <b>فرقة TEAM-01</b> و <b>TEAM-03</b> لمساندة المناطق المجاورة ذات كثافة البلاغات المرتفعة.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # --- 6. بطاقات تتبع وحالة المعاملات الميدانية (Task Tracking Cards) ---
    st.subheader("📋 متابعة حالة البلاغات والمعاينات الميدانية الجارية")

    if not df_ops.empty:
        sample_df = df_ops.head(6)
        cols = st.columns(3)

        for idx, (_, row) in enumerate(sample_df.iterrows()):
            col_idx = idx % 3
            with cols[col_idx]:
                prio_color = (
                    "#ef4444"
                    if row.get("درجة الأهمية") == "عاجل"
                    else ("#f59e0b" if row.get("درجة الأهمية") == "هام" else "#3b82f6")
                )

                st.markdown(
                    f"""
                    <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255,255,255,0.1); border-top: 5px solid {prio_color}; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b style="color:#f8fafc; font-size:1.1rem;">{row.get('رقم_المعاملة', 'MML-0000')}</b>
                            <span style="background:{prio_color}; color:#fff; padding:2px 8px; border-radius:10px; font-size:0.75rem;">{row.get('درجة الأهمية', 'عادي')}</span>
                        </div>
                        <p style="color:#94a3b8; font-size:0.9rem; margin:8px 0;">
                            <b>📍 الحي:</b> {row.get('الحي', 'غير محدد')}<br>
                            <b>🏢 القطاع:</b> {row.get('القسم المكلف', 'عام')}<br>
                            <b>⏳ الحالة:</b> {row.get('حالة_المعاملة', 'قيد المعالجة')}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                c_act1, c_act2 = st.columns(2)
                with c_act1:
                    if st.button(
                        "✅ تأكيد الإنجاز",
                        key=f"done_{row.get('رقم_المعاملة')}_{idx}",
                        use_container_width=True,
                    ):
                        st.toast(f"تم اعتماد إغلاق البلاغ {row.get('رقم_المعاملة')} بنجاح!")
                with c_act2:
                    if st.button(
                        "📍 تحديث الموقع",
                        key=f"loc_{row.get('رقم_المعاملة')}_{idx}",
                        use_container_width=True,
                    ):
                        st.info("تم إرسال إحداثيات الموقع الحالي إلى خريطة الفرقة.")

    # --- 7. التنبؤ بالتحسين اللوجستي والوقود ---
    st.divider()
    st.subheader("🔮 التحليل التنبؤي للمسارات وتقليل استهلاك وقود الفرق")

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); border-right: 6px solid #3b82f6; border-radius: 12px; padding: 18px;">
            <h4 style="color:#93c5fd; margin-top:0;">🤖 توصية خوارزميات المسار الذكي (Smart Route Optimization):</h4>
            <p style="color:#f8fafc; font-size:0.95rem; line-height:1.7;">
                <b>📌 التحليل التجميعي للبلاغات:</b> يوضح تحليل المجموعات المكانية وجود <b>14 بلاغاً متجاوراً</b> في نطاق حي الصفا يقل التباعد بينها عن 800 متر.<br>
                <b>⚠️ الهدر اللوجستي الحركي:</b> توجيه الفرق بشكل فردي يتسبب في زيادة استهلاك الوقود بنسبة <b>22%</b> ورفع زمن التنقل بـ <b>35 دقيقة</b>.<br>
                <b>💡 الحل اللوجستي الموصى به:</b> تفعيل نظام <b>"التكامل المساري"</b> بتجميع البلاغات المتقاربة وتسليمها دفعة واحدة لـ (فرقة الطوارئ 02)، مما يضمن إغلاقها بالكامل قبل الساعة 4:00 مساءً.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- 8. أدوات التحليل البصري للصور الميدانية ---
    st.markdown("---")
    st.subheader("📷 التحليل البصري الذكي للبلاغات والمخالفات الميدانية")

    uploaded_ops_image = st.file_uploader(
        "ارفع صورة ميدانية للمعاينة أو المخالفة (حفريات، إنارة، نظافة..):", 
        type=["jpg", "jpeg", "png"],
        key="ops_image_upload"
    )

    if uploaded_ops_image is not None:
        st.image(uploaded_ops_image, caption="الصورة الميدانية المرفوعة للمعاينة", use_container_width=True)
        
        custom_ops_prompt = st.text_input(
            "تحديد هدف التحليل البصري:",
            value="قم بتحليل هذه الصورة الميدانية واستخرج نوع المخالفة بدقة، درجة الخطورة، والقسْم المعني بالمباشرة دون افتراض أي حي مسبقاً:",
            key="ops_prompt_input"
        )
        
        if st.button("🔍 تحليل الصورة بالذكاء الاصطناعي التشغيلي", key="btn_run_ops_vision"):
            with st.spinner("جاري قراءة وتحليل الصورة عبر محرك الرؤية..."):
                vision_result = analyze_site_image_vision(uploaded_ops_image, prompt_text=custom_ops_prompt)
                st.success("✨ نتائج التحليل البصري الميداني:")
                st.markdown(
                    f"""
                    <div style="background: rgba(15, 23, 42, 0.85); padding: 18px; border-radius: 12px; border: 1px solid #38bdf8; color: #f8fafc;">
                        {vision_result}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # --- 9. أدوات التصدير والطباعة الخاصة بغرفة العمليات والفرق الميدانية ---
    st.markdown("---")
    st.markdown("### 🖨️ أدوات التصدير والطباعة للعمليات")

    col_op1, col_op2 = st.columns(2)
    with col_op1:
        if st.button("📥 تصدير تقرير العمليات الميدانية (CSV)", use_container_width=True, key="export_ops_csv"):
            st.success("✅ يتم تجهيز تقرير العمليات للتحميل.")
    with col_op2:
        if st.button("🖨️ طباعة تقرير العمليات الحالي", use_container_width=True, key="print_ops_btn"):
            st.info("💡 يمكنك طباعة التقرير أو حفظه بصيغة PDF بالضغط على (Ctrl + P) من لوحة المفاتيح.")

    # استدعاء المساعد الذكي مع سياق الصفحة المحددة بدقة
    render_global_ai_copilot_widget("مركز إدارة العمليات والفرق الميدانية MML")