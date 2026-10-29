import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
import urllib.parse
import database as db

# ==========================================
# 1. تهيئة الصفحة الرئيسية
# ==========================================
st.set_page_config(
    page_title="منصة إدارة أمانة محافظة جدة - المساعد الذكي",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. تهيئة قاعدة البيانات والتأكد من التوصيل
# ==========================================
db.init_db()

# ==========================================
# 3. إدارة حالة الجلسة (Session State)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [
        {"role": "assistant", "content": "مرحباً بك! أنا **المساعد الذكي لأمانة محافظة جدة** 🏛️.\nكيف يمكنني مساعدتك اليوم في متابعة المعاملات، تقييم مهل الإنجاز (SLA)، أو صياغة البلاغات والتقارير الإدارية وإرسالها عبر البريد؟"}
    ]

# ==========================================
# 4. التنسيق البصري الفاخر والشامل (CSS)
# ==========================================
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0b1329 0%, #111c38 50%, #0f172a 100%) !important;
        color: #f8fafc !important;
        direction: rtl;
        text-align: right;
    }
    div[data-testid="stAppViewContainer"] {
        direction: rtl;
        text-align: right;
    }
    .stMetric {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        padding: 18px;
        border-radius: 14px;
        border-right: 5px solid #38bdf8;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .dev-card {
        padding: 16px;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
        margin-top: 25px;
        color: #38bdf8;
        font-weight: bold;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    .meeting-box-sun {
        background-color: #1e293b;
        border-right: 5px solid #38bdf8;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 12px;
        color: #f1f5f9;
    }
    .meeting-box-thu {
        background-color: #1e293b;
        border-right: 5px solid #f43f5e;
        padding: 16px 20px;
        border-radius: 10px;
        color: #f1f5f9;
    }
    .ai-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-right: 5px solid #a855f7;
        padding: 18px;
        border-radius: 12px;
        margin-top: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.15);
    }
    .ai-sla-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-right: 5px solid #38bdf8;
        padding: 18px;
        border-radius: 10px;
        margin-top: 15px;
    }
    .alert-card-red {
        background-color: #1e293b;
        border-right: 5px solid #f43f5e;
        padding: 18px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .alert-card-blue {
        background-color: #1e293b;
        border-right: 5px solid #38bdf8;
        padding: 18px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .email-btn {
        display: block;
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white !important;
        text-align: center;
        padding: 12px 20px;
        border-radius: 10px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
        margin-top: 10px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    .email-btn:hover {
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%);
        box-shadow: 0 6px 15px rgba(2, 132, 199, 0.5);
    }
    .guidance-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. الشريط الجانبي (Sidebar)
# ==========================================
with st.sidebar:
    st.subheader("🔒 توثيق الجلسة والتسجيل")
    if not st.session_state['authenticated']:
        user = st.text_input("اسم المستخدم", key="admin")
        password = st.text_input("كلمة المرور", type="password", key="123456")
        if st.button("تسجيل الدخول 🔑", use_container_width=True):
            if user == "admin" and password == "123456":
                st.session_state['authenticated'] = True
                st.success("تم التوثيق بنجاح")
                st.rerun()
            else:
                st.error("بيانات غير صحيحة")
    else:
        st.success("تم التوثيق - وصول كامل للمعاملات السرية")
        if st.button("تسجيل الخروج 🚪", use_container_width=True):
            st.session_state['authenticated'] = False
            st.rerun()

    st.divider()
    st.markdown('<div class="dev-card">تصميم وتطوير المقترح بواسطة فريق - الذكاء الاصطناعي ونظم المعلومات🤲❤️‍🩹✨</div>', unsafe_allow_html=True)

# ==========================================
# 6. الهيدر والتعريف بالنظام
# ==========================================
col_header1, col_header2 = st.columns([1.2, 2])

with col_header1:
    if os.path.exists("jeddah_building.jpg"):
        st.image("jeddah_building.jpg", caption="مبنى أمانة محافظة جدة الرئيسي", use_container_width=True)

with col_header2:
    st.title("🏛️ منصة إدارة أمانة محافظة جدة التجريبي")
    st.caption("نظام أمن البيانات وإدارة العمليات والتحليلات التنبؤية بالذكاء الاصطناعي | متصل بقاعدة البيانات الحقيقية ومزود بمركز مراسلات البريد ✉️")

st.divider()

# ==========================================
# 7. التبويبات الرئيسية الشاملة (Tabs)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 لوحة التحليلات والعمليات الذكية", 
    "📝 إدخال وتصنيف البيانات (AI SLA)", 
    "📢 بث الرسائل والإنذارات العاجلة",
    "🤖 المساعد الذكي والإرشاد البلدي"
])

