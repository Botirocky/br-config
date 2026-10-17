import pytest

from br_config import driverek, tweakek
from br_config.csomagkezelok import KEZELOK
from br_config.gep import Eszkoz, GepInfo
from br_config.lepesek import PythonLepes


@pytest.fixture
def nvidia_intel_gep():
    return GepInfo(cpu=Eszkoz("Intel Core i7", "intel"),
                   gpuk=[Eszkoz("Intel UHD", "intel"), Eszkoz("NVIDIA RTX 4060", "nvidia")],
                   ram_gb=16.0, laptop=True)


def test_arch_hianyzo_nvidia_csomagokat_telepiti(monkeypatch, arch, nvidia_intel_gep):
    monkeypatch.setattr(driverek, "van_program", lambda p: False)
    lista = driverek.ajanlasok(nvidia_intel_gep, arch, {"nvidia-utils", "mesa"})
    nvidia = next(a for a in lista if a.nev.startswith("NVIDIA"))
    assert nvidia.telepitve is False
    assert nvidia.lepesek[0].argv[-2:] == ("nvidia-open-dkms", "nvidia-settings")
    assert any(a.nev.startswith("Intel processzor") for a in lista)


def test_teljesen_telepitett_ajanlas_nem_ad_lepest(monkeypatch, arch, nvidia_intel_gep):
    monkeypatch.setattr(driverek, "van_program", lambda p: False)
    minden = {c for d in driverek.LINUX_CSOMAGOK.values() for c in d["arch"]}
    minden |= {"intel-ucode", "linux-firmware"}
    for a in driverek.ajanlasok(nvidia_intel_gep, arch, minden):
        assert a.telepitve is True and a.lepesek == []


def test_cachyos_chwd_elso_ha_elerheto(monkeypatch, cachyos, nvidia_intel_gep):
    monkeypatch.setattr(driverek, "van_program", lambda p: p == "chwd")
    elso = driverek.ajanlasok(nvidia_intel_gep, cachyos, set())[0]
    assert elso.lepesek[0].argv == ("chwd", "-a")
    assert elso.lepesek[0].root


def test_windows_gyartoi_linkek(windows, nvidia_intel_gep):
    lista = driverek.ajanlasok(nvidia_intel_gep, windows, set())
    assert lista[0].url.startswith("ms-settings:")
    assert {a.url for a in lista} >= {driverek.WINDOWS_LINKEK["nvidia"],
                                       driverek.WINDOWS_LINKEK["intel"]}
    assert all(not a.lepesek for a in lista)


def _kornyezet(rendszer, **kw):
    alap = dict(kimenet=lambda argv: "", fajl=lambda u: "", registry=lambda u, n: None,
                letezik=lambda u: False, program=lambda p: True)
    alap.update(kw)
    return tweakek.Kornyezet(rendszer, KEZELOK["pacman"], **alap)


def test_platform_szerinti_szures(arch, windows):
    linuxos = tweakek.tamogatott(_kornyezet(arch))
    windowsos = tweakek.tamogatott(_kornyezet(windows))
    assert linuxos and windowsos
    assert all(t.platform == "linux" for t in linuxos)
    assert all(t.platform == "windows" for t in windowsos)


def test_tweak_azonositok_egyediek_es_kategoriak_ismertek():
    osszes = tweakek.osszes()
    assert len({t.id for t in osszes}) == len(osszes)
    assert {t.kategoria for t in osszes} <= set(tweakek.KATEGORIAK)


def test_reg_tweak_be_ki_es_allapot(windows):
    t = next(t for t in tweakek.WINDOWS_TWEAKEK if t.id == "win-telemetria")
    k = _kornyezet(windows, registry=lambda u, n: 0)
    be, ki = t.bekapcsol(k)[0], t.kikapcsol(k)[0]
    assert be.root and be.argv[:2] == ("reg", "add")
    assert ki.argv[:2] == ("reg", "delete")
    assert t.allapot(k) is True
    assert t.allapot(_kornyezet(windows, registry=lambda u, n: None)) is False


def test_hkcu_tweak_nem_kell_rendszergazda(windows):
    t = next(t for t in tweakek.WINDOWS_TWEAKEK if t.id == "win-kiterjesztes")
    assert not any(l.root for l in t.bekapcsol(_kornyezet(windows)))


def test_drop_in_tweak_rootos_shell_es_visszaallitas(arch):
    t = next(t for t in tweakek.LINUX_TWEAKEK if t.id == "swappiness")
    k = _kornyezet(arch, fajl=lambda u: "10")
    be = t.bekapcsol(k)[0]
    assert be.root and be.argv[:2] == ("sh", "-c")
    assert "/etc/sysctl.d/90-br-config-swappiness.conf" in be.argv[2]
    assert "rm -f" in t.kikapcsol(k)[0].argv[2]
    assert t.allapot(k) is True


def test_dns_tweak_csak_resolveddal_elerheto(arch):
    t = next(t for t in tweakek.LINUX_TWEAKEK if t.id == "cloudflare-dns")
    assert not t.tamogatott(_kornyezet(arch, letezik=lambda u: False))
    assert t.tamogatott(_kornyezet(arch, letezik=lambda u: True))


def test_egyszeri_muveletnek_nincs_visszavonasa(arch):
    t = next(t for t in tweakek.LINUX_TWEAKEK if t.id == "belyegkepek")
    assert t.egyszeri
    assert isinstance(t.bekapcsol(_kornyezet(arch))[0], PythonLepes)


def test_tisztit_mappat(tmp_path):
    (tmp_path / "a.png").write_text("x")
    (tmp_path / "almappa").mkdir()
    (tmp_path / "almappa" / "b.png").write_text("y")
    assert tweakek._tisztit_mappat(tmp_path).startswith("2 elem")
    assert not any(tmp_path.iterdir())
