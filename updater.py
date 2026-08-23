import installer
from path import Path

def updater_check():
  vers = installer.get_version()
  cur_vers = (Path.home() / "ventoy" / "version.txt").read_text()
  
  if vers != cur_vers:
    print('updating')
    installer.install()
