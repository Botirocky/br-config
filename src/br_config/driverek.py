from dataclasses import dataclass, field

from br_config.csomagkezelok import KEZELOK, Kezelo
from br_config.gep import GepInfo
from br_config.lepesek import Parancs, parancs
from br_config.rendszer import Rendszer, van_program

LINUX_CSOMAGOK: dict[str, dict[str, list[str]]] = {
    "nvidia": {
        "arch": ["nvidia-open-dkms", "nvidia-utils", "nvidia-settings"],
        "debian": ["nvidia-driver", "firmware-misc-nonfree"],
        "fedora": ["akmod-nvidia", "xorg-x11-drv-nvidia-cuda"],
        "suse": ["nvidia-open-driver-G06-signed-kmp-default"],
    },
    "amd": {
        "arch": ["mesa", "vulkan-radeon", "libva-mesa-driver"],
        "debian": ["mesa-vulkan-drivers", "mesa-va-drivers"],
        "fedora": ["mesa-vulkan-drivers", "mesa-va-drivers"],
        "suse": ["Mesa-dri", "libvulkan_radeon"],
    },
    "intel": {
        "arch": ["mesa", "vulkan-intel", "intel-media-driver"],
        "debian": ["mesa-vulkan-drivers", "intel-media-va-driver"],
        "fedora": ["mesa-vulkan-drivers", "intel-media-driver"],
        "suse": ["Mesa-dri", "libvulkan_intel", "intel-media-driver"],
    },
}

MIKROKOD = {
    "intel": {"arch": ["intel-ucode"], "debian": ["intel-microcode"], "fedora": ["microcode_ctl"],
              "suse": ["ucode-intel"]},
    "amd": {"arch": ["amd-ucode"], "debian": ["amd64-microcode"], "fedora": ["linux-firmware"],
            "suse": ["ucode-amd"]},
}

FIRMWARE = {"arch": ["linux-firmware"], "debian": ["firmware-linux"], "fedora": ["linux-firmware"],
            "suse": ["kernel-firmware-all"]}

WINDOWS_LINKEK = {
    "nvidia": "https://www.nvidia.com/hu-hu/software/nvidia-app/",
    "amd": "https://www.amd.com/en/support/download/drivers.html",
    "intel": "https://www.intel.com/content/www/us/en/support/detect.html",
}

GYARTO_NEV = {"nvidia": "NVIDIA", "amd": "AMD", "intel": "Intel"}


@dataclass(slots=True)
class DriverAjanlas:
    nev: str
    leiras: str
    csomagok: list[str] = field(default_factory=list)
    lepesek: list[Parancs] = field(default_factory=list)
    url: str = ""
    telepitve: bool | None = None


def _csomag_ajanlas(nev: str, leiras: str, csomagok: list[str], kezelo: Kezelo | None,
                    telepitett: set[str]) -> DriverAjanlas:
    hianyzo = [c for c in csomagok if c not in telepitett]
    lepesek = kezelo.telepit(hianyzo) if kezelo and hianyzo else []
    return DriverAjanlas(nev, leiras, csomagok, lepesek,
                         telepitve=not hianyzo if telepitett else None)


def linux_ajanlasok(gep: GepInfo, rendszer: Rendszer, telepitett: set[str],
                    kezelo: Kezelo | None = None) -> list[DriverAjanlas]:
    csalad = rendszer.csalad()
    kezelo = kezelo or KEZELOK.get({"arch": "pacman", "debian": "apt", "fedora": "dnf",
                                    "suse": "zypper"}.get(csalad, ""))
    ajanlasok: list[DriverAjanlas] = []
    if rendszer.disztro == "cachyos" and van_program("chwd"):
        ajanlasok.append(DriverAjanlas(
            "CachyOS automatikus hardverbeállítás",
            "A chwd felismeri a hardvert, és a CachyOS által ajánlott drivereket telepíti.",
            lepesek=[parancs("chwd", "-a", root=True)]))
    elif csalad == "debian" and van_program("ubuntu-drivers"):
        ajanlasok.append(DriverAjanlas(
            "Ubuntu ajánlott driverek",
            "Az ubuntu-drivers felismeri a hiányzó zárt drivereket, és telepíti őket.",
            lepesek=[parancs("ubuntu-drivers", "install", root=True)]))
    gyartok = list(dict.fromkeys(g.gyarto for g in gep.gpuk if g.gyarto in LINUX_CSOMAGOK))
    for gyarto in gyartok:
        csomagok = LINUX_CSOMAGOK[gyarto].get(csalad)
        if not csomagok:
            continue
        nevek = ", ".join(g.nev for g in gep.gpuk if g.gyarto == gyarto)
        leiras = f"Felismert videókártya: {nevek}."
        if gyarto == "nvidia":
            leiras += " A nyílt kernelmodul a Turing (GTX 16xx / RTX 20xx) és újabb kártyákhoz való."
            if csalad == "fedora":
                leiras += " Ehhez az RPM Fusion tároló kell."
        ajanlasok.append(_csomag_ajanlas(f"{GYARTO_NEV[gyarto]} grafikus driver", leiras,
                                         csomagok, kezelo, telepitett))
    if (kod := MIKROKOD.get(gep.cpu.gyarto, {}).get(csalad)) is not None:
        ajanlasok.append(_csomag_ajanlas(
            f"{GYARTO_NEV[gep.cpu.gyarto]} processzor-mikrokód",
            f"Biztonsági és stabilitási javítások a processzorhoz ({gep.cpu.nev}).",
            kod, kezelo, telepitett))
    if (fw := FIRMWARE.get(csalad)) is not None:
        ajanlasok.append(_csomag_ajanlas(
            "Linux firmware", "Wifi-, Bluetooth- és egyéb eszközök firmware-je.", fw, kezelo,
            telepitett))
    return ajanlasok


def windows_ajanlasok(gep: GepInfo) -> list[DriverAjanlas]:
    ajanlasok = [DriverAjanlas(
        "Windows Update driverek",
        "A legtöbb drivert a Windows Update telepíti; itt nézd meg az opcionális frissítéseket.",
        url="ms-settings:windowsupdate-optionalupdates")]
    for gyarto in dict.fromkeys(g.gyarto for g in gep.gpuk):
        if gyarto in WINDOWS_LINKEK:
            nevek = ", ".join(g.nev for g in gep.gpuk if g.gyarto == gyarto)
            ajanlasok.append(DriverAjanlas(
                f"{GYARTO_NEV[gyarto]} grafikus driver",
                f"Felismert videókártya: {nevek}. A gyártó hivatalos oldala nyílik meg.",
                url=WINDOWS_LINKEK[gyarto]))
    if gep.cpu.gyarto == "intel" and "intel" not in {g.gyarto for g in gep.gpuk}:
        ajanlasok.append(DriverAjanlas(
            "Intel Driver & Support Assistant",
            "Az Intel lapkakészlet-, wifi- és Bluetooth-drivereit kezeli.",
            url=WINDOWS_LINKEK["intel"]))
    return ajanlasok


def ajanlasok(gep: GepInfo, rendszer: Rendszer, telepitett: set[str],
              kezelo: Kezelo | None = None) -> list[DriverAjanlas]:
    if rendszer.windows:
        return windows_ajanlasok(gep)
    return linux_ajanlasok(gep, rendszer, telepitett, kezelo)
