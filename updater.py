from pathlib import Path

import installer


def updater_check():
  vers = installer.get_version()
  cur_vers = (installer.OUTPUT / "version.txt").read_text()
  
  if vers != cur_vers:
    print('updating')
    installer.install()
