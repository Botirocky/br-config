from pathlib import Path

import pytest

from br_config.rendszer import Rendszer

ADATOK = Path(__file__).parent / "adatok"


@pytest.fixture
def adat():
    return lambda nev: (ADATOK / nev).read_text(encoding="utf-8")


@pytest.fixture
def arch():
    return Rendszer(os="linux", disztro="arch", nev="Arch Linux")


@pytest.fixture
def cachyos():
    return Rendszer(os="linux", disztro="cachyos", rokonok=("arch",), nev="CachyOS")


@pytest.fixture
def ubuntu():
    return Rendszer(os="linux", disztro="ubuntu", rokonok=("debian",), nev="Ubuntu 24.04")


@pytest.fixture
def windows():
    return Rendszer(os="windows", disztro="windows", nev="Windows 11")
