%simport os
from pathlib import Path

import sys

base = %s
target = base / "%s"
  
import updater
updater.updater_check()
  
os.chdir(base)
if os.name == "nt":
    import subprocess, ctypes
    
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print(
            f"\033[33mAsking for elevation because on {get_os()} will need "
            f"to store @ {elevated_path}, which needs elevation."
            "\033[0m"
        )
        
        params = subprocess.list2cmdline(sys.argv)

        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            params,
            None,
            1,
        )

        if result <= 32:
            raise RuntimeError("Failed to request administrator privileges")

        sys.exit()
        
    
    subprocess.Popen(
        [str(target), *sys.argv[1:]],
        cwd=base,
    )
    sys.exit(0)
else:
    os.execv(str(target), [str(target), *sys.argv[1:]])
