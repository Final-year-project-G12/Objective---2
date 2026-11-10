import ansys.fluent.core as pyfluent
s = pyfluent.launch_fluent(product_version="26.1.0", dimension=2, precision="double",
                           processor_count=2, ui_mode="no_gui_or_graphics",
                           start_timeout=120, cwd=r"C:\fluent_work")
try:
    av = s.file.import_.read.file_type.get_attr("allowed-values")
    print("ALLOWED:", av)
except Exception as e:
    print("err:", e)
    try:
        print("ALLOWED2:", s.file.import_.read.file_type.allowed_values())
    except Exception as e2:
        print("err2:", e2)
s.exit()
