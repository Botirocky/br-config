__lazy_modules__ = ["configparser"]

import configparser
import os
import sys
from dataclasses import dataclass
from pathlib import Path

RUN_KULCS = r"Software\Microsoft\Windows\CurrentVersion\Run"
JOVAHAGYOTT = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
BEKAPCSOLT = bytes([2]) + bytes(11)
KIKAPCSOLT = bytes([3]) + bytes(11)


@dataclass(slots=True)
class InditasiElem:
    azonosito: str
    nev: str
    parancs: str
    engedelyezve: bool
    forras: str
    modosithato: bool = True


class _DesktopFajl(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr


def _desktop_olvas(fajl: Path) -> configparser.ConfigParser | None:
    p = _DesktopFajl(interpolation=None, strict=False)
    try:
        p.read(fajl, encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return None
    return p if p.has_section("Desktop Entry") else None


def _engedelyezett(p: configparser.ConfigParser) -> bool:
    bejegyzes = p["Desktop Entry"]
    if bejegyzes.get("Hidden", "false").lower() == "true":
        return False
    return bejegyzes.get("X-GNOME-Autostart-enabled", "true").lower() != "false"


class LinuxInditas:
    def __init__(self, felhasznaloi: Path | None = None, rendszer: list[Path] | None = None):
        konfig = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.felhasznaloi = felhasznaloi or konfig / "autostart"
        self.rendszer = rendszer if rendszer is not None else [Path("/etc/xdg/autostart")]

    def lista(self) -> list[InditasiElem]:
        elemek: dict[str, InditasiElem] = {}
        for mappa, forras in [*((m, "rendszer") for m in self.rendszer),
                              (self.felhasznaloi, "felhasználói")]:
            if not mappa.is_dir():
                continue
            for fajl in sorted(mappa.glob("*.desktop")):
                if (p := _desktop_olvas(fajl)) is None:
                    continue
                b = p["Desktop Entry"]
                elozo = elemek.get(fajl.name)
                elemek[fajl.name] = InditasiElem(
                    fajl.name,
                    b.get("Name") or (elozo.nev if elozo else fajl.stem),
                    b.get("Exec") or (elozo.parancs if elozo else ""),
                    _engedelyezett(p),
                    elozo.forras if elozo else forras,
                )
        return sorted(elemek.values(), key=lambda e: e.nev.lower())

    def _rendszer_fajl(self, nev: str) -> Path | None:
        for mappa in self.rendszer:
            if (mappa / nev).is_file():
                return mappa / nev
        return None

    def beallit(self, azonosito: str, engedelyezve: bool) -> None:
        sajat = self.felhasznaloi / azonosito
        rendszer = self._rendszer_fajl(azonosito)
        if engedelyezve and rendszer is not None and sajat.is_file():
            p = _desktop_olvas(sajat)
            if p is not None and set(p["Desktop Entry"]) <= {"Hidden", "Name", "Exec", "Type"}:
                sajat.unlink()
                return
        forras = sajat if sajat.is_file() else rendszer
        if forras is None:
            raise FileNotFoundError(azonosito)
        p = _desktop_olvas(forras)
        if p is None:
            raise ValueError(f"Hibás .desktop fájl: {forras}")
        b = p["Desktop Entry"]
        b["Hidden"] = "false" if engedelyezve else "true"
        if "X-GNOME-Autostart-enabled" in b:
            b["X-GNOME-Autostart-enabled"] = "true" if engedelyezve else "false"
        self.felhasznaloi.mkdir(parents=True, exist_ok=True)
        with sajat.open("w", encoding="utf-8") as f:
            p.write(f, space_around_delimiters=False)


class WindowsInditas:
    def lista(self) -> list[InditasiElem]:
        import winreg

        elemek = []
        for hive, cimke in ((winreg.HKEY_CURRENT_USER, "felhasználói"),
                            (winreg.HKEY_LOCAL_MACHINE, "minden felhasználó")):
            jovahagyas = self._jovahagyasok(hive)
            try:
                with winreg.OpenKey(hive, RUN_KULCS) as k:
                    i = 0
                    while True:
                        try:
                            nev, ertek, _ = winreg.EnumValue(k, i)
                        except OSError:
                            break
                        allapot = jovahagyas.get(nev)
                        elemek.append(InditasiElem(
                            f"{cimke}:{nev}", nev, str(ertek),
                            allapot is None or allapot[:1] != b"\x03", cimke,
                            hive == winreg.HKEY_CURRENT_USER))
                        i += 1
            except OSError:
                continue
        return sorted(elemek, key=lambda e: e.nev.lower())

    @staticmethod
    def _jovahagyasok(hive: int) -> dict[str, bytes]:
        import winreg

        eredmeny = {}
        try:
            with winreg.OpenKey(hive, JOVAHAGYOTT) as k:
                i = 0
                while True:
                    try:
                        nev, ertek, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    if isinstance(ertek, bytes):
                        eredmeny[nev] = ertek
                    i += 1
        except OSError:
            pass
        return eredmeny

    def beallit(self, azonosito: str, engedelyezve: bool) -> None:
        import winreg

        cimke, _, nev = azonosito.partition(":")
        hive = winreg.HKEY_CURRENT_USER if cimke == "felhasználói" else winreg.HKEY_LOCAL_MACHINE
        with winreg.CreateKeyEx(hive, JOVAHAGYOTT, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, nev, 0, winreg.REG_BINARY,
                              BEKAPCSOLT if engedelyezve else KIKAPCSOLT)


def kezelo() -> LinuxInditas | WindowsInditas:
    return WindowsInditas() if sys.platform.startswith("win") else LinuxInditas()
