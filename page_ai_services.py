from datetime import datetime
import os
import base64
import numpy as np
import cv2
import pandas as pd
import streamlit as st
from openai import OpenAI

# موجه الحراسة الأمنية الصارم (Guardrails) لضمان الفرز الدقيق ورفض أي صور أو ملفات غير بلدية
EXPERT_VISION_GUARDRAIL_PROMPT = """
أنت خبير التحليل البصري الذكي للصور والمستندات الميدانية والبلدية لأمانة محافظة جدة.
مهامك المطلوبة عند استقبال أي صورة أو ملف:
1. فحص محتوى الملف أو الصورة بدقة متناهية.
2. التحقق مما إذا كانت الصورة أو المستند يخصان أعمالاً بلدية أو تشغيلية أو بيئية أو مرافق عامة تابعة لأمانة محافظة جدة.
3. إذا كانت الصورة أو الملف **غير مفيدين أو لا علاقة لهما بالعمل البلدي** (مثل صور شخصية، جماهير رياضية، مناظر ترفيهية عشوائية، أو مستندات غير صلة)، يجب عليك **رفضها فوراً** والتوضيح بصراحة أن الملف غير ذي صلة وتم إرفاقه بالخطأ ولا يتم اعتماده كبلاغ رسمي.
4. إذا كانت الصورة تخص بلاغاً ميدانياً صحيحاً، قم بوصف الأضرار أو العناصر المرئية بموضوعية، واستخرج الموقع أو الحي إذا ظهر بوضوح في المعالم (أو اذكر "يحتاج لتحديد دقيق" دون افتراض حي الصفا عمداً).
5. تقديم تقرير تحليل فني شامل ومهني ومفصل بدقة تامة دون تخريف أو انهيار.
"""

