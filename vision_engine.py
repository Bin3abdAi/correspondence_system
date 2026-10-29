import os
import base64
import streamlit as st
from PIL import Image
from openai import OpenAI
import streamlit as st
import datetime
from PIL import Image

def render_vision_analysis_widget():
    st.markdown("### 👁️ محرك تحليل المستندات والصور الذكي (Vision & OCR)")
    st.caption("التقط أو ارفع صورة الخطاب الميداني أو التقرير لاستخراج التفاصيل وتوقع مهلة الإنجاز (SLA) تلقائياً.")

    uploaded_image = st.file_uploader("اختر صورة الخطاب أو التقرير (JPG, PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption="الصورة المرفوعة للمعاينة", use_container_width=True)

        if st.button("🚀 تحليل الصورة واستخراج البيانات بالذكاء الاصطناعي", use_container_width=True):
            with st.spinner("جاري تحليل الصورة واستخراج النصوص وتوقع مهلة الإنجاز..."):
                # محاكاة تحليل النموذج الذكي واستخراج البيانات
                st.success("✅ تم تحليل الصورة بنجاح واستخراج المعطيات التالية:")
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.info("**موضوع المعاملة المستخرج:** طلب سفلتة وتأهيل طريق فرعي")
                    st.info("**الحي المحدد:** حي الصفا")
                with col_res2:
                    st.warning("**درجة الأهمية المكتشفة:** عاجل")
                    st.success("**مهلة الإنجاز المقترحة (AI SLA):** 2 أيام عمل")

                st.markdown("---")
                st.markdown("🔊 **الاستجابة الصوتية (Text-to-Speech):** *تم استخراج المعاملة بنجاح وتصنيفها كحالة عاجلة في حي الصفا، والمهلة المقترحة يومان عمل.*")

                

def analyze_with_gpt_vision(uploaded_file) -> dict:
    """إرسال الصورة إلى نموذج GPT Vision للتحليل الفعلي والتصنيف."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "is_municipal": False,
            "text": "مفتاح OpenAI API غير متوفر في ملف .env"
        }
    
    try:
        client = OpenAI(api_key=api_key)
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode("utf-8")
        mime_type = uploaded_file.type or "image/jpeg"

        system_prompt = (
            "أنت محلل بصري ذكي متخصص لصالح منصة أمانة محافظة جدة السيادية.\n"
            "مهمتك التأكد أولاً مما إذا كانت الصورة المرفقة تتعلق باختصاصات الشؤون البلدية وأمانة جدة "
            "(مثل: الحفريات، الطرق، التشوه البصري، النظافة، المباني الآيلة للسقوط، الرقابة الميدانية) "
            "أو أنها صورة غير متعلقة إطلاقاً بالأمانة (مثل: مباريات رياضية، مشاهير، صور شخصية، حيوانات، إلخ).\n\n"
            "إذا كانت الصورة لا تخص الشؤون البلدية، ابدأ إجابتك حتماً بعبارة: 'غير متعلق بالعمل البلدي: ' "
            "ثم وضح للمستخدم بأنه ربما تم إدراجها بالخطأ ولا تعني شيئاً للمنصة."
        )

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_VISION_MODEL", "gpt-4o"),
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "حلل هذه الصورة المرفقة واستخرج منها التفاصيل البلدية الميدانية:"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=600
        )

        result_text = response.choices[0].message.content.strip()
        is_municipal = not result_text.startswith("غير متعلق بالعمل البلدي")

        return {
            "is_municipal": is_municipal,
            "text": result_text
        }
    except Exception as e:
        return {
            "is_municipal": False,
            "text": f"حدث خطأ أثناء معالجة النموذج للصورة: {str(e)}"
        }


def render_vision_analysis_widget():
    st.markdown("### 👁️ محرك تحليل المستندات والصور الذكي (Vision & OCR)")
    st.caption("التقط أو ارفع صورة الخطاب الميداني أو التقرير لاستخراج التفاصيل وتوقع مهلة الإنجاز (SLA) تلقائياً.")

    uploaded_image = st.file_uploader("اختر صورة الخطاب أو التقرير", type=["jpg", "jpeg", "png"])

    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption="الصورة المرفوعة للمعايتة", use_container_width=True)

        if st.button("🚀 تحليل الصورة واستخراج البيانات بالذكاء الاصطناعي", use_container_width=True):
            with st.spinner("جاري تحليل الصورة بواسطة نموذج الذكاء الاصطناعي..."):
                analysis_result = analyze_with_gpt_vision(uploaded_image)

            # عرض التنبيه باللون الوردي/الأحمر إذا كانت الصورة لا تخص البلدية
            if not analysis_result["is_municipal"]:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #381521; 
                        border-right: 6px solid #ff4b4b; 
                        color: #ffb3c1; 
                        padding: 16px; 
                        border-radius: 8px; 
                        font-size: 15px; 
                        line-height: 1.6;
                        margin-top: 15px;
                        margin-bottom: 15px;
                    ">
                        ⚠️ <b>تنبيه عدم الاختصاص:</b> هذه الصورة لا تعني الشؤون البلدية أو أمانة جدة، وربما تم إدراجها بالخطأ ولا تؤثر في النظام.<br><br>
                        <b>رأي المحلل البصري:</b><br>{analysis_result['text']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.success("تم تحليل الصورة بنجاح بواسطة النموذج البصري المباشر ✅")
                st.markdown(
                    f"""
                    <div style="
                        background-color: #112233; 
                        border-right: 6px solid #00c853; 
                        color: #e0e0e0; 
                        padding: 16px; 
                        border-radius: 8px; 
                        font-size: 15px; 
                        line-height: 1.6;
                        margin-top: 15px;
                        margin-bottom: 15px;
                    ">
                        <b>📋 مخرجات التقرير البلدي البصري:</b><br><br>
                        {analysis_result['text']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )