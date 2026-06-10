import importlib
names = ['multipart', 'python_multipart', 'multipart.multipart']
for name in names:
    try:
        importlib.import_module(name)
        print('import ok', name)
    except Exception as e:
        print('import fail', name, e)
