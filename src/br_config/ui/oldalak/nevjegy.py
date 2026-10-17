import platform

from PySide6 import __version__ as pyside_verzio
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from br_config import APP_NEV, KESZITO, __version__
from br_config.ui.elemek import Kartya, cimke, gomb
from br_config.ui.kontextus import Kontextus
from br_config.ui.tema import logo_pixmap

GITHUB = "https://github.com/Botirocky/br-config"
WEBOLDAL = "https://botirocky.github.io/br-config/"


class NevjegyOldal(QWidget):
    def __init__(self, ktx: Kontextus):
        super().__init__()
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 24, 0, 0)
        l.setSpacing(16)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(112))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        l.addWidget(logo)
        for szoveg, nev in ((APP_NEV, "cim"), (f"Verzió: {__version__} · Készítő: {KESZITO}", "alcim")):
            c = cimke(szoveg, nev)
            c.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(c)
        leiras = cimke("Nyílt forrású konfigurációs központ Windowsra és Linuxra: gépfelismerés, "
                       "driverek, programtelepítés és tuning egy helyen.", "leiras", sortores=True)
        leiras.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(leiras)
        gombok = QHBoxLayout()
        gombok.addStretch(1)
        for felirat, url, ikon_nev, szerep in (("GitHub", GITHUB, "github", ""),
                                                ("Weboldal", WEBOLDAL, "kulso", "fo")):
            g = gomb(felirat, szerep, ikon_nev)
            g.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            gombok.addWidget(g)
        gombok.addStretch(1)
        l.addLayout(gombok)
        k = Kartya()
        k.setMaximumWidth(520)
        for felirat, ertek in (("Rendszer", ktx.rendszer.nev), ("Python", platform.python_version()),
                               ("Qt / PySide6", pyside_verzio), ("Licenc", "GPL-3.0-or-later")):
            sor = QHBoxLayout()
            sor.addWidget(cimke(felirat, "leiras"))
            sor.addStretch(1)
            sor.addWidget(cimke(ertek))
            k.elrendezes.addLayout(sor)
        tarto = QHBoxLayout()
        tarto.addStretch(1)
        tarto.addWidget(k, 2)
        tarto.addStretch(1)
        l.addLayout(tarto)
        l.addStretch(1)
