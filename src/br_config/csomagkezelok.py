__lazy_modules__ = ["json", "tempfile"]

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from br_config.folyamat import kimenet
from br_config.lepesek import Parancs, parancs
from br_config.rendszer import Rendszer, van_program

FLATHUB = "https://dl.flathub.org/repo/flathub.flatpakrepo"


@dataclass(frozen=True, slots=True)
class Kezelo:
    nev: str
    program: str
    root: bool

    def telepit(self, azonositok: list[str]) -> list[Parancs]:
        if not azonositok:
            return []
        match self.nev:
            case "winget":
                return [parancs("winget", "install", "--exact", "--id", a, "--silent",
                                "--accept-package-agreements", "--accept-source-agreements",
                                leiras=f"{a} telepítése") for a in azonositok]
            case "pacman":
                return [parancs("pacman", "-S", "--needed", "--noconfirm", *azonositok, root=True)]
            case "apt":
                return [parancs("apt-get", "install", "-y", *azonositok, root=True)]
            case "dnf":
                return [parancs("dnf", "install", "-y", *azonositok, root=True)]
            case "zypper":
                return [parancs("zypper", "--non-interactive", "install", *azonositok, root=True)]
            case "flatpak":
                return [
                    parancs("flatpak", "remote-add", "--user", "--if-not-exists", "flathub",
                            FLATHUB, leiras="Flathub forrás hozzáadása"),
                    parancs("flatpak", "install", "--user", "-y", "--noninteractive", "flathub",
                            *azonositok),
                ]
        raise ValueError(f"Ismeretlen csomagkezelő: {self.nev}")

    def eltavolit(self, azonositok: list[str]) -> list[Parancs]:
        if not azonositok:
            return []
        match self.nev:
            case "winget":
                return [parancs("winget", "uninstall", "--exact", "--id", a, "--silent")
                        for a in azonositok]
            case "pacman":
                return [parancs("pacman", "-Rns", "--noconfirm", *azonositok, root=True)]
            case "apt":
                return [parancs("apt-get", "remove", "-y", *azonositok, root=True)]
            case "dnf":
                return [parancs("dnf", "remove", "-y", *azonositok, root=True)]
            case "zypper":
                return [parancs("zypper", "--non-interactive", "remove", *azonositok, root=True)]
            case "flatpak":
                return [parancs("flatpak", "uninstall", "--user", "-y", "--noninteractive",
                                *azonositok)]
        raise ValueError(f"Ismeretlen csomagkezelő: {self.nev}")

    def frissit_mindent(self) -> list[Parancs]:
        match self.nev:
            case "winget":
                return [parancs("winget", "upgrade", "--all", "--silent",
                                "--accept-package-agreements", "--accept-source-agreements")]
            case "pacman":
                return [parancs("pacman", "-Syu", "--noconfirm", root=True)]
            case "apt":
                return [parancs("apt-get", "update", root=True),
                        parancs("apt-get", "upgrade", "-y", root=True)]
            case "dnf":
                return [parancs("dnf", "upgrade", "-y", root=True)]
            case "zypper":
                return [parancs("zypper", "--non-interactive", "update", root=True)]
            case "flatpak":
                return [parancs("flatpak", "update", "--user", "-y", "--noninteractive")]
        raise ValueError(f"Ismeretlen csomagkezelő: {self.nev}")


KEZELOK = {
    "winget": Kezelo("winget", "winget", False),
    "pacman": Kezelo("pacman", "pacman", True),
    "apt": Kezelo("apt", "apt-get", True),
    "dnf": Kezelo("dnf", "dnf", True),
    "zypper": Kezelo("zypper", "zypper", True),
    "flatpak": Kezelo("flatpak", "flatpak", False),
}

CSALAD_KEZELO = {"arch": "pacman", "debian": "apt", "fedora": "dnf", "suse": "zypper",
                 "windows": "winget"}


def fo_kezelo(rendszer: Rendszer) -> Kezelo | None:
    nev = CSALAD_KEZELO.get(rendszer.csalad())
    if nev and van_program(KEZELOK[nev].program):
        return KEZELOK[nev]
    for kezelo in KEZELOK.values():
        if kezelo.nev not in ("flatpak", "winget") and van_program(kezelo.program):
            return kezelo
    return None


def elerheto_kezelok(rendszer: Rendszer) -> list[Kezelo]:
    kezelok = []
    if (fo := fo_kezelo(rendszer)) is not None:
        kezelok.append(fo)
    if rendszer.linux and van_program("flatpak"):
        kezelok.append(KEZELOK["flatpak"])
    return kezelok


def soronkent(szoveg: str) -> set[str]:
    return {s.strip() for s in szoveg.splitlines() if s.strip()}


def winget_export_feldolgoz(szoveg: str) -> set[str]:
    adat = json.loads(szoveg or "{}")
    return {
        csomag.get("PackageIdentifier", "")
        for forras in adat.get("Sources", [])
        for csomag in forras.get("Packages", [])
        if csomag.get("PackageIdentifier")
    }


def telepitett(kezelo: Kezelo) -> set[str]:
    match kezelo.nev:
        case "pacman":
            return soronkent(kimenet(["pacman", "-Qq"]))
        case "apt":
            return soronkent(kimenet(["dpkg-query", "-W", "-f", "${Package}\n"]))
        case "dnf" | "zypper":
            return soronkent(kimenet(["rpm", "-qa", "--qf", "%{NAME}\n"]))
        case "flatpak":
            return soronkent(kimenet(["flatpak", "list", "--app", "--columns=application"]))
        case "winget":
            with tempfile.TemporaryDirectory() as mappa:
                fajl = Path(mappa) / "export.json"
                kimenet(["winget", "export", "-o", str(fajl), "--accept-source-agreements"], 120)
                try:
                    return winget_export_feldolgoz(fajl.read_text(encoding="utf-8-sig"))
                except (OSError, json.JSONDecodeError):
                    return set()
    return set()
