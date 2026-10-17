import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

KATALOGUS = Path(__file__).resolve().parent.parent / "src" / "br_config" / "katalogus.json"


def _http_ok(url: str) -> bool:
    keres = urllib.request.Request(url, headers={"User-Agent": "br-config-katalogus-ellenor"})
    try:
        with urllib.request.urlopen(keres, timeout=20) as valasz:
            return valasz.status == 200
    except urllib.error.HTTPError:
        return False


def flatpak(azonosito: str) -> bool:
    return _http_ok(f"https://flathub.org/api/v2/appstream/{azonosito}")


def winget(azonosito: str) -> bool:
    utvonal = "/".join(azonosito.split("."))
    url = ("https://api.github.com/repos/microsoft/winget-pkgs/contents/manifests/"
           f"{azonosito[0].lower()}/{utvonal}")
    return _http_ok(url)


def pacman(azonosito: str) -> bool:
    return subprocess.run(["pacman", "-Si", azonosito], capture_output=True).returncode == 0


def main() -> int:
    ellenorok = {"flatpak": flatpak, "winget": winget}
    if shutil.which("pacman"):
        ellenorok["pacman"] = pacman
    hibak = 0
    for elem in json.loads(KATALOGUS.read_text(encoding="utf-8")):
        for kezelo, ellenor in ellenorok.items():
            if (azonosito := elem.get(kezelo)) and not ellenor(azonosito):
                print(f"HIÁNYZIK  {elem['id']:<12} {kezelo:<8} {azonosito}")
                hibak += 1
    print(f"{hibak} hibás azonosító")
    return 1 if hibak else 0


if __name__ == "__main__":
    sys.exit(main())
