"""واجهة التجميع: app.py يستورد من هنا فقط، والمحتوى موزّع حسب الجمهور في ملفات مستقلة:

  views_common.py  مشترك (استيرادات، أدوات، مكوّنات مشتركة)
  views_shell.py   هيكل الصفحة: الشريط الجانبي، الدخول، تنبيهات SLA، الفلاتر، زر إمكانية الوصول
  views_public.py  الزوار والجمهور: تتبّع، مشاريع، بيانات مفتوحة، رأيك، خصوصية، تدريب، الواجهة، المساعد العائم
  views_staff.py   الموظفون: إدخال، فرق ميدانية وتنبؤ، خطابات، المساعد الذكي، GIS
  views_admin.py   المدير: لوحة التحليلات، جودة البيانات، النظام، الحوكمة، الجاهزية
  views_pages.py   الصفحات المستقلة للأزرار: المساعد الكامل، إمكانية الوصول، خدماتي، الدعم، الأسئلة الشائعة

لا تضع منطقاً هنا. أي دالة جديدة تُضاف في ملف جمهورها.
"""
from views_common import *  # noqa: F401,F403
from views_shell import *  # noqa: F401,F403
from views_public import *  # noqa: F401,F403
from views_staff import *  # noqa: F401,F403
from views_admin import *  # noqa: F401,F403
from views_pages import *  # noqa: F401,F403