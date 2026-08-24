import installer

def updater_check():
  ver = installer.get_version()
  curr = (installer.OUTPUT / "version.txt").read_text()

  if ver != curr:
    print('updating')
    installer.install()
