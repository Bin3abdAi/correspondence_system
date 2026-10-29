from ai_service import Bin3abdAiEngine

# 1. تهيئة المحرك
engine = Bin3abdAiEngine()

# 2. نص معاملة تجريبية
sample_transaction = """
المملكة العربية السعودية - أمانة محافظة جدة
الرقم المرجعي: 1445/8821
الجهة المرسلة: شركة المقاولات الوطنية
الموضوع: طلب صيانة وتعبيد الشوارع وحفريات حي الصفا
التفاصيل: نأمل التكرم بالاطلاع والتعميد بصيانة طريق حي الصفا بشكل عاجل وسري لحساسية الموقع.
"""

print("==================================================")
print("1. بدء اختبار تحليل المعاملة...")
print("==================================================")

try:
    analysis = engine.process_universal_input(sample_transaction, input_type="text")
    print(f"رقم المعاملة: {analysis.extraction.transaction_number}")
    print(f"الموضوع: {analysis.extraction.subject}")
    print(f"التصنيف: {analysis.extraction.ai_category}")
    print(f"مستوى الخطر: {analysis.risk_level.value}")
    print(f"رمز التوجيه الداخلي: {analysis.suggested_routing_code}")
    print(f"المهلة المحددة: {analysis.calculated_sla_hours} ساعة")
    print(f"درجة الثقة: {analysis.ai_confidence_score}%")
except Exception as e:
    print(f"خطأ أثناء التحليل: {e}")

print("\n==================================================")
print("2. اختبار الاستفسار عن المطور والمنشئ...")
print("==================================================")

reply = engine.ask_identity_or_general_question("من طور هذا النظام ومن صاحب التطبيق؟")
print(reply)