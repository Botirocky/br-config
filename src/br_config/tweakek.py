__lazy_modules__ = ["shutil", "tempfile"]

import os
import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from br_config.csomagkezelok import Kezelo
from br_config.folyamat import kimenet
from br_config.lepesek import Lepes, PythonLepes, parancs
from br_config.rendszer import Rendszer, van_program

KATEGORIAK = ("Játék és teljesítmény", "Energia", "Hálózat", "Adatvédelem", "Kényelem",
              "Takarítás")

HKCU = "HKCU"
HKLM = "HKLM"
SEMA_TELJESITMENY = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
SEMA_KIEGYENSULYOZOTT = "381b4222-f694-41f0-9685-ff5bb260df2e"


def _kimenet(argv: list[str]) -> str:
    return kimenet(argv, 20)


def _fajl(utvonal: str) -> str:
    try:
        return Path(utvonal).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def registry_olvas(utvonal: str, nev: str) -> object | None:
    if not sys.platform.startswith("win"):
        return None
    import winreg

    gyoker, _, kulcs = utvonal.partition("\\")
    hive = {HKCU: winreg.HKEY_CURRENT_USER, HKLM: winreg.HKEY_LOCAL_MACHINE}[gyoker]
    try:
        with winreg.OpenKey(hive, kulcs) as k:
            return winreg.QueryValueEx(k, nev)[0]
    except OSError:
        return None


@dataclass(slots=True)
class Kornyezet:
    rendszer: Rendszer
    kezelo: Kezelo | None = None
    kimenet: Callable[[list[str]], str] = _kimenet
    fajl: Callable[[str], str] = _fajl
    registry: Callable[[str, str], object | None] = registry_olvas
    letezik: Callable[[str], bool] = os.path.exists
    program: Callable[[str], bool] = van_program


type Lepesgyarto = Callable[[Kornyezet], list[Lepes]]


@dataclass(frozen=True, slots=True)
class Tweak:
    id: str
    nev: str
    leiras: str
    kategoria: str
    platform: str
    bekapcsol: Lepesgyarto
    kikapcsol: Lepesgyarto | None = None
    allapot: Callable[[Kornyezet], bool | None] = field(default=lambda k: None)
    elerheto: Callable[[Kornyezet], bool] = field(default=lambda k: True)
    ujrainditas: bool = False

    @property
    def egyszeri(self) -> bool:
        return self.kikapcsol is None

    def tamogatott(self, k: Kornyezet) -> bool:
        return self.platform in ("mind", k.rendszer.os) and self.elerheto(k)


def reg_beallit(utvonal: str, nev: str, tipus: str, ertek: object) -> Lepes:
    return parancs("reg", "add", utvonal, "/v", nev, "/t", tipus, "/d", str(ertek), "/f",
                   root=utvonal.startswith(HKLM), leiras=f"{utvonal}\\{nev} = {ertek}")


def reg_torol(utvonal: str, nev: str) -> Lepes:
    return parancs("reg", "delete", utvonal, "/v", nev, "/f", root=utvonal.startswith(HKLM),
                   leiras=f"{utvonal}\\{nev} törlése")


def reg_tweak(id: str, nev: str, leiras: str, kategoria: str, utvonal: str,
              ertekek: list[tuple[str, str, object, object | None]],
              ujrainditas: bool = False) -> Tweak:
    def be(_: Kornyezet) -> list[Lepes]:
        return [reg_beallit(utvonal, n, t, ertek) for n, t, ertek, _ in ertekek]

    def ki(_: Kornyezet) -> list[Lepes]:
        return [reg_torol(utvonal, n) if alap is None else reg_beallit(utvonal, n, t, alap)
                for n, t, _, alap in ertekek]

    def allapot(k: Kornyezet) -> bool:
        return all(str(k.registry(utvonal, n)) == str(ertek) for n, _, ertek, _ in ertekek)

    return Tweak(id, nev, leiras, kategoria, "windows", be, ki, allapot,
                 ujrainditas=ujrainditas)


