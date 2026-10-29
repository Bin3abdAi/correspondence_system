"""فحص سلامة التركيب: شغّله قبل streamlit بالأمر  python check_install.py
يخبرك بالعربية أي ملف ناقص أو قديم بدل أن تظهر لك رسالة ImportError غامضة."""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["config", "security", "greeting", "nafath", "auth", "database", "data_layer", "table_engine", "fields", "analytics", "charts",
            "floor", "exports", "notifier", "notion_meetings", "ai_service", "voice_assistant", "characters", "system_tools", "ui",
            "views_common", "views_shell", "views_public", "views_staff", "views_admin", "views_pages", "views"]
CHECKS = {"ui": ["dock_buttons", "_light_fix", "nav_buttons", "recolor", "companions", "inject_prefs", "official_footer", "_REACT", "_CMP_JS", "chart_colors", "style_fig"], "characters": ["companions", "_SCENES", "_ENGINE", "_HOVER", "_IDLE", "warm_all", "_lines_for", "_clip_bytes"], "exports": ["play_audio", "speak_ui", "speak_auto", "send_email"], "floor": ["floor_init", "boot_js", "FLOOR_VER"],
          "greeting": ["welcome_speech", "salutation", "hero_user", "style_rule"], "nafath": ["valid_id", "new_request", "account_for"],
          "fields": ["combo_multi", "combo_one"], "table_engine": [], "notifier": ["share_links", "notify", "normalize_phone"],
          "views_shell": ["_filter_options"], "views_public": ["_TAB_LINKS", "render_quick_links"], "views_pages": ["page_header"],
          "security": ["WRITE_ROLES"], "auth": ["verify_2fa", "totp_code"], "analytics": ["sla_summary"],
          "ai_service": ["PERSONAS", "synthesize_speech", "_speech_prep", "CHARACTERS_INFO", "ask_assistant_stream", "_needs_data",
                        "translate_text", "speak_translation", "transcribe_audio", "assistant_voice", "LANGUAGES"], "views": ["render_page", "render_fab", "render_sidebar"],
          "views_common": ["open_page", "go_tab", "run_pending_tab", "speak_now", "scroll_to_page", "link_btn"]}
bad = 0
for name in REQUIRED:
    if not os.path.exists(name + ".py"):
        print(f"❌ الملف ناقص: {name}.py"); bad += 1; continue
    try:
        mod = importlib.import_module(name)
    except Exception as e:  # noqa: BLE001
        print(f"❌ {name}.py فيه خطأ أو نسخته قديمة: {type(e).__name__}: {e}"); bad += 1; continue
    for attr in CHECKS.get(name, []):
        if not hasattr(mod, attr):
            print(f"❌ {name}.py قديم: ينقصه «{attr}» (استبدله بالنسخة الجديدة)"); bad += 1
print("✅ كل الملفات سليمة" if not bad else f"⚠️ عدد المشكلات: {bad}")
