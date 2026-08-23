%simport os
from path import Path
import sys

def main():
  base = Path.home() / "ventoy"
  target = base / "%s"
  
  if globals().get('updater_verify',True):
    import updater
    updater.updater_check()
  
  os.chdir(base)
  os.execv(target, [str(target), *sys.argv[1:]])
if __name__ == '__main__': main()
