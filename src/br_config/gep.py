__lazy_modules__ = ["json", "subprocess"]

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from br_config.rendszer import Rendszer, felismer, van_program

GYARTOK = {
    "nvidia": ("nvidia", "10de"),
    "amd": ("advanced micro devices", "amd", "ati technologies", "ati", "1002", "radeon"),
    "intel": ("intel", "8086"),
}


@dataclass(frozen=True, slots=True)
class Eszkoz:
    nev: str
    gyarto: str


@dataclass(slots=True)
class GepInfo:
    cpu: Eszkoz = field(default_factory=lambda: Eszkoz("Ismeretlen processzor", "ismeretlen"))
    gpuk: list[Eszkoz] = field(default_factory=list)
    halozat: list[Eszkoz] = field(default_factory=list)
    hang: list[Eszkoz] = field(default_factory=list)
    ram_gb: float = 0.0
    laptop: bool = False

    def van_gpu(self, gyarto: str) -> bool:
        return any(g.gyarto == gyarto for g in self.gpuk)


def gyarto_felismer(szoveg: str) -> str:
    szavak = set(re.findall(r"[a-z0-9]+", szoveg.lower()))
    kis = " ".join(re.findall(r"[a-z0-9]+", szoveg.lower()))
    for gyarto, kulcsszavak in GYARTOK.items():
        for k in kulcsszavak:
            if (" " in k and k in kis) or k in szavak:
                return gyarto
    return "egyéb"


def cpuinfo_feldolgoz(szoveg: str) -> Eszkoz:
    nev, gyarto = "", ""
    for sor in szoveg.splitlines():
        kulcs, _, ertek = sor.partition(":")
        kulcs = kulcs.strip()
        if kulcs == "model name" and not nev:
            nev = ertek.strip()
        elif kulcs == "vendor_id" and not gyarto:
            gyarto = ertek.strip()
        elif kulcs in ("Model", "Hardware") and not nev:
            nev = ertek.strip()
    if not nev:
        return Eszkoz("Ismeretlen processzor", "ismeretlen")
    tipus = {"GenuineIntel": "intel", "AuthenticAMD": "amd"}.get(gyarto) or gyarto_felismer(nev)
    return Eszkoz(nev, tipus)


def meminfo_gb(szoveg: str) -> float:
    for sor in szoveg.splitlines():
        if sor.startswith("MemTotal:"):
            kb = int(sor.split()[1])
            return round(kb / 1024 / 1024, 1)
    return 0.0


def lspci_feldolgoz(szoveg: str) -> dict[str, list[Eszkoz]]:
    eredmeny: dict[str, list[Eszkoz]] = {"gpu": [], "halozat": [], "hang": []}
    for sor in szoveg.splitlines():
        reszek = [r for r in sor.split('"') if r.strip()]
        if len(reszek) < 4:
            continue
        osztaly, gyarto, nev = reszek[1].lower(), reszek[2], reszek[3]
        eszkoz = Eszkoz(f"{gyarto} {nev}".strip(), gyarto_felismer(gyarto))
        if any(k in osztaly for k in ("vga", "3d controller", "display controller")):
            eredmeny["gpu"].append(eszkoz)
        elif "network controller" in osztaly or "ethernet" in osztaly:
            eredmeny["halozat"].append(eszkoz)
        elif "audio" in osztaly:
            eredmeny["hang"].append(eszkoz)
    return eredmeny


WINDOWS_LEKERDEZES = (
    "$ErrorActionPreference='SilentlyContinue';"
    "[ordered]@{"
    "cpu=(Get-CimInstance Win32_Processor | Select-Object -First 1 Name,Manufacturer);"
    "gpu=@(Get-CimInstance Win32_VideoController | Select-Object Name,AdapterCompatibility);"
    "halozat=@(Get-CimInstance Win32_NetworkAdapter -Filter 'PhysicalAdapter=True' | "
    "Select-Object Name,Manufacturer);"
    "hang=@(Get-CimInstance Win32_SoundDevice | Select-Object Name,Manufacturer);"
    "ram=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory;"
    "akku=@(Get-CimInstance Win32_Battery).Count"
    "} | ConvertTo-Json -Depth 3 -Compress"
)


def _lista(ertek: object) -> list[dict]:
    if isinstance(ertek, dict):
        return [ertek]
    if isinstance(ertek, list):
        return [e for e in ertek if isinstance(e, dict)]
    return []


def windows_feldolgoz(szoveg: str) -> GepInfo:
    adat = json.loads(szoveg or "{}")
    info = GepInfo()
    cpu = adat.get("cpu") or {}
    if cpu.get("Name"):
        nev = cpu["Name"].strip()
        info.cpu = Eszkoz(nev, gyarto_felismer(f"{cpu.get('Manufacturer', '')} {nev}"))
    for g in _lista(adat.get("gpu")):
        nev = g.get("Name") or ""
        info.gpuk.append(Eszkoz(nev, gyarto_felismer(f"{g.get('AdapterCompatibility', '')} {nev}")))
    for kulcs, cel in (("halozat", info.halozat), ("hang", info.hang)):
        for e in _lista(adat.get(kulcs)):
            nev = e.get("Name") or ""
            cel.append(Eszkoz(nev, gyarto_felismer(f"{e.get('Manufacturer', '')} {nev}")))
    try:
        info.ram_gb = round(int(adat.get("ram") or 0) / 1024**3, 1)
    except (TypeError, ValueError):
        info.ram_gb = 0.0
    info.laptop = int(adat.get("akku") or 0) > 0
    return info


def _olvas(utvonal: str) -> str:
    try:
        return Path(utvonal).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _futtat(argv: list[str]) -> str:
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=30,
                              encoding="utf-8", errors="replace").stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def _linux_gep() -> GepInfo:
    info = GepInfo(
        cpu=cpuinfo_feldolgoz(_olvas("/proc/cpuinfo")),
        ram_gb=meminfo_gb(_olvas("/proc/meminfo")),
        laptop=any(Path("/sys/class/power_supply").glob("BAT*")),
    )
    if van_program("lspci"):
        pci = lspci_feldolgoz(_futtat(["lspci", "-mm"]))
        info.gpuk, info.halozat, info.hang = pci["gpu"], pci["halozat"], pci["hang"]
    return info


def _windows_gep() -> GepInfo:
    kimenet = _futtat(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                       WINDOWS_LEKERDEZES])
    try:
        return windows_feldolgoz(kimenet)
    except json.JSONDecodeError:
        return GepInfo()


def felismer_gep(rendszer: Rendszer | None = None) -> GepInfo:
    rendszer = rendszer or felismer()
    return _windows_gep() if rendszer.windows else _linux_gep()
