import importlib, traceback
importlib.invalidate_caches()
try:
    import data_layer
    print("data_layer imported OK")
except Exception:
    traceback.print_exc()

