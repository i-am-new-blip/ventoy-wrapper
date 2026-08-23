import ctypes
import os
import platform
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

from bs4 import BeautifulSoup

OUTPUT = Path.home() / "ventoy"

class ScrapingError(Exception):
    """Raised when Ventoy version/file scraping fails."""

def elevate():
    if os.name == "posix":
        if os.geteuid() == 0:
            return

        subprocess.run(
            ["sudo", sys.executable, *sys.argv],
            check=True
        )
        sys.exit()

    elif os.name == "nt":
        if ctypes.windll.shell32.IsUserAnAdmin():
            return

        params = subprocess.list2cmdline(sys.argv)

        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            params,
            None,
            1
        )

        if result <= 32:
            raise RuntimeError("Failed to request administrator privileges")

        sys.exit()

    else:
        raise RuntimeError(f"Unsupported OS: {os.name}")

def get_os():
    
    if os.name == "nt":
        return "windows"
    if os.name == "posix":
        return "linux"
    raise RuntimeError(f"Unsupported OS: {os.name}")

def get_github(path):
    p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8")
        
    url = "https://raw.githubusercontent.com/i-am-new-blip/ventoy-wrapper/main/%s" % path

    with urlopen(url) as r:
        return r.read().decode("utf-8")

def get_arch():
    arch = platform.machine().lower()

    if arch in ("x86_64", "amd64"):
        return "x86_64"
    if arch in ("aarch64", "arm64"):
        return "aarch64"
    if arch in ("i386", "i686", "x86"):
        return "i386"
    if arch in ("mips64el",):
        return "mips64el"

    raise RuntimeError("Unsupported architecture: %s" % arch)

def get_version():
  url = "https://sourceforge.net/projects/ventoy/files/"
  
  with urlopen(url) as r:
      text = r.read().decode("utf-8")
  
  soup = BeautifulSoup(text, "html.parser")
  
  row = soup.select_one("#files_list tbody tr")
  
  if row is None:
      raise ScrapingError("Could not find Ventoy file list")
  
  version = row.get("title")
  
  if not version:
      raise ScrapingError("Could not find Ventoy version")
  
  return 'https://sourceforge.net/projects/ventoy/files/%s/' % version

def get_osfile(ver_url = None, os = None):
  if ver_url is None:
    ver_url = get_version()

  if os is None:
    os = get_os()
  
  
  with urlopen(ver_url) as r:
      soup = BeautifulSoup(r.read(), "html.parser")
  
  tbody = soup.select_one("tbody")

  files = [
      tr.get("title","")
      for tr in tbody.find_all("tr")
      if tr.get("title", "").startswith("ventoy-") and 'livecd' not in tr.get("title","")
  ]

  for i in files:
    if os in i:
      return ver_url + i + '/download' 

def download(url=None):
  if url is None:
    url = get_osfile()
  filename = 'ventoy.zip' if 'tar' not in url else 'ventoy.tar.gz'

  home = Path.home()
  output = home / filename
    
  with urlopen(url) as r, open(output, "wb") as f:
    while chunk := r.read(1024 * 1024):
      f.write(chunk)

  return output

def extract(filename=None):
    
    if filename is None:
        filename = download()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    
    if filename.name.endswith(".tar.gz"):
        with tarfile.open(filename, "r:gz") as tar:
            for member in tar.getmembers():
                member.name = "/".join(member.name.split("/")[1:])
                if member.name:
                    tar.extract(member, OUTPUT)
    elif filename.suffix == ".zip":
        with zipfile.ZipFile(filename) as z:
            for member in z.infolist():
                parts = member.filename.split("/", 1)

                if parts[1] == '':
                    continue

                member.filename = parts[1]
                z.extract(member, OUTPUT)

    else:
        raise RuntimeError("Unsupported archive format")

    os.remove(filename)
  
    return filename.name.endswith(".tar.gz")

def install():
    extract()
    wrapper = get_github('wrapper.py')
    win_wrapper = get_github('ventoy.cmd')
    shebang = ''
    
    if get_os() == 'linux':
        shebang = '#!%s\n' % sys.executable
        path = 'VentoyGUI.%s' % get_arch()    
    else:
        path = 'Ventoy2Disk.exe'

    os.chdir(OUTPUT)
    
    with open('wrapper.py','w') as f:
        f.write(wrapper % (shebang, path))

    with open('version.txt','w') as f:
        f.write(get_version())
    
    if get_os() == 'linux':
        local = Path.home() / ".local/bin/ventoy"
        local.parent.mkdir(parents=True, exist_ok=True)
        local.unlink(missing_ok=True)
        local.symlink_to(OUTPUT / "wrapper.py")

        system = Path("/usr/bin/ventoy")
        system.unlink(missing_ok=True)
        system.symlink_to(OUTPUT / "wrapper.py")
    else:
        fancy = Path(os.environ["WINDIR"]) / "ventoy.cmd"
        fancy.write_text(win_wrapper)

def main():
        if get_os() == "linux":
            elevated_path = "/usr/bin/ventoy"
        else:
            elevated_path = r"C:\Windows\ventoy.cmd"
        
        print(
            "\033[33mAsking for elevation because on %s will need to store @ %s, "
            "which needs elevation.\033[0m"
            % (get_os(), elevated_path)
        )
        
        elevate()
        install()
          
        os.execvp('ventoy',['ventoy'])
