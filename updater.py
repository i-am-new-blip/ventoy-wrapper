import installer

INSTALLER_MANAGED=True

def updater_check():
  ver = installer.get_version()
  ventoy, program = (installer.OUTPUT / "version.txt").read_text().split(" : ")

  if ver != ventoy:
    print('updating')
    if INSTALLER_MANAGED:
      installer.install()
    else:
      installer.extract()
      installer.progress(80, "Checking for wrapper updates")
      prog_ver = installer.get_version(installer.WRAPPER_API)
      installer.progress(85, "Sucessfully checked for updates")
      installer.progress(100, "Sucessfully reinstalled")
      
      if prog_ver != program:
        print("\033[1;33m⚠️  Ventoy wrapper update required.\033[0m")
        print("\033[1;33m   Please update it using your package manager.\033[0m")