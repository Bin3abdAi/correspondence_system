"""حقول «لوحة المطار»: كل خانة قائمة قابلة للبحث بالكتابة، وتقبل إضافة أي قيمة يدوية.

وظيفة هذا الملف: غلاف رفيع حول st.multiselect / st.selectbox يفعّل accept_new_options (إضافة قيمة بنفسك ثم Enter).
إن كانت نسخة Streamlit قديمة لا تدعمها نرجع تلقائياً للقائمة العادية (قابلة للبحث) بدل أن تنهار الصفحة.
"""
import streamlit as st

HINT_MULTI = "اكتب للبحث أو أضف قيمتك ثم Enter"
HINT_ONE = "اكتب للبحث أو أضف قيمة جديدة"


def combo_multi(label: str, options, key: str, target=None, placeholder: str = HINT_MULTI, help: str = None,
                default=None, allow_new: bool = True):
    """قائمة متعددة الاختيار قابلة للبحث، تقبل قيماً يدوية. تُرجع قائمة القيم المختارة (فارغة = بلا تصفية)."""
    host = target if target is not None else st
    opts = list(options)
    kw = dict(key=key, placeholder=placeholder, help=help)
    if default is not None and key not in st.session_state:
        kw["default"] = default
    if allow_new:
        try:
            return host.multiselect(label, opts, accept_new_options=True, **kw)
        except TypeError:  # نسخة قديمة بلا accept_new_options
            pass
    return host.multiselect(label, opts, **kw)


def combo_one(label: str, options, key: str = None, index=0, target=None, placeholder: str = HINT_ONE,
              help: str = None, allow_new: bool = True):
    """قائمة اختيار واحد قابلة للبحث، تقبل قيمة يدوية. تُرجع النص المختار أو المكتوب."""
    host = target if target is not None else st
    opts = list(options)
    kw = dict(index=index, placeholder=placeholder, help=help)
    if key:
        kw["key"] = key
    if allow_new:
        try:
            return host.selectbox(label, opts, accept_new_options=True, **kw)
        except TypeError:
            pass
    return host.selectbox(label, opts, **kw)
