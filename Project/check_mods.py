import importlib.util
for mod in ['uvicorn', 'fastapi', 'multipart']:
    print(mod, bool(importlib.util.find_spec(mod)))
