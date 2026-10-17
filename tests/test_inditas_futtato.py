import sys

import pytest

from br_config import futtato
from br_config.futtato import FuttatasiHiba, Futtato, csoportosit, emelt_argv
from br_config.inditas import LinuxInditas
from br_config.lepesek import PythonLepes, parancs


@pytest.fixture
def mappak(tmp_path):
    felh, rendszer = tmp_path / "felh", tmp_path / "rendszer"
    rendszer.mkdir()
    (rendszer / "nm-applet.desktop").write_text(
        "[Desktop Entry]\nName=Hálózat\nExec=nm-applet\nType=Application\n", encoding="utf-8")
    return LinuxInditas(felh, [rendszer]), felh, rendszer


def test_rendszer_elem_listazasa(mappak):
    kezelo, _, _ = mappak
    [elem] = kezelo.lista()
    assert (elem.nev, elem.engedelyezve, elem.forras) == ("Hálózat", True, "rendszer")


def test_rendszer_elem_kikapcsolasa_felulirassal(mappak):
    kezelo, felh, rendszer = mappak
    kezelo.beallit("nm-applet.desktop", False)
    assert "Hidden=true" in (felh / "nm-applet.desktop").read_text(encoding="utf-8")
    assert "Hidden" not in (rendszer / "nm-applet.desktop").read_text(encoding="utf-8")
    assert kezelo.lista()[0].engedelyezve is False
    kezelo.beallit("nm-applet.desktop", True)
    assert kezelo.lista()[0].engedelyezve is True


def test_sajat_elem_kapcsolgatasa(tmp_path):
    felh = tmp_path / "felh"
    felh.mkdir()
    (felh / "sajat.desktop").write_text(
        "[Desktop Entry]\nName=Saját\nExec=sajat\nX-GNOME-Autostart-enabled=true\n",
        encoding="utf-8")
    kezelo = LinuxInditas(felh, [])
    kezelo.beallit("sajat.desktop", False)
    tartalom = (felh / "sajat.desktop").read_text(encoding="utf-8")
    assert "X-GNOME-Autostart-enabled=false" in tartalom
    assert "Name=Saját" in tartalom
    kezelo.beallit("sajat.desktop", True)
    assert kezelo.lista()[0].engedelyezve


def test_ismeretlen_elem(mappak):
    kezelo, _, _ = mappak
    with pytest.raises(FileNotFoundError):
        kezelo.beallit("nincs.desktop", False)


def test_csoportositas_root_lepeseket_osszevonja():
    lepesek = [parancs("a", root=True), parancs("b", root=True), parancs("c"), parancs("d"),
               parancs("e", root=True)]
    csomagok = csoportosit(lepesek)
    assert [len(c.lepesek) for c in csomagok] == [2, 1, 1, 1]
    assert [c.root for c in csomagok] == [True, False, False, True]


def test_emelt_argv_egyetlen_jelszokeres():
    argv = emelt_argv([parancs("pacman", "-S", "vlc", root=True),
                       parancs("sh", "-c", "echo 'x y'", root=True)])
    assert argv[:3] == ["pkexec", "sh", "-c"]
    assert argv[3] == "pacman -S vlc && sh -c 'echo '\"'\"'x y'\"'\"''"


def test_proba_mod_nem_futtat(arch):
    sorok = []
    hivasok = []
    lepes = PythonLepes(lambda: hivasok.append(1), "teszt")
    assert Futtato(arch, sorok.append, proba=True).futtat([lepes, parancs("false")])
    assert hivasok == []
    assert sorok[-1] == "Kész."


def test_valodi_futtatas_kimenettel(arch):
    sorok = []
    ok = Futtato(arch, sorok.append).futtat([
        parancs(sys.executable, "-c", "print('helló')"),
        PythonLepes(lambda: "beépített kész", "teszt"),
    ])
    assert ok
    assert "helló" in sorok and "beépített kész" in sorok


def test_hibas_parancs_megszakit(arch):
    sorok = []
    ok = Futtato(arch, sorok.append).futtat([
        parancs(sys.executable, "-c", "raise SystemExit(3)"),
        parancs(sys.executable, "-c", "print('nem fut le')"),
    ])
    assert not ok
    assert any("3 kóddal" in s for s in sorok)
    assert "nem fut le" not in sorok


def test_nincs_emelo(monkeypatch):
    monkeypatch.setattr(futtato, "van_program", lambda p: False)
    with pytest.raises(FuttatasiHiba):
        futtato.linux_emelo()