# ------------------------------------------
# التبويب الأول: لوحة التحليلات والعمليات الذكية
# ------------------------------------------
with tab1:
    df_main = db.get_all_transactions()

    # مؤشرات الأداء الحيوية
    c1, c2, c3, c4 = st.columns(4)
    total_cnt = len(df_main)
    completed_cnt = len(df_main[df_main['الحالة'] == 'منجزة']) if total_cnt > 0 else 0
    pending_cnt = len(df_main[df_main['الحالة'] == 'غير منجزة']) if total_cnt > 0 else 0
    rate = round((completed_cnt / total_cnt) * 100, 1) if total_cnt > 0 else 0

    c1.metric("إجمالي السجلات بقاعدة البيانات", total_cnt)
    c2.metric("المعاملات المنجزة", completed_cnt)
    c3.metric("المعاملات غير المنجزة", pending_cnt)
    c4.metric("معدل الكفاءة الميداني", f"{rate}%")

    # وحدة تشخيص واستنتاجات الذكاء الاصطناعي (AI Insights Engine)
    st.markdown("""
        <div class="ai-card">
            <h4 style="color:#a855f7; margin:0 0 10px 0;">🧠 التقرير التشخيصي المباشر محرك الذكاء الاصطناعي (AI Insights)</h4>
    """, unsafe_allow_html=True)
    
    if total_cnt > 0:
        top_pending_dept = df_main[df_main['الحالة'] == 'غير منجزة']['القسم المكلف'].value_counts().idxmax() if pending_cnt > 0 else "لا يوجد"
        urgent_pending = len(df_main[(df_main['الحالة'] == 'غير منجزة') & (df_main['درجة الأهمية'] == 'عاجل')])
        
        report_text = f"معدل الإنجاز العام: {rate}% | المنجزة: {completed_cnt} | المعلقة: {pending_cnt} | القطاع الأعلى تأخيراً: {top_pending_dept} | المعاملات العاجلة المعلقة: {urgent_pending}"
        
        st.markdown(f"""
            • <b>تحليل الأداء:</b> يُظهر النظام نسبة إنجاز قدرها <b style="color:#38bdf8;">{rate}%</b> عبر كافة القطاعات الميدانية.<br>
            • <b>نقطة الاختناق الإداري:</b> القسم الأعلى تسجيلاً للمهام غير المنجزة هو <b style="color:#f43f5e;">[{top_pending_dept}]</b>.<br>
            • <b>إنذار SLA للذكاء الاصطناعي:</b> يوجد <b style="color:#f43f5e;">{urgent_pending} معاملات عاجلة</b> تتطلب معالجة فورية وتعيين فرق عمل ميدانية.
        """, unsafe_allow_html=True)
    else:
        report_text = "لا توجد بيانات كافية حالياً."
        st.markdown("لا توجد بيانات كافية حالياً لإجراء التحليل التنبؤي.", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # ✉️ قسم إرسال التقرير الشامل عبر البريد/Gmail
    col_em1, col_em2 = st.columns([2, 1])
    with col_em1:
        target_email_tab1 = st.text_input("عنوان البريد الإلكتروني للمستلم (الإدارة / المسؤول)", value="management@jeddah.gov.sa", key="em_tab1")
    with col_em2:
        st.markdown("<br>", unsafe_allow_html=True)
        subject_enc1 = urllib.parse.quote("تقرير التحليلات التنفيذي - منصة أمانة جدة")
        body_enc1 = urllib.parse.quote(f"السادة الأفاضل في الإدارة التنفيذية،\n\nإليكم التقرير اللحظي لمؤشرات الأداء بأمانة جدة:\n\n{report_text}\n\nيرجى الاطلاع والتعميد.\n\nمنصة إدارة أمانة محافظة جدة التجريبي")
        mailto_link1 = f"mailto:{target_email_tab1}?subject={subject_enc1}&body={body_enc1}"
        st.markdown(f'<a href="{mailto_link1}" target="_blank" class="email-btn">إرسال تقرير التحليلات الشامل عبر Gmail ✉️</a>', unsafe_allow_html=True)

    st.divider()

    # مركز الاجتماعات والتنبيهات
    st.subheader("🔔 مركز التنبيهات والاجتماعات الأسبوعية")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("""
            <div class="meeting-box-sun">
                <b style="font-size:1.05rem; color:#38bdf8;">📅 اجتماع صباح الأحد (09:00 صباحاً):</b><br>
                • توجيه المعاملات والمهمات اليومية لمختلف الأقسام المباشرة.<br>
                • تحديد الأقسام المكلفة وتعيين مهلة الإنجاز المتوقعة (SLA) لكل مهمة.
            </div>
        """, unsafe_allow_html=True)
    with col_m2:
        st.markdown("""
            <div class="meeting-box-thu">
                <b style="font-size:1.05rem; color:#f43f5e;">📅 اجتماع ظهيرة الخميس (12:00 ظهراً):</b><br>
                • التذكير بجدول المساءلة لمراجعة المهام غير المنجزة والأخطاء الإدارية والإملائية.<br>
                • مناقشة الاقتراحات بشأن بعض الحلول والأفكار الجماعية لتطوير سرعة الإنجاز.
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # الرسوم البيانية التفاعلية
    col_chart1, col_chart2 = st.columns(2)
    color_map = {'منجزة': '#38bdf8', 'غير منجزة': '#f43f5e'}

    with col_chart1:
        st.subheader("📊 نسبة الإنجاز الشاملة")
        if total_cnt > 0:
            fig_status = px.pie(df_main, names='الحالة', color='الحالة', color_discrete_map=color_map, hole=0.45)
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("لا توجد بيانات للعرض")

    with col_chart2:
        st.subheader("📈 أداء الأقسام المباشر")
        if total_cnt > 0:
            fig_dept = px.bar(df_main, x='القسم المكلف', color='الحالة', barmode='group', color_discrete_map=color_map)
            st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("لا توجد بيانات للعرض")

    st.divider()

    # جدول السجلات التفصيلي
    st.subheader("📋 سجل المعاملات التفصيلي")
    if not st.session_state['authenticated']:
        st.info("🔒 المعاملات السرية محجوبة. يرجى تسجيل الدخول من الشريط الجانبي لعرض كامل البيانات.")
        display_df = df_main[df_main['السرية'] == 'عام'].copy() if total_cnt > 0 else df_main
    else:
        display_df = df_main.copy()

    st.dataframe(display_df, use_container_width=True)
    
    if len(display_df) > 0:
        csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("تنزيل تقرير المعاملات (CSV) 📥", csv_data, "Jeddah_Municipality_Report.csv", "text/csv")


# ------------------------------------------
# التبويب الثاني: إدخال وتصنيف البيانات (AI SLA Engine)
# ------------------------------------------
with tab2:
    st.subheader("📝 نموذج إدخال وتوجيه المعاملات الذكي")
    
    existing_transactions = db.get_all_transactions()
    next_trx_num = f"TRX-{1001 + len(existing_transactions)}"

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        trx_num = st.text_input("رقم المعاملة", value=next_trx_num)
        subject = st.text_input("موضوع المعاملة / البلاغ", placeholder="أدخل تفاصيل المعاملة...")
        district = st.selectbox("الحي / المنطقة", [
            "حي الصفا", "حي أبحر الشمالية", "حي الشاطئ / الكورنيش", 
            "حي الجامعة", "حي الحمراء", "حي الحمدانية", "حي النسيم"
        ])
        sender_type = st.selectbox("نوع الجهة", ["توجيه رسمي", "توجيه خاص", "بلاغ مواطن"])
        sender_name = st.text_input("اسم الجهة / المواطن", placeholder="اسم الراسل...")

    with col_f2:
        dept = st.selectbox("القسم المكلف المباشر", [
            "إدارة محافظة جدة", "قسم المعلومات", "إدارة صيانة الطرق", 
            "إدارة التراخيص", "إدارة الأراضي والأملاك", "إدارة النظافة والبيئة", 
            "بلدية الصفا الفرعية", "بلدية أبحر الفرعية"
        ])
        priority = st.selectbox("درجة الأهمية", ["عاجل", "هام", "عادي"])
        confidentiality = st.selectbox("درجة السرية", ["عام", "سري", "سري للغاية"])
        delivery_date = st.date_input("تاريخ التسليم", datetime.date.today())

    # 🧠 محرك التنبؤ والتوجيه بالذكاء الاصطناعي (AI SLA Engine)
    st.markdown("---")
    st.markdown("### 🧠 محرك التنبؤ والتوجيه بالذكاء الاصطناعي (AI SLA Engine)")

    predicted_days = 3
    complexity_level = "متوسطة"
    ai_reason = ""
    recommended_action = ""

    if priority == "عاجل" and sender_type == "توجيه رسمي":
        predicted_days = 2
        complexity_level = "عالية جداً (أولوية قصوى)"
        ai_reason = "توجيه رسمي عاجل يتطلب معالجة فورية وإشعار مدير الإدارة مباشرة."
        recommended_action = "إرسال فريق ميداني فوراً + إدراج الموضوع بجدول المساءلة يوم الخميس."
    elif priority == "عاجل" or sender_type == "بلاغ مواطن":
        predicted_days = 3
        complexity_level = "متوسطة إلى عالية"
        ai_reason = "بلاغ عاجل يتطلب متابعة وسرعة معالجة ميدانية لمعالجة الشكوى."
        recommended_action = "تأكيد استلام البلاغ وإفادة المواطن برقم المعاملة لتتبع التنفيذ."
    elif priority == "هام":
        predicted_days = 5
        complexity_level = "متوسطة"
        ai_reason = "معاملة هامة تتطلب تدقيقاً فنياً واستيفاء كافة الشروط الميدانية والقانونية."
        recommended_action = "تحويل الملف للقسم المختص لاستكمال المرفقات قبل الاعتماد النهائية."
    else:
        predicted_days = 7
        complexity_level = "عادية"
        ai_reason = "معاملة روتينية ضمن إجراءات العمل والخدمات الدورية بالأمانة."
        recommended_action = "جدولة المعاملة ضمن الخطة الأسبوعية المعتادة."

    st.markdown(f"""
        <div class="ai-sla-card">
            <h4>💡 النتيجة التنبؤية والتوجيه الذكي:</h4>
            • <b>مهلة الإنجاز المقترحة (SLA):</b> <span style="color:#38bdf8; font-size:1.2rem; font-weight:bold;">{predicted_days} أيام</span><br>
            • <b>مستوى الصعوبة الإدارية:</b> {complexity_level}<br>
            • <b>التحليل والتسويغ:</b> {ai_reason}<br>
            • <b>توصية الذكاء الاصطناعي للموظف:</b> <span style="color:#a855f7; font-weight:bold;">{recommended_action}</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # قسم تحديد بريد المستلم للتوجيه
    recipient_email_tab2 = st.text_input("بريد الجهة / القسم المستلم للإرسال المباشر", value="info@jeddah.gov.sa", key="em_tab2")

    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        if st.button("حفظ المعاملة في قاعدة البيانات 💾", use_container_width=True):
            if subject and sender_name:
                exp_date = delivery_date + datetime.timedelta(days=predicted_days)
                new_entry = {
                    "رقم المعاملة": trx_num,
                    "موضوع المعاملة": subject,
                    "الحي": district,
                    "نوع الجهة": sender_type,
                    "اسم الجهة": sender_name,
                    "درجة الأهمية": priority,
                    "السرية": confidentiality,
                    "القسم المكلف": dept,
                    "الحالة": "غير منجزة",
                    "تاريخ التسليم": str(delivery_date),
                    "التاريخ المتوقع للإنجاز": str(exp_date),
                    "سبب عدم الإنجاز": "معاملة جديدة - قيد المعالجة"
                }
                db.add_transaction(new_entry)
                st.success(f"تم حفظ المعاملة ({trx_num}) بنجاح بقاعدة البيانات!")
                st.rerun()
            else:
                st.error("يرجى إكمال موضوع المعاملة واسم الجهة قبل الحفظ.")

    with btn_col2:
        email_subject2 = urllib.parse.quote(f"توجيه معاملة جديدة: {trx_num} - {subject}")
        email_body2 = urllib.parse.quote(
            f"رقم المعاملة: {trx_num}\n"
            f"الموضوع: {subject}\n"
            f"الحي: {district}\n"
            f"الجهة الراسلة: {sender_name} ({sender_type})\n"
            f"القسم المكلف: {dept}\n"
            f"درجة الأهمية: {priority}\n"
            f"درجة السرية: {confidentiality}\n"
            f"مهلة الإنجاز التنبؤية (AI SLA): {predicted_days} أيام\n"
            f"توصية النظام: {recommended_action}\n\n"
            f"يرجى اتخاذ اللازم حسب الصلاحيات."
        )
        mailto_link2 = f"mailto:{recipient_email_tab2}?subject={email_subject2}&body={email_body2}"
        st.markdown(f'<a href="{mailto_link2}" target="_blank" class="email-btn">إرسال تفاصيل المعاملة عبر Gmail ✉️</a>', unsafe_allow_html=True)


# ------------------------------------------
# التبويب الثالث: بث الرسائل والإنذارات العاجلة
# ------------------------------------------
with tab3:
    st.subheader("✉️ إنشاء وبث تنبيه جديد بالذكاء الاصطناعي")

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        alert_title = st.text_input("عنوان التنبيه", placeholder="مثال: حالة مطرية طارئة - حي الشاطئ")
        target_dept = st.multiselect("القطاعات المستهدفة", [
            "كافة الأقسام والبلديات", "إدارة صيانة الطرق", "إدارة النظافة والبيئة", 
            "بلدية الصفا الفرعية", "بلدية أبحر الفرعية", "قسم المعلومات والحاسب الآلي"
        ], default=["كافة الأقسام والبلديات"])

    with col_a2:
        alert_level = st.selectbox("مستوى الخطورة", ["عالي جداً (إنذار أحمر)", "متوسط (تنبيه هام)", "عادي (إشعار إداري)"])
        sender_officer = st.text_input("المسؤول المنسق", value="مركز المتابعة والتحكم الميداني")

    alert_body = st.text_area("نص الرسالة والتعليمات الميدانية", placeholder="اكتب التعليمات الميدانية هنا...")

    # 🧠 تقييم طوارئ بالذكاء الاصطناعي
    if alert_title:
        st.markdown(f"""
            <div class="ai-card" style="margin-top:10px;">
                <b style="color:#a855f7;">🤖 تقييم الذكاء الاصطناعي للبث الطارئ:</b><br>
                • <b>زمن الاستجابة المقترح:</b> خلال 30 دقيقة للميدان.<br>
                • <b>الفرق المطلوبة:</b> السلامة، الصيانة، المتابعة الميدانية.<br>
                • <b>توصية البث:</b> تفعيل التنبيه العاجل للشاشات الرئيسية والغرف الميدانية وإرسال بريد طوارئ.
            </div>
        """, unsafe_allow_html=True)

    alert_email_target = st.text_input("بريد الطوارئ الموحد لفرق المتابعة", value="emergency@jeddah.gov.sa", key="em_tab3")

    col_btn_a1, col_btn_a2 = st.columns(2)
    with col_btn_a1:
        if st.button("إرسال وبث التنبيه للنظام 🚀", use_container_width=True):
            if alert_title and alert_body:
                st.success(f"تم بث التنبيه العاجل ({alert_title}) بنجاح لكافة القطاعات المعنية!")
            else:
                st.error("يرجى كتابة عنوان الرسالة والنص قبل البث.")

    with col_btn_a2:
        email_subject3 = urllib.parse.quote(f"🚨 إنذار عاجل: {alert_title} - {alert_level}")
        email_body3 = urllib.parse.quote(
            f"تنبيه طارئ صادرة من: {sender_officer}\n"
            f"القطاعات المستهدفة: {', '.join(target_dept)}\n"
            f"مستوى الخطورة: {alert_level}\n\n"
            f"تفاصيل التعليمات الميدانية:\n{alert_body}\n\n"
            f"يرجى الجاهزية والاستجابة السريعة."
        )
        mailto_link3 = f"mailto:{alert_email_target}?subject={email_subject3}&body={email_body3}"
        st.markdown(f'<a href="{mailto_link3}" target="_blank" class="email-btn">بث الإنذار العاجل فوراً عبر Gmail 🚨✉️</a>', unsafe_allow_html=True)

    st.divider()

    st.subheader("📜 سجل التنبيهات والإنذارات النشطة حالياً")
    st.markdown("""
        <div class="alert-card-red">
            <h4 style="color:#f43f5e; margin:0;">🚨 تنبيه طارئ: صيانة وتأهيل المصبات المائية - الكورنيش</h4>
            <small style="color:#94a3b8;">التاريخ: 2026-09-25 | المصدر: إدارة الصيانة والبيئة</small>
            <p style="margin-top:8px;">مطلوب توجه فرقة الصيانة الميدانية فوراً لتدقيق الجاهزية ومتابعة البلاغات بالتنسيق مع مركز التحليلات.</p>
        </div>
        <div class="alert-card-blue">
            <h4 style="color:#38bdf8; margin:0;">🔔 إشعار إداري: الاجتماع الدوري لمراجعة SLA</h4>
            <small style="color:#94a3b8;">التاريخ: 2026-09-24 | المصدر: قسم نظم المعلومات والذكاء الاصطناعي</small>
            <p style="margin-top:8px;">يرجى من كافة رؤوساء الأقسام مراجعة المعاملات ومتابعة الأخطاء الإدارية والإملائية.</p>
        </div>
    """, unsafe_allow_html=True)


# ------------------------------------------
# التبويب الرابع: المساعد الذكي والإرشاد البلدي (AI Copilot)
# ------------------------------------------
with tab4:
    st.subheader("🤖 المساعد الذكي والإرشاد البلدي (AI Copilot)")
    st.caption("مساعدك التفاعلي للإجابة على استفسارات النظام، صياغة المراسلات الإدارية، وإرسال المخرجات عبر البريد ✉️")

    col_chat1, col_chat2 = st.columns([2, 1])

    with col_chat1:
        st.markdown("### 💬 المحادثة المباشرة مع المساعد")
        
        # عرض سجل المحادثة
        for msg in st.session_state['chat_history']:
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                st.chat_message("assistant").write(msg['content'])

        # استقبال سؤال الموظف
        user_query = st.chat_input("اطرح سؤالك هنا (مثال: صغ لي خطاب توجيهي لمعاملة تأخير صيانة الطرق)...")
        
        if user_query:
            st.session_state['chat_history'].append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            # توليد رد المساعد الذكي
            response = ""
            query_lower = user_query.lower()
            
            if "sla" in query_lower or "مهل" in query_lower or "إنجاز" in query_lower:
                response = "📌 **معايير مهل الإنجاز (SLA) في المنصة:**\n- **المعاملات العاجلة جداً:** 2 أيام عمل.\n- **البلاغات العاجلة:** 3 أيام عمل.\n- **المعاملات الهامة:** 5 أيام عمل.\n- **المعاملات العادية:** 7 أيام عمل."
            elif "خميس" in query_lower or "مساءلة" in query_lower or "اجتماع" in query_lower:
                response = "📅 **اجتماع الخميس للمساءلة:** يُعقد الساعة 12:00 ظهراً لمراجعة المعاملات غير المنجزة وتدقيق الأخطاء الإدارية والإملائية وبحث الحلول لتسريع الإنجاز."
            elif "سرية" in query_lower or "دخول" in query_lower or "رمز" in query_lower:
                response = "🔒 **إدارة السرية:** المعاملات المحددة كـ (سري) أو (سري للغاية) تحجب تلقائياً عن الزوار، وتتطلب تسجيل الدخول من القائمة الجانبية بواسطة المسؤول."
            else:
                response = f"**خطاب توجيهي / إرشادي بناءً على طلبك:**\n\nإشارة إلى الموضوع: **[{user_query}]**\n\nنفيدكم بضرورة سرعة معالجة المعاملة واستكمال الإجراءات الميدانية طبقاً لدليل حوكمة أمانة جدة ومعايير SLA المعتمدة."

            st.session_state['chat_history'].append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)

        # ✉️ إرسال ملخص المحادثة الأخيرة عبر البريد
        st.markdown("---")
        st.markdown("#### ✉️ توثيق المخرجات والخطابات عبر البريد")
        chat_email_target = st.text_input("أدخل البريد الإلكتروني لإرسال الرد / الخطاب الحالي", value="user@jeddah.gov.sa", key="em_tab4")
        
        last_resp = st.session_state['chat_history'][-1]['content'] if len(st.session_state['chat_history']) > 0 else ""
        
        email_subject4 = urllib.parse.quote("إفادة المساعد الذكي - أمانة محافظة جدة")
        email_body4 = urllib.parse.quote(f"مخرجات الاستفسار والخطاب الإداري:\n\n{last_resp}\n\nصادرة عن منصة أمانة جدة الذكية.")
        mailto_link4 = f"mailto:{chat_email_target}?subject={email_subject4}&body={email_body4}"
        
        st.markdown(f'<a href="{mailto_link4}" target="_blank" class="email-btn">إرسال الرد والخطاب الحالي عبر Gmail ✉️</a>', unsafe_allow_html=True)

    with col_chat2:
        st.markdown("### 📚 دليل الإرشاد والتعليمات")
        
        st.markdown("""
            <div class="guidance-box">
                <b style="color:#38bdf8;">1. دليل حوكمة البيانات:</b><br>
                يلتزم جميع الموظفين بإدخال البيانات بدقة متناهية والتأكد من تحديد درجة السرية المناسبة.
            </div>
            <div class="guidance-box">
                <b style="color:#a855f7;">2. التنبؤ التلقائي SLA:</b><br>
                يعتمد محرك الذكاء الاصطناعي على درجة الأهمية ونوع الجهة لتعيين مهلة الإنجاز التلقائية.
            </div>
            <div class="guidance-box">
                <b style="color:#f43f5e;">3. المساءلة والجودة:</b><br>
                تخضع جميع المعاملات المتأخرة للمراجعة الأسبوعية في اجتماع ظهيرة الخميس.
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 8. التوقيع السفلي
# ==========================================
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #94a3b8; font-size: 0.9rem; padding: 15px;">
        <div style="font-size: 1.1rem; font-weight: bold; color: #f8fafc; margin-bottom: 6px;">
            🏛️ منصة إدارة أمانة محافظة جدة التجريبي
        </div>
        <div style="font-size: 0.8rem; color: #64748b;">
            تنويه: يرجى التأكد من صحة المعلومات والمعطيات ويفضل الفحص اليومي تدريجياً - فكرة أمن المعلومات والتصميم والتطوير المقترح بواسطة Bin3abdAi 🤲❤️‍🩹✨
        </div>
    </div>
""", unsafe_allow_html=True)
# ---------------------------------------------------------
# أدوات الطباعة والتصدير الرسمية للوحة التحكم والتحليلات
# ---------------------------------------------------------
st.markdown("---")
st.markdown("### 🖨️ أدوات التصدير والطباعة الشاملة")

col_p1, col_p2 = st.columns(2)
with col_p1:
    if st.button("📥 تصدير تقرير التحليلات والبيانات (CSV)", use_container_width=True):
        st.success("✅ يتم تجهيز ملف التصدير بنجاح.")
with col_p2:
    if st.button("🖨️ طباعة الصفحة الحالية", use_container_width=True):
        st.info("💡 يمكنك طباعة أو حفظ التقرير بصيغة PDF بالضغط على (Ctrl + P) من لوحة المفاتيح.")
        from ai_service import render_global_ai_copilot_widget
render_global_ai_copilot_widget("اسم الصفحة الحالية")
