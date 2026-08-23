import ctypes
import json
import os
import platform
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

OUTPUT = Path.home() / "ventoy"

GITHUB_API = "https://api.github.com/repos/ventoy/Ventoy/releases/latest"


class GitHubError(Exception):
    """Raised when fetching Ventoy's GitHub release fails."""

def is_elevated():
  if os.name == 'posix':
    if os.geteuid() == 0:
      return True
    return False
  elif os.name == 'nt':
    if ctypes.windll.shell32.IsUserAnAdmin():
      return True
    return False
  return None

def elevate():
    if os.name == "posix":
        if os.geteuid() == 0:
            return True

        subprocess.run(
            ["sudo", sys.executable, *sys.argv],
            check=True,
        )
        sys.exit()

    elif os.name == "nt":
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True

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

    else:
        raise RuntimeError(f"Unsupported OS: {os.name}")


def get_os():
    if os.name == "nt":
        return "windows"

    if os.name == "posix":
        return "linux"

    raise RuntimeError(f"Unsupported OS: {os.name}")


def get_github(*path):
    p = Path(*path)

    if p.exists():
        return p.read_text(encoding="utf-8")

    url = (
        "https://raw.githubusercontent.com/"
        "i-am-new-blip/ventoy-wrapper/main/"
        + "/".join(path)
    )

    req = Request(
        url,
        headers={"User-Agent": "ventoy-wrapper"},
    )

    with urlopen(req) as r:
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


def get_release():
    req = Request(
        GITHUB_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ventoy-wrapper",
        },
    )

    try:
        with urlopen(req) as r:
            return json.load(r)
    except Exception as e:
        raise GitHubError(
            f"Could not fetch latest Ventoy release: {e}"
        ) from e


def get_version():
    release = get_release()

    version = release.get("tag_name")

    if not version:
        raise GitHubError("Could not find Ventoy version")

    return version


def get_osfile(version=None, os=None):
    release = get_release()

    if version is not None:
        # If you ever want to support a specific release later.
        if version != release.get("tag_name"):
            raise GitHubError(
                "Requested version is not the latest release"
            )

    if os is None:
        os = get_os()

    if os == "linux":
        wanted = ".tar.gz"
    elif os == "windows":
        wanted = ".zip"
    else:
        raise RuntimeError(f"Unsupported OS: {os}")

    for asset in release.get("assets", []):
        name = asset.get("name", "")

        if not name.startswith("ventoy-"):
            continue

        if "livecd" in name.lower():
            continue

        if os == "linux" and not name.endswith("-linux.tar.gz"):
            continue

        if os == "windows" and not name.endswith("-windows.zip"):
            continue

        return asset["browser_download_url"]

    raise GitHubError(
        f"Could not find Ventoy {os} download"
    )


def download(url=None):
    if url is None:
        url = get_osfile()

    filename = (
        "ventoy.tar.gz"
        if url.endswith(".tar.gz")
        else "ventoy.zip"
    )

    output = Path.home() / filename

    req = Request(
        url,
        headers={"User-Agent": "ventoy-wrapper"},
    )

    print(f"Downloading {url}")

    with urlopen(req) as r, open(output, "wb") as f:
        while chunk := r.read(1024 * 1024):
            f.write(chunk)

    return output

def extract(filename=None):
    if filename is None:
        filename = download()

    filename = Path(filename)

    OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if filename.name.endswith(".tar.gz"):
        with tarfile.open(filename, "r:gz") as tar:
            for member in tar.getmembers():
                parts = member.name.split("/", 1)

                if len(parts) != 2 or not parts[1]:
                    continue

                member.name = parts[1]
                tar.extract(member, OUTPUT)

    elif filename.suffix == ".zip":
        with zipfile.ZipFile(filename) as z:
            for member in z.infolist():
                parts = member.filename.split("/", 1)

                if len(parts) != 2 or not parts[1]:
                    continue

                member.filename = parts[1]
                z.extract(member, OUTPUT)

    else:
        raise RuntimeError("Unsupported archive format")

    filename.unlink()

    return filename.name.endswith(".tar.gz")


def install():
    extract()

    wrapper = get_github("wrapper.py")
    win_wrapper = get_github("ventoy.cmd")

    shebang = ""

    if get_os() == "linux":
        shebang = f"#!{sys.executable}\n"
        path = f"VentoyGUI.{get_arch()}"
    else:
        path = "Ventoy2Disk.exe"

    os.chdir(OUTPUT)

    with open("wrapper.py", "w", encoding="utf-8") as f:
        f.write(wrapper % (shebang, path))

    with open("version.txt", "w", encoding="utf-8") as f:
        f.write(get_version())

    if get_os() == "linux":
        local = Path.home() / ".local/bin/ventoy"

        local.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        local.unlink(missing_ok=True)
        local.symlink_to(OUTPUT / "wrapper.py")

        system = Path("/usr/bin/ventoy")

        system.unlink(missing_ok=True)
        system.symlink_to(OUTPUT / "wrapper.py")

    else:
        fancy = Path(os.environ["WINDIR"]) / "ventoy.cmd"
        fancy.write_text(win_wrapper, encoding="utf-8")


def main():
    if get_os() == "linux":
        elevated_path = "/usr/bin/ventoy"
    else:
        elevated_path = r"C:\Windows\ventoy.cmd"

    if not is_elevated():

    	print(
          "\033[33mAsking for elevation because on %s will need "
          "to store @ %s, which needs elevation."
          "\033[0m"
          % (get_os(), elevated_path)
    	)

	elevate()

    install()

    os.execvp("ventoy", ["ventoy"])
