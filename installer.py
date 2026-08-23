import requests
import os
from pathlib import Path
from bs4 import BeautifulSoup
import tarfile
import zipfile

class ScrapingError(Exception):
    """Raised when Ventoy version/file scraping fails."""
    pass

def get_os():
    if os.name == "nt":
        return "windows"
    if os.name == "posix":
        return "linux"
    raise RuntimeError(f"Unsupported OS: {os.name}")

def get_version():

  url = "https://sourceforge.net/projects/ventoy/files/"
  
  r = requests.get(url)
  r.raise_for_status()
  
  soup = BeautifulSoup(r.text, "html.parser")
  
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
  
  r = requests.get(ver_url)
  r.raise_for_status()
  
  soup = BeautifulSoup(r.text, "html.parser")
  
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
  
  r = requests.get(url, stream=True, allow_redirects=True)
  r.raise_for_status()

  
  home = Path.home()
  output = home / filename
  
  with open(output, "wb") as f:
    for chunk in r.iter_content(chunk_size=1024 * 1024):
      if chunk:
        f.write(chunk)

  return output

def extract(filename=None):
    if filename is None:
        filename = download()

    output = Path.home() / "ventoy"

    if filename.name.endswith(".tar.gz"):
        with tarfile.open(filename, "r:gz") as tar:
            tar.extractall(output)

    elif filename.suffix == ".zip":
        with zipfile.ZipFile(filename) as zip:
            zip.extractall(output)

    else:
        raise RuntimeError("Unsupported archive format")

    os.remove(filename)
  
    return output

if __name__ == 'installer':
  if globals().get('main',False):
    extract()

    import updater
    updater.update_check()
  