def drop_in_tweak(id: str, nev: str, leiras: str, kategoria: str, fajl: str, tartalom: str,
                  utana: list[str], visszaallit: list[str],
                  allapot: Callable[[Kornyezet], bool | None] | None = None,
                  elerheto: Callable[[Kornyezet], bool] = lambda k: True) -> Tweak:
    mappa = str(Path(fajl).parent)
    beir = f"mkdir -p {mappa} && printf '{tartalom}' > {fajl}"

    def be(_: Kornyezet) -> list[Lepes]:
        return [parancs("sh", "-c", " && ".join([beir, *utana]), root=True,
                        leiras=f"{fajl} létrehozása")]

    def ki(_: Kornyezet) -> list[Lepes]:
        return [parancs("sh", "-c", " && ".join([f"rm -f {fajl}", *visszaallit]), root=True,
                        leiras=f"{fajl} törlése")]

    return Tweak(id, nev, leiras, kategoria, "linux", be, ki,
                 allapot or (lambda k: k.letezik(fajl)), elerheto)


def _profil(nev: str) -> Lepesgyarto:
    return lambda k: [parancs("powerprofilesctl", "set", nev)]


def _ppd(k: Kornyezet) -> bool:
    return k.program("powerprofilesctl")


def _resolved(k: Kornyezet) -> bool:
    return k.program("resolvectl") and k.letezik("/run/systemd/resolve")


def _tisztit_mappat(mappa: Path) -> str:
    torolt = 0
    if not mappa.is_dir():
        return f"{mappa} nem létezik"
    for elem in mappa.iterdir():
        try:
            if elem.is_dir() and not elem.is_symlink():
                shutil.rmtree(elem)
            else:
                elem.unlink()
            torolt += 1
        except OSError:
            continue
    return f"{torolt} elem törölve: {mappa}"


def _csomag_gyorsitotar(k: Kornyezet) -> list[Lepes]:
    nev = k.kezelo.nev if k.kezelo else ""
    lepesek: list[Lepes] = {
        "pacman": [parancs("pacman", "-Sc", "--noconfirm", root=True)],
        "apt": [parancs("apt-get", "clean", root=True),
                parancs("apt-get", "autoremove", "-y", root=True)],
        "dnf": [parancs("dnf", "clean", "all", root=True)],
        "zypper": [parancs("zypper", "clean", "--all", root=True)],
    }.get(nev, [])
    if k.program("flatpak"):
        lepesek.append(parancs("flatpak", "uninstall", "--user", "--unused", "-y",
                               "--noninteractive"))
    return lepesek


LINUX_TWEAKEK = [
    Tweak("ppd-teljesitmeny", "Teljesítmény energiaprofil",
          "A processzor és a videókártya a legnagyobb sebességen jár. Játékhoz ajánlott.",
          "Játék és teljesítmény", "linux", _profil("performance"), _profil("balanced"),
          lambda k: k.kimenet(["powerprofilesctl", "get"]).strip() == "performance", _ppd),
    Tweak("ppd-takarekos", "Energiatakarékos profil",
          "Kisebb fogyasztás és hosszabb akkumulátoros üzemidő, kisebb teljesítmény árán.",
          "Energia", "linux", _profil("power-saver"), _profil("balanced"),
          lambda k: k.kimenet(["powerprofilesctl", "get"]).strip() == "power-saver", _ppd),
    drop_in_tweak(
        "swappiness", "Kevesebb lapozás (swappiness = 10)",
        "A rendszer tovább tartja a programokat a RAM-ban, így gyorsabban reagál.",
        "Játék és teljesítmény", "/etc/sysctl.d/90-br-config-swappiness.conf",
        "vm.swappiness = 10\\n", ["sysctl -q -w vm.swappiness=10"],
        ["sysctl -q -w vm.swappiness=60"],
        lambda k: k.fajl("/proc/sys/vm/swappiness") == "10"),
    drop_in_tweak(
        "bbr", "TCP BBR torlódáskezelés",
        "A Google BBR algoritmusa gyorsabb és stabilabb hálózatot ad, főleg wifin.",
        "Hálózat", "/etc/sysctl.d/90-br-config-bbr.conf",
        "net.core.default_qdisc = fq\\nnet.ipv4.tcp_congestion_control = bbr\\n",
        ["sysctl -q -w net.core.default_qdisc=fq",
         "sysctl -q -w net.ipv4.tcp_congestion_control=bbr"],
        ["sysctl -q -w net.ipv4.tcp_congestion_control=cubic"],
        lambda k: k.fajl("/proc/sys/net/ipv4/tcp_congestion_control") == "bbr"),
    drop_in_tweak(
        "cloudflare-dns", "Cloudflare DNS (1.1.1.1), titkosítva",
        "Gyors, adatvédelem-barát névfeloldás DNS-over-TLS-sel. A helyi tartományok így is működnek.",
        "Hálózat", "/etc/systemd/resolved.conf.d/90-br-config-dns.conf",
        "[Resolve]\\nDNS=1.1.1.1#cloudflare-dns.com 1.0.0.1#cloudflare-dns.com\\n"
        "DNSOverTLS=opportunistic\\n",
        ["systemctl restart systemd-resolved"], ["systemctl restart systemd-resolved"],
        elerheto=_resolved),
    drop_in_tweak(
        "gyors-leallitas", "Gyorsabb leállítás",
        "Leálláskor legfeljebb 10 másodpercet vár egy beragadt szolgáltatásra (alapból 90-et).",
        "Kényelem", "/etc/systemd/system.conf.d/90-br-config-leallitas.conf",
        "[Manager]\\nDefaultTimeoutStopSec=10s\\n", ["systemctl daemon-reload"],
        ["systemctl daemon-reload"]),
    Tweak("fstrim", "SSD heti TRIM",
          "Hetente jelzi az SSD-nek a szabad blokkokat, így hosszú távon is gyors marad.",
          "Játék és teljesítmény", "linux",
          lambda k: [parancs("systemctl", "enable", "--now", "fstrim.timer", root=True)],
          lambda k: [parancs("systemctl", "disable", "--now", "fstrim.timer", root=True)],
          lambda k: k.kimenet(["systemctl", "is-enabled", "fstrim.timer"]).strip() == "enabled",
          lambda k: k.letezik("/usr/lib/systemd/system/fstrim.timer")
          or k.letezik("/lib/systemd/system/fstrim.timer")),
    Tweak("dns-urites", "DNS-gyorsítótár ürítése",
          "Akkor hasznos, ha egy oldal nem töltődik be, vagy új címre költözött.",
          "Hálózat", "linux", lambda k: [parancs("resolvectl", "flush-caches")],
          elerheto=_resolved),
    Tweak("csomag-gyorsitotar", "Csomag-gyorsítótár takarítása",
          "Törli a letöltött régi csomagfájlokat és a már nem használt Flatpak-futtatókörnyezeteket.",
          "Takarítás", "linux", _csomag_gyorsitotar, elerheto=lambda k: k.kezelo is not None),
    Tweak("naplo", "Rendszernapló rövidítése",
          "A 14 napnál régebbi naplóbejegyzéseket törli.", "Takarítás", "linux",
          lambda k: [parancs("journalctl", "--vacuum-time=14d", root=True)],
          elerheto=lambda k: k.program("journalctl")),
    Tweak("belyegkepek", "Bélyegkép-gyorsítótár törlése",
          "A fájlkezelő előnézeti képeit törli; ezek szükség esetén újra elkészülnek.",
          "Takarítás", "linux",
          lambda k: [PythonLepes(lambda: _tisztit_mappat(Path.home() / ".cache" / "thumbnails"),
                                 "~/.cache/thumbnails ürítése")]),
]

ADV = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

WINDOWS_TWEAKEK = [
    reg_tweak("win-jatekmod", "Windows Játék mód", "A Windows játék közben a játéknak ad elsőbbséget.",
              "Játék és teljesítmény", r"HKCU\Software\Microsoft\GameBar",
              [("AutoGameModeEnabled", "REG_DWORD", 1, 0)]),
    reg_tweak("win-egergyorsitas", "Egérgyorsítás kikapcsolása",
              "Pontosabb célzás: az egér mozgása nem függ a sebességtől.",
              "Játék és teljesítmény", r"HKCU\Control Panel\Mouse",
              [("MouseSpeed", "REG_SZ", 0, 1), ("MouseThreshold1", "REG_SZ", 0, 6),
               ("MouseThreshold2", "REG_SZ", 0, 10)], ujrainditas=True),
    Tweak("win-teljesitmeny", "Nagy teljesítményű energiaséma",
          "A processzor nem lassít vissza, ami játékhoz és munkához jó, akkumulátorról viszont többet fogyaszt.",
          "Energia", "windows",
          lambda k: [parancs("powercfg", "/setactive", SEMA_TELJESITMENY)],
          lambda k: [parancs("powercfg", "/setactive", SEMA_KIEGYENSULYOZOTT)],
          lambda k: SEMA_TELJESITMENY in k.kimenet(["powercfg", "/getactivescheme"]).lower()),
    Tweak("win-hibernalas", "Hibernálás kikapcsolása",
          "Felszabadítja a hiberfil.sys által foglalt, több gigabájtnyi lemezterületet.",
          "Energia", "windows",
          lambda k: [parancs("powercfg", "/hibernate", "off", root=True)],
          lambda k: [parancs("powercfg", "/hibernate", "on", root=True)],
          lambda k: str(k.registry(r"HKLM\SYSTEM\CurrentControlSet\Control\Power",
                                   "HibernateEnabled")) == "0"),
    reg_tweak("win-telemetria", "Telemetria minimalizálása",
              "A Windows csak a szükséges diagnosztikai adatokat küldi el.",
              "Adatvédelem", r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
              [("AllowTelemetry", "REG_DWORD", 0, None)]),
    reg_tweak("win-hirdetes", "Hirdetési azonosító kikapcsolása",
              "Az alkalmazások nem tudnak személyre szabott hirdetést mutatni az azonosítód alapján.",
              "Adatvédelem", r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
              [("Enabled", "REG_DWORD", 0, 1)]),
    reg_tweak("win-bing", "Webes keresés kikapcsolása a Start menüben",
              "A Start menü csak a gépen keres, a beírt szöveg nem kerül a Bingre.",
              "Adatvédelem", r"HKCU\Software\Policies\Microsoft\Windows\Explorer",
              [("DisableSearchBoxSuggestions", "REG_DWORD", 1, None)], ujrainditas=True),
    reg_tweak("win-kiterjesztes", "Fájlkiterjesztések mutatása",
              "Látszik, hogy egy fájl .exe vagy .pdf, így a kártevőket is könnyebb kiszúrni.",
              "Kényelem", ADV, [("HideFileExt", "REG_DWORD", 0, 1)]),
    reg_tweak("win-rejtett", "Rejtett fájlok mutatása", "A fájlkezelő a rejtett fájlokat is mutatja.",
              "Kényelem", ADV, [("Hidden", "REG_DWORD", 1, 2)]),
    reg_tweak("win-sotet", "Sötét mód", "Sötét téma a rendszerben és az alkalmazásokban.",
              "Kényelem", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
              [("AppsUseLightTheme", "REG_DWORD", 0, 1),
               ("SystemUsesLightTheme", "REG_DWORD", 0, 1)]),
    Tweak("win-dns-urites", "DNS-gyorsítótár ürítése",
          "Akkor hasznos, ha egy oldal nem töltődik be, vagy új címre költözött.",
          "Hálózat", "windows", lambda k: [parancs("ipconfig", "/flushdns")]),
    Tweak("win-temp", "Ideiglenes fájlok törlése",
          "Kiüríti a saját TEMP mappádat; a használatban lévő fájlokat kihagyja.",
          "Takarítás", "windows",
          lambda k: [PythonLepes(lambda: _tisztit_mappat(Path(tempfile.gettempdir())),
                                 "TEMP mappa ürítése")]),
    Tweak("win-lomtar", "Lomtár ürítése", "Véglegesen törli a Lomtár tartalmát.",
          "Takarítás", "windows",
          lambda k: [parancs("powershell", "-NoProfile", "-Command",
                             "Clear-RecycleBin -Force -ErrorAction SilentlyContinue")]),
    Tweak("win-dism", "Windows-összetevők takarítása",
          "A DISM törli a régi frissítések maradványait. Ez több percig is tarthat.",
          "Takarítás", "windows",
          lambda k: [parancs("Dism.exe", "/Online", "/Cleanup-Image", "/StartComponentCleanup",
                             root=True)]),
]


def osszes() -> list[Tweak]:
    return [*LINUX_TWEAKEK, *WINDOWS_TWEAKEK]


def tamogatott(k: Kornyezet) -> list[Tweak]:
    return [t for t in osszes() if t.tamogatott(k)]
