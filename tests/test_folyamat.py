import sys

from br_config import folyamat


def test_utf8_kimenet_valtozatlan():
    assert folyamat.dekodol("helló, ő ű".encode()) == "helló, ő ű"


def test_oem_kodlapos_kimenet_visszaall(monkeypatch):
    monkeypatch.setattr(folyamat, "oem_kodlap", lambda: "cp852")
    assert folyamat.dekodol("Kész: ó".encode("cp852")) == "Kész: ó"


def test_gyermek_python_utf8_kimenetet_ad():
    kornyezet = folyamat.gyermek_kornyezet()
    assert kornyezet["PYTHONIOENCODING"] == "utf-8"
    assert folyamat.kimenet([sys.executable, "-c", "print('árvíztűrő')"]).strip() == "árvíztűrő"


def test_nem_letezo_program_ures_kimenet():
    assert folyamat.kimenet(["br-config-nem-letezo-parancs"]) == ""
