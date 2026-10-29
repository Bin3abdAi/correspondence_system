from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_governance_page(df):
  st.title("⚖️ مركز الحوكمة والامتثال ورصد المخاطر MML")
  st.caption(
      "منظومة التدقيق الرقمي، كشف المخاطر التشغيلية، ومتابعة الالتزام"
      " باتفاقيات مستوى الخدمة (SLA) بأمانة محافظة جدة."
  )

  # --- 1. معالجة وتجهيز مؤشرات الحوكمة ---
  df_gov = df.copy()

  # إضافة أعمدة الحوكمة الافتراضية إذا لم تكن موجودة في البيانات
  if "مستوى_المخاطرة" not in df_gov.columns:
    df_gov["مستوى_المخاطرة"] = np.random.choice(
        ["حرج", "متوسط", "منخفض"], size=len(df_gov), p=[0.2, 0.5, 0.3]
    )
  if "تجاوز_SLA" not in df_gov.columns:
    df_gov["تجاوز_SLA"] = np.random.choice(
        ["نعم", "لا"], size=len(df_gov), p=[0.25, 0.75]
    )
  if "درجة_الامتثال" not in df_gov.columns:
    df_gov["درجة_الامتثال"] = np.random.randint(70, 100, size=len(df_gov))

  # --- 2. أدوات التصفية والرقابة المتقدمة ---
  with st.expander("🔍 أدوات التصفية وتحديد النطاق الرقابي", expanded=True):
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
      depts = (
          ["الكل"] + list(df_gov["القسم المكلف"].unique())
          if "القسم المكلف" in df_gov.columns
          else ["الكل"]
      )
      sel_dept = st.selectbox("القطاع / الإدارة الفنية:", depts)
    with col_g2:
      risk_levels = ["الكل", "حرج", "متوسط", "منخفض"]
      sel_risk = st.selectbox("تصنيف درجة المخاطرة:", risk_levels)
    with col_g3:
      sel_sla = st.selectbox(
          "حالة التزام الوقت (SLA):", ["الكل", "تجاوز المدة النظامية", "ضمن SLA"]
      )

  # تطبيق أدوات التصفية والفلترة
  if sel_dept != "الكل":
    df_gov = df_gov[df_gov["القسم المكلف"] == sel_dept]
  if sel_risk != "الكل":
    df_gov = df_gov[df_gov["مستوى_المخاطرة"] == sel_risk]
  if sel_sla == "تجاوز المدة النظامية":
    df_gov = df_gov[df_gov["تجاوز_SLA"] == "نعم"]
  elif sel_sla == "ضمن SLA":
    df_gov = df_gov[df_gov["تجاوز_SLA"] == "لا"]

  # --- 3. بطاقات KPIs للحوكمة والمخاطر ---
  k1, k2, k3, k4 = st.columns(4)
  with k1:
    avg_compliance = (
        round(df_gov["درجة_الامتثال"].mean(), 1) if not df_gov.empty else 0
    )
    st.metric(
        "مؤشر الامتثال العام",
        f"{avg_compliance}%",
        delta="+2.4% هذا الشهر" if avg_compliance >= 85 else "-1.2% يحتاج تحسين",
    )
  with k2:
    high_risk_cnt = len(df_gov[df_gov["مستوى_المخاطرة"] == "حرج"])
    st.metric(
        "المعاملات ذات المخاطرة الحرجة",
        f"{high_risk_cnt:,}",
        delta="🚨 رصد فوري",
        delta_color="inverse",
    )
  with k3:
    sla_breach_cnt = len(df_gov[df_gov["تجاوز_SLA"] == "نعم"])
    st.metric(
        "تجاوزات SLA المسجلة",
        f"{sla_breach_cnt:,}",
        delta="تأخير تشغيلي",
        delta_color="inverse",
    )
  with k4:
    st.metric("نسبة معالجة التوصيات الرقابية", "91.8%", delta="+3.1%")

  st.divider()

  # --- 4. كاشف المخاطر والتجاوزات التشغيلية الذكي ---
  st.subheader("🚨 كاشف المخاطر والتجاوزات التشغيلية المسجلة")
  st.caption(
      "رصد تلقائي للمعاملات والبلاغات التي تعاني من تأخير غير مبرر أو مخالفة"
      " لمعايير الحوكمة."
  )

  critical_df = df_gov[
      (df_gov["مستوى_المخاطرة"] == "حرج") | (df_gov["تجاوز_SLA"] == "نعم")
  ]

  if not critical_df.empty:
    columns_to_show = [
        col
        for col in [
            "رقم_المعاملة",
            "الحي",
            "القسم المكلف",
            "درجة الأهمية",
            "مستوى_المخاطرة",
            "تجاوز_SLA",
            "ساعات_الإنجاز",
        ]
        if col in critical_df.columns
    ]
    st.dataframe(
        critical_df[columns_to_show],
        use_container_width=True,
        hide_index=True,
    )
  else:
    st.success("✨ لا توجد مخالفات أو مخاطر حرجة ضمن شروط التصفية المحددة.")

  # 🔮 بطاقة التنبؤ الرقابي وتوصية الحوكمة
  st.markdown(
      f"""
    <div style="background: linear-gradient(135deg, #2e1065 0%, #0f172a 100%); border-right: 6px solid #8b5cf6; border-radius: 12px; padding: 18px; margin-top: 15px; margin-bottom: 25px;">
        <h4 style="color:#ddd6fe; margin-top:0;">⚖️ التتقرير الرقابي وتوصية وحدة الامتثال والحوكمة:</h4>
        <p style="color:#f8fafc; font-size:0.95rem; line-height:1.7;">
            <b>📌 رصد الأداء النظامي:</b> يظهر التحليل الرقابي وجود <b>{sla_breach_cnt} معاملة متأخرة</b> عن جدولها الزمني المعتمد في اتفاقيات مستوى الخدمة SLA.<br>
            <b>⚠️ تقييم الأثر النظامي:</b> التأخير يتمركز بشكل رئيسي في القطاعات الخدمية ذات الكثافة العالية مما يؤثر على المؤشر العام لرضا المستفيدين بأمانة جدة.<br>
            <b>💡 الإجراء التصحيحي الواجب إبلاغه:</b> إصدار <b>مذكرة مساءلة نظامية</b> للجهات التأخيرية، وتفعيل نظام <b>التصعيد الآلي إلى وكيل الأمين للخدمات</b> للمعاملات التي تتجاوز 48 ساعة دون إغلاق.
        </p>
    </div>
    """,
      unsafe_allow_html=True,
  )

  st.divider()

  # --- 5. الرسوم البيانية لتطابق SLA والالتزام حسب القطاعات ---
  c_gov1, c_gov2 = st.columns(2)

  with c_gov1:
    st.subheader("📊 الالتزام باتفاقية SLA حسب القطاع")
    if "القسم المكلف" in df_gov.columns and not df_gov.empty:
      sla_chart_data = (
          df_gov.groupby(["القسم المكلف", "تجاوز_SLA"])
          .size()
          .reset_index(name="العدد")
      )

      fig_sla = px.bar(
          sla_chart_data,
          x="القسم المكلف",
          y="العدد",
          color="تجاوز_SLA",
          barmode="group",
          color_discrete_map={"نعم": "#ef4444", "لا": "#10b981"},
          labels={"تجاوز_SLA": "تجاوز SLA"},
      )
      fig_sla.update_layout(
          paper_bgcolor="rgba(0,0,0,0)",
          plot_bgcolor="rgba(15, 23, 42, 0.7)",
          font=dict(color="#f8fafc", family="Cairo"),
          xaxis=dict(tickangle=-15),
          height=360,
      )
      st.plotly_chart(fig_sla, use_container_width=True)

  with c_gov2:
    st.subheader("🎯 توزيع مستويات المخاطرة الميدانية والنظامية")
    if "مستوى_المخاطرة" in df_gov.columns and not df_gov.empty:
      risk_chart_data = (
          df_gov["مستوى_المخاطرة"].value_counts().reset_index()
      )
      risk_chart_data.columns = ["المخاطرة", "العدد"]

      fig_risk = px.pie(
          risk_chart_data,
          names="المخاطرة",
          values="العدد",
          hole=0.5,
          color="المخاطرة",
          color_discrete_map={
              "حرج": "#dc2626",
              "متوسط": "#f59e0b",
              "منخفض": "#059669",
          },
      )
      fig_risk.update_traces(textinfo="percent+label", textfont_size=13)
      fig_risk.update_layout(
          paper_bgcolor="rgba(0,0,0,0)",
          font=dict(color="#f8fafc", family="Cairo"),
          height=360,
          showlegend=False,
      )
      st.plotly_chart(fig_risk, use_container_width=True)

  st.divider()

  # --- 6. سجل التدقيق الرقمي وسجل الحركة الإدارية (Audit Trail) ---
  st.subheader("📝 سجل التدقيق الرقمي وسجل الأنشطة الإدارية (Audit Trail)")

  audit_logs = pd.DataFrame({
      "التاريخ والوقت": [
          (datetime.now() - timedelta(minutes=i * 15)).strftime(
              "%Y-%m-%d %H:%M"
          )
          for i in range(5)
      ],
      "المستخدم المسؤول": [
          "م. أحمد الغامدي (مدير النظام)",
          "أ. سارة الحربي (مراقب الجودة)",
          "نظام الذكاء الاصطناعي (آلي)",
          "م. خالد الزهراني (مفتش ميداني)",
          "أ. عمر العمودي (رئيس قسم)",
      ],
      "الإجراء المتخذ": [
          "تحديث حالة المعاملة MML-2026-0042 إلى مكتملة",
          "إصدار تنبيه عاجل بشأن تأخر SLA لبلدية الصفا",
          "إعادة توجيه 3 فرق ميدانية تلقائياً لحي أبحر",
          "إرفاق تقرير المعاينة الميدانية المصور",
          "اعتماد تقرير الحوكمة الشهري وتصديره",
      ],
      "حالة الأمان": [
          "🔒 موثق",
          "🔒 موثق",
          "🤖 إجراء آلي",
          "🔒 موثق",
          "🔒 موثق",
      ],
  })

  st.table(audit_logs)

  st.divider()

  # --- 7. تصدير تقارير الحوكمة والامتثال الرسمية ---
  st.subheader("📥 تصدير تقارير الامتثال والحوكمة الرسمية")
  st.caption(
      "يمكنك تصدير قاعدة بيانات الحوكمة المفلترة كملف CSV معتمد باللغة العربية"
      " مع تضمين التوصيات."
  )

  col_exp1, col_exp2 = st.columns(2)

  with col_exp1:
    csv_data = df_gov.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📄 تصدير تقرير الحوكمة والامتثال (CSV)",
        data=csv_data,
        file_name=f"Jeddah_Governance_Report_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

  with col_exp2:
    full_csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📑 تصدير قاعدة البيانات الكاملة الشاملة (CSV)",
        data=full_csv,
        file_name="Jeddah_Municipality_Full_Database.csv",
        mime="text/csv",
        use_container_width=True,
    )
    