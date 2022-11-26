import pip
required_modules = ['termcolor', 'pypdfium2']
for module in required_modules:
    try:
        module_obj = __import__(module)
        globals()[module] = module_obj
    except ImportError:
        print("Installing {}".format(module))
        pip.main(['install', module])
