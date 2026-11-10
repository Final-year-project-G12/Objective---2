import ansys.fluent.core as pyfluent
s = pyfluent.launch_fluent(product_version="26.1.0", dimension=2, precision="double",
                           processor_count=2, ui_mode="no_gui_or_graphics",
                           start_timeout=120, cwd=r"C:\fluent_work")
try:
    print("file.import_ children:", [a for a in dir(s.file.import_) if not a.startswith('_')])
except Exception as e:
    print("settings import_ missing:", e)
try:
    print("\ncgns children:", [a for a in dir(s.file.import_.cgns) if not a.startswith('_')])
except Exception as e:
    print("cgns missing:", e)
try:
    import inspect
    print("\nsig:", inspect.signature(s.file.import_.cgns.mesh))
    print("doc:", (s.file.import_.cgns.mesh.__doc__ or "")[:800])
except Exception as e:
    print("sig failed:", e)
s.exit()
