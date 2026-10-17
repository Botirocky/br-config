import json

import pytest

from br_config import gep
from br_config.rendszer import Rendszer, linux_rendszer, os_release_feldolgoz

CACHYOS_OS_RELEASE = """NAME="CachyOS Linux"
PRETTY_NAME="CachyOS"
ID=cachyos
ID_LIKE=arch
# megjegyzés
BUILD_ID=rolling
"""


def test_os_release_feldolgozas_idezojelekkel_es_megjegyzessel():
    adatok = os_release_feldolgoz(CACHYOS_OS_RELEASE)
    assert adatok["ID"] == "cachyos"
    assert adatok["PRETTY_NAME"] == "CachyOS"
    assert "#" not in "".join(adatok)


def test_linux_rendszer_rokonokkal():
    r = linux_rendszer(CACHYOS_OS_RELEASE)
    assert r.linux and not r.windows
    assert r.rokonok == ("arch",)
    assert r.csalad() == "arch"


@pytest.mark.parametrize(("disztro", "rokonok", "csalad"), [
    ("ubuntu", ("debian",), "debian"),
    ("linuxmint", ("ubuntu", "debian"), "debian"),
    ("fedora", (), "fedora"),
    ("opensuse-tumbleweed", ("opensuse", "suse"), "suse"),
    ("manjaro", ("arch",), "arch"),
    ("valami", (), "ismeretlen"),
])
def test_csalad_felismeres(disztro, rokonok, csalad):
    assert Rendszer("linux", disztro, rokonok).csalad() == csalad


def test_windows_csalad(windows):
    assert windows.csalad() == "windows"


@pytest.mark.parametrize(("szoveg", "gyarto"), [
    ("Intel Corporation", "intel"),
    ("NVIDIA Corporation", "nvidia"),
    ("Advanced Micro Devices, Inc. [AMD/ATI]", "amd"),
    ("AMD Radeon RX 7800 XT", "amd"),
    ("Realtek Semiconductor Co., Ltd.", "egyéb"),
    ("Microsoft Basic Display Adapter", "egyéb"),
])
def test_gyarto_felismeres_nem_tevesztheto_ossze(szoveg, gyarto):
    assert gep.gyarto_felismer(szoveg) == gyarto


def test_cpuinfo_intel():
    szoveg = "processor\t: 0\nvendor_id\t: GenuineIntel\nmodel name\t: Intel(R) Core(TM) i5\n"
    assert gep.cpuinfo_feldolgoz(szoveg) == gep.Eszkoz("Intel(R) Core(TM) i5", "intel")


def test_cpuinfo_ures():
    assert gep.cpuinfo_feldolgoz("").gyarto == "ismeretlen"


def test_meminfo():
    assert gep.meminfo_gb("MemTotal:       16303420 kB\nMemFree: 1 kB\n") == 15.5


def test_lspci_valodi_minta(adat):
    eredmeny = gep.lspci_feldolgoz(adat("lspci.txt"))
    assert [g.gyarto for g in eredmeny["gpu"]] == ["intel", "nvidia"]
    assert "RTX 5060" in eredmeny["gpu"][1].nev
    assert len(eredmeny["halozat"]) == 2
    assert len(eredmeny["hang"]) == 2


def test_windows_json_egy_gpu_objektumkent():
    szoveg = json.dumps({
        "cpu": {"Name": "AMD Ryzen 5 5600X 6-Core Processor", "Manufacturer": "AuthenticAMD"},
        "gpu": {"Name": "NVIDIA GeForce RTX 3060", "AdapterCompatibility": "NVIDIA"},
        "halozat": [{"Name": "Intel(R) Wi-Fi 6 AX200", "Manufacturer": "Intel Corporation"}],
        "hang": None,
        "ram": 17179869184,
        "akku": 0,
    })
    info = gep.windows_feldolgoz(szoveg)
    assert info.cpu.gyarto == "amd"
    assert info.van_gpu("nvidia")
    assert info.ram_gb == 16.0
    assert not info.laptop
    assert info.hang == []


def test_windows_json_hianyos():
    info = gep.windows_feldolgoz("{}")
    assert info.gpuk == [] and info.ram_gb == 0.0
