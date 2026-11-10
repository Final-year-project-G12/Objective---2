import ansys.fluent.core as pyfluent
s = pyfluent.launch_fluent(product_version="26.1.0", dimension=2, precision="double",
                           processor_count=2, ui_mode="no_gui_or_graphics",
                           start_timeout=120, cwd=r"C:\fluent_work")
r = s.file.import_.read
print("DOC:", (r.__doc__ or "")[:1200])
try:
    print("ARGS:", r.argument_names)
except Exception as e:
    print("argument_names failed:", e)
s.exit()
