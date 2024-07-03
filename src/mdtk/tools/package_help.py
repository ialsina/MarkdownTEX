from mdtk.config import packages

def md2tex_package_help():
    onoff_str = "\n" + "\n".join([f"- {el}" for el in packages.on_off]) + "\n"
    functionalities_str = ""
    functionalities_pkg_str = ""
    for functionality, pkglst in packages.functionality.items():
        functionalities_str += f"\n- {functionality}"
        pkglst_str = "\n".join([f"    - {el}" for el in pkglst])
        functionalities_pkg_str += f"\n- {functionality}\n{pkglst_str}\n"

    functionalities_str += "\n"
    functionalities_pkg_str += "\n"

    lines = [
        f"ON-OFF PACKAGES: {onoff_str}",
        f"FUNCTIONALITIES: {functionalities_str}",
        f"PACKAGES PER FUNCTIONALITY: {functionalities_pkg_str}",
    ]
    print("\n" + "\n".join(lines))