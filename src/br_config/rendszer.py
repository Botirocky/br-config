__lazy_modules__ = ["platform", "shutil"]

import os
import platform
import shutil
import sys
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

ARCH_CSALAD = {"arch", "cachyos", "manjaro", "endeavouros", "garuda", "artix"}
DEBIAN_CSALAD = {"debian", "ubuntu", "linuxmint", "pop", "elementary", "zorin", "kali", "raspbian"}
FEDORA_CSALAD = {"fedora", "rhel", "centos", "rocky", "almalinux", "nobara"}
SUSE_CSALAD = {"opensuse", "opensuse-tumbleweed", "opensuse-leap", "suse", "sles"}


@dataclass(frozen=True, slots=True)
class Rendszer:
    os: str
    disztro: str = ""
    rokonok: tuple[str, ...] = field(default_factory=tuple)
    nev: str = ""
    verzio: str = ""

    @property
    def windows(self) -> bool:
        return self.os == "windows"

    @property
    def linux(self) -> bool:
        return self.os == "linux"

    def csalad(self) -> str:
        azonositok = {self.disztro, *self.rokonok}
        for nev, tagok in (
            ("arch", ARCH_CSALAD),
            ("debian", DEBIAN_CSALAD),
            ("fedora", FEDORA_CSALAD),
            ("suse", SUSE_CSALAD),
        ):
            if azonositok & tagok or any(a.startswith(nev) for a in azonositok if a):
                return nev
        return "windows" if self.windows else "ismeretlen"


def os_release_feldolgoz(szoveg: str) -> dict[str, str]:
    adatok: dict[str, str] = {}
    for sor in szoveg.splitlines():
        sor = sor.strip()
        if not sor or sor.startswith("#") or "=" not in sor:
            continue
        kulcs, ertek = sor.split("=", 1)
        adatok[kulcs.strip()] = ertek.strip().strip('"').strip("'")
    return adatok


def linux_rendszer(os_release: str) -> Rendszer:
    adatok = os_release_feldolgoz(os_release)
    return Rendszer(
        os="linux",
        disztro=adatok.get("ID", "").lower(),
        rokonok=tuple(adatok.get("ID_LIKE", "").lower().split()),
        nev=adatok.get("PRETTY_NAME") or adatok.get("NAME", "Linux"),
        verzio=adatok.get("VERSION_ID", ""),
    )


@cache
def felismer() -> Rendszer:
    if sys.platform.startswith("win"):
        return Rendszer(os="windows", disztro="windows", nev=f"Windows {platform.release()}",
                        verzio=platform.version())
    for utvonal in (Path("/etc/os-release"), Path("/usr/lib/os-release")):
        try:
            return linux_rendszer(utvonal.read_text(encoding="utf-8"))
        except OSError:
            continue
    return Rendszer(os="linux", nev="Linux")


def van_program(nev: str) -> bool:
    return shutil.which(nev) is not None


def rendszergazda() -> bool:
    if sys.platform.startswith("win"):
        import ctypes

        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False
    return os.geteuid() == 0


def konfig_mappa() -> Path:
    if sys.platform.startswith("win"):
        alap = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return alap / "BR Config"
    alap = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return alap / "br-config"