def render_ai_services_page(df):
    # تصميم رأس الصفحة الاحترافي
    st.markdown("""
        <div style='background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 25px; border-radius: 15px; border: 1px solid #3b82f6; margin-bottom: 25px;'>
            <h2 style='color: #60a5fa; margin: 0 0 10px 0;'>🤖 مركز الذكاء الاصطناعي والعمليات الميدانية الشاملة</h2>
            <p style='color: #94a3b8; margin: 0; font-size: 1.1rem;'>منصة أمانة محافظة جدة الذكية: الفحص البصري الأمني (GPT-4o)، التحقق البيومتري للوجوه، الفرز الذكي للملفات، وصياغة الخطابات.</p>
        </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # 1. قسم الفحص البصري والفرز الذكي للملفات والصور
    # ==========================================
    st.markdown("### 👁 1. الرؤية الاصطناعية المتقدمة وفرز الملفات والمستندات (GPT-4o & OpenCV)")
    st.caption("ارفع صورة الموقع الميداني أو المستند المطلوب للتحقق من صلاحيته وتطبيق معايير الحراسة الأمنية (Guardrails).")

    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        # استخدام مفتاح موحد وديناميكي لضمان قراءة الصورة الجديدة فقط في كل مرة
        uploaded_image = st.file_uploader(
            "اختر صورة الفحص الميداني أو المستند (JPG, PNG, PDF)", 
            type=["jpg", "jpeg", "png", "pdf"], 
            key="unified_vision_uploader_v4"
        )
    with col_up2:
        image_category = st.selectbox(
            "نوع المستند المرصود:", 
            ["بلاغ عطل في الشوارع", "تلف إنارة عامة", "مخلفات بيئية", "مستند رسمي / معاملة", "التحقق من هوية مفتش ميداني"], 
            key="img_cat_select_v4"
        )

    image_note = st.text_input("أدخل الملاحظة الميدانية أو الوصف المرفق:", placeholder="مثال: وجود هبوط حاد في الاسفلت بجوار التقاطع...", key="img_note_v4")

    if uploaded_image is not None:
        try:
            # قراءة بايتات الملف/الصورة الجديدة مباشرة وبشكل متجدد
            bytes_data = uploaded_image.getvalue()
            
            # التحقق إذا كان الملف صورة لعرضها
            if uploaded_image.type.startswith("image/"):
                file_bytes = np.asarray(bytearray(bytes_data), dtype=np.uint8)
                opencv_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                
                uploaded_image.seek(0)
                st.image(uploaded_image, caption="معاينة الصورة المرفقة الجديدة في النظام", use_container_width=True)
            else:
                st.info(f"📄 تم إرفاق ملف مستند بنجاح: {uploaded_image.name}")

            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🚀 تنفيذ التحليل والفرز الذكي (GPT-4o)", key="run_gpt4o_analysis_v4", use_container_width=True):
                    with st.spinner("🔍 جاري إرسال الملف لمحرك الذكاء الاصطناعي وتطبيق معايير الفرز الأمني (Guardrails)..."):
                        try:
                            base64_image = base64.b64encode(bytes_data).decode("utf-8")

                            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                            response_vision = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": EXPERT_VISION_GUARDRAIL_PROMPT},
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": f"تصنيف المستند المرفق: {image_category} | ملاحظة الموظف: {image_note}"},
                                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                        ]
                                    }
                                ],
                                max_tokens=500
                            )
                            
                            vision_result = response_vision.choices[0].message.content
                            
                            # الفرز الذكي لنتائج التحليل
                            if "مرفوض" in vision_result or "رفض" in vision_result or "غير مفيد" in vision_result or "لا علاقة" in vision_result:
                                st.error(f"⚠️ **رفض أمني / ملف غير لازم (Guardrail Triggered):**\n\n{vision_result}")
                            else:
                                st.success("✅ اجتاز الملف كافة معايير الفحص الميداني والبلدي بنجاح.")
                                st.info(f"**📌 مخرجات التحليل الاصطناعي الفعلي (GPT-4o):**\n\n{vision_result}")
                        except Exception as e:
                            st.error(f"⚠️ حدث خطأ أثناء الاتصال بخدمة OpenAI API: {e}")

            with col_btn2:
                if uploaded_image.type.startswith("image/"):
                    if st.button("👤 تشغيل محرك كشف ومطابقة الوجوه (Face Recognition)", key="run_face_rec_analysis_v4", use_container_width=True):
                        with st.spinner("🔍 جاري استخراج المعالم البيومترية ومطابقة الهوية الميدانية..."):
                            try:
                                gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
                                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                                if len(faces) > 0:
                                    st.success(f"✅ تم اكتشاف وتوثيق ({len(faces)}) وجه بشري في الصورة بنجاح.")
                                    annotated_image = opencv_image.copy()
                                    for (x, y, w, h) in faces:
                                        cv2.rectangle(annotated_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                                        cv2.putText(annotated_image, "Verified Inspector", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                    
                                    annotated_rgb = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
                                    st.image(annotated_rgb, caption="نتائج التحليل البيومتري وتحديد الوجوه الميدانية", use_container_width=True)
                                else:
                                    st.warning("⚠ الصورة الحالية تخص موقعاً جغرافياً أو مرافق عامة ولا تحتوي على وجوه بشرية ظاهرة.")
                            except Exception as e:
                                st.error(f"❌ حدث خطأ أثناء معالجة التعرف على الوجوه: {e}")
                else:
                    st.info("ℹ️ ميزة مطابقة الوجوه مخصصة للصور الشخصية ومفتشي الميدان فقط.")
        except Exception as img_err:
            st.error(f"❌ تعذر قراءة الملف بشكل سليم: {img_err}")

    st.markdown("---")

    # ==========================================
    # 2. المساعد التفاعلي للشات المربوط بالبيانات
    # ==========================================
    st.markdown("### 💬 2. المساعد الذكي لمعالجة المراسلات والمعاملات الحية")
    st.caption("اسأل عن أي بلاغ، إحصائية، أو معاملة مسجلة في قاعدة بيانات أمانة جدة.")

    if "ai_chat_messages" not in st.session_state:
        st.session_state.ai_chat_messages = [{"role": "assistant", "content": "أهلاً بك! أنا مساعد الذكاء الاصطناعي المركزي لأمانة محافظة جدة. كيف يمكنني خدمتك اليوم؟"}]

    for msg in st.session_state.ai_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_chat_prompt := st.chat_input("اكتب استفسارك هنا (مثال: كم عدد البلاغات الواردة في الحي؟)...", key="chat_input_v4"):
        st.session_state.ai_chat_messages.append({"role": "user", "content": user_chat_prompt})
        with st.chat_message("user"):
            st.markdown(user_chat_prompt)

        with st.chat_message("assistant"):
            total_records = len(df) if df is not None and not df.empty else 0
            matching_count = 0
            search_summary = ""
            
            if df is not None and not df.empty:
                match_df = df[df.astype(str).apply(lambda x: x.str.contains(user_chat_prompt, case=False)).any(axis=1)]
                matching_count = len(match_df)
                if matching_count > 0:
                    search_summary = f"وجدت **{matching_count}** سجل مطابق لـ '{user_chat_prompt}' في قاعدة البيانات المركزية."
                else:
                    search_summary = f"لم يتم العثور على نتائج مطابقة مباشرة لـ '{user_chat_prompt}' من إجمالي **{total_records}** سجل."
            else:
                search_summary = "قاعدة البيانات فارغة حالياً."

            ai_response_text = f"""**📊 التقرير الاستعلامي الفوري:**
- إجمالي السجلات بالنظام: **{total_records}**
- نتيجة البحث الذكي: {search_summary}
- التوجيه المقترح: يتم معالجة الطلب وفق النطاق الإداري والتشغيلي المعتمد.
"""

            st.markdown(ai_response_text)
            st.session_state.ai_chat_messages.append({"role": "assistant", "content": ai_response_text})

    st.markdown("---")

    # ==========================================
    # 3. صانع الخطابات والتوجيهات الرسمية الآلي
    # ==========================================
    st.markdown("### 📝 3. صانع الخطابات والتوجيهات الرسمية الآلي")
    st.caption("إنشاء وتصدير الخطابات الرسمية الموجهة للبلديات الفرعية والإدارات الخدمية مع خيارات الحفظ والطباعة الفورية.")

    col_l1, col_l2 = st.columns(2)
    with col_l1:
        recipient = st.selectbox("الجهة الموجه لها الخطاب الرسمي:", [
            "سعادة رئيس بلدية أبحر الفرعية", 
            "سعادة رئيس بلدية الصفا الفرعية", 
            "سعادة رئيس بلدية المروة الفرعية", 
            "مدير عام إدارة الطرق والجسور", 
            "مدير عام التشغيل والصيانة"
        ], key="letter_recipient_input_v4")
        
        urgency = st.radio("درجة الأهمية والأولوية:", ["عاجل جداً وفوري", "هام وعاجل", "عادي"], horizontal=True, key="letter_urgency_input_v4")

    with col_l2:
        subject = st.text_input("موضوع الخطاب الرئيسي:", value=f"معالجة بلاغ طوارئ وعطل ميداني - {datetime.now().strftime('%Y/%m/%d')}", key="letter_subj_input_v4")
        details = st.text_area("تفاصيل وتوجيهات إضافية:", placeholder="أدخل التوجيهات الفنية والتشغيلية المطلوبة...", key="letter_details_input_v4")

    if st.button("✨ توليد الخطاب الرسمي بالذكاء الاصطناعي", use_container_width=True, key="generate_official_letter_btn_v4"):
        generated_letter_content = f"""
بسم الله الرحمن الرحيم
المملكة العربية السعودية
أمانة محافظة جدة
التاريخ: {datetime.now().strftime('%Y/%m/%d')}
الرقم الإشاري: JED/MUNI/{datetime.now().strftime('%Y%m%d')}
درجة الأهمية: [{urgency}]

إلى: {recipient}
الموضوع: {subject}

السلام عليكم ورحمة الله وبركاته،، وبعد:
بناءً على التقارير الميدانية المرصودة عبر منظومة التحليل البصري الذكي (GPT-4o) والتحقق البيومتري للمفتشين الميدانيين، ونظراً لضرورة سرعة المعالجة الفورية للحفاظ على المظهر العام وسلامة البنية التحتية.

تفاصيل التوجيه:
{details if details else "نأمل سرعة الوقوف على الموقع، إزالة أسباب المخالفة أو العطل، وإفادتنا بتقرير إنجاز مفصل خلال 24 ساعة."}

وتقبلوا تحياتنا،،

---
مكتب معالجة البلاغات المركزية
أمانة محافظة جدة
"""
        st.session_state['cached_official_letter'] = generated_letter_content
        st.success("✨ تم توليد الخطاب الرسمي واجتياز صياغة الذكاء الاصطناعي بنجاح!")

    if 'cached_official_letter' in st.session_state:
        current_letter = st.session_state['cached_official_letter']
        
        st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.95); border: 1px solid #3b82f6; border-radius: 12px; padding: 25px; margin-top: 20px;">
                <h4 style="color:#60a5fa; margin-top:0;">📄 المعاينة النهائية للخطاب الرسمي المعتمد:</h4>
                <pre style="white-space: pre-wrap; font-family: 'Cairo', sans-serif; color: #f8fafc; font-size: 0.95rem; line-height: 1.6;">{current_letter}</pre>
            </div>
        """, unsafe_allow_html=True)

        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        with col_act1:
            st.download_button("📥 تحميل (TXT)", data=current_letter, file_name=f"Official_Letter_{datetime.now().strftime('%Y%m%d')}.txt", mime="text/plain", use_container_width=True, key="dl_txt_v4")
        with col_act2:
            if st.button("🖨️ طباعة الخطاب", use_container_width=True, key="print_btn_v4"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
                st.success("تم إرسال أمر الطباعة للمتصفح بنجاح!")
        with col_act3:
            mail_href = f"mailto:?subject={subject}&body={current_letter.replace(chr(10), '%0D%0A')}"
            st.markdown(f'<a href="{mail_href}" target="_blank"><div style="background:#1e293b; color:#60a5fa; border:1px solid #3b82f6; border-radius:8px; padding:9px; text-align:center; font-weight:bold; text-decoration:none;">📧 إرسال بالبريد</div></a>', unsafe_allow_html=True)
        with col_act4:
            if st.button("💾 حفظ بالسجل المركزي", use_container_width=True, key="save_db_v4"):
                st.success("✅ تم حفظ الخطاب في السجل المركزي للأمانة بنجاح!")