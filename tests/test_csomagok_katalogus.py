import json

import pytest

from br_config import csomagkezelok, katalogus
from br_config.csomagkezelok import KEZELOK


def test_pacman_egy_rootos_parancs():
    lepesek = KEZELOK["pacman"].telepit(["firefox", "git"])
    assert len(lepesek) == 1
    assert lepesek[0].root
    assert lepesek[0].argv == ("pacman", "-S", "--needed", "--noconfirm", "firefox", "git")


def test_winget_programonkent_kulon_parancs_rendszergazda_nelkul():
    lepesek = KEZELOK["winget"].telepit(["Mozilla.Firefox", "Git.Git"])
    assert [l.argv[4] for l in lepesek] == ["Mozilla.Firefox", "Git.Git"]
    assert not any(l.root for l in lepesek)


def test_flatpak_felhasznaloi_es_flathubot_ad():
    lepesek = KEZELOK["flatpak"].telepit(["org.videolan.VLC"])
    assert "remote-add" in lepesek[0].argv
    assert all("--user" in l.argv for l in lepesek)


@pytest.mark.parametrize("nev", list(KEZELOK))
def test_ures_lista_nem_ad_parancsot(nev):
    assert KEZELOK[nev].telepit([]) == []
    assert KEZELOK[nev].eltavolit([]) == []
    assert KEZELOK[nev].frissit_mindent()


def test_winget_export_feldolgozas():
    szoveg = json.dumps({"Sources": [{"Packages": [{"PackageIdentifier": "Git.Git"},
                                                   {"PackageIdentifier": "Valve.Steam"}]}]})
    assert csomagkezelok.winget_export_feldolgoz(szoveg) == {"Git.Git", "Valve.Steam"}


def test_fo_kezelo_csalad_szerint(monkeypatch, ubuntu):
    monkeypatch.setattr(csomagkezelok, "van_program", lambda p: p in ("apt-get", "flatpak"))
    assert csomagkezelok.fo_kezelo(ubuntu) == KEZELOK["apt"]
    assert [k.nev for k in csomagkezelok.elerheto_kezelok(ubuntu)] == ["apt", "flatpak"]


def test_fo_kezelo_ha_nincs_semmi(monkeypatch, arch):
    monkeypatch.setattr(csomagkezelok, "van_program", lambda p: False)
    assert csomagkezelok.fo_kezelo(arch) is None


def test_katalogus_ervenyes():
    programok = katalogus.betolt()
    assert len(programok) >= 25
    assert len({p.id for p in programok}) == len(programok)
    for p in programok:
        assert p.azonositok, p.id
        assert p.nev and p.kategoria and p.leiras


def test_forras_a_nativ_kezelot_elonyben_reszesiti():
    vlc = next(p for p in katalogus.betolt() if p.id == "vlc")
    kezelo, azonosito = vlc.forras([KEZELOK["pacman"], KEZELOK["flatpak"]])
    assert (kezelo.nev, azonosito) == ("pacman", "vlc")
    chrome = next(p for p in katalogus.betolt() if p.id == "chrome")
    assert chrome.forras([KEZELOK["pacman"], KEZELOK["flatpak"]])[0].nev == "flatpak"
    assert chrome.forras([KEZELOK["pacman"]]) is None


def test_csoportositas_kezelonkent():
    programok = [p for p in katalogus.betolt() if p.id in ("vlc", "chrome", "git")]
    csoportok = katalogus.csoportosit(programok, [KEZELOK["pacman"], KEZELOK["flatpak"]])
    assert sorted(csoportok[KEZELOK["pacman"]]) == ["git", "vlc"]
    assert csoportok[KEZELOK["flatpak"]] == ["com.google.Chrome"]
