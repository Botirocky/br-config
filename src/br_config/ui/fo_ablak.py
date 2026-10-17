__lazy_modules__ = [
    "br_config.ui.oldalak.attekintes",
    "br_config.ui.oldalak.programok",
    "br_config.ui.oldalak.tuning",
    "br_config.ui.oldalak.inditopult",
    "br_config.ui.oldalak.nevjegy",
]

import sys
from collections.abc import Callable
from importlib import import_module

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from br_config import APP_NEV, KESZITO, __version__
from br_config.ui.elemek import cimke, gomb
from br_config.ui.kontextus import Kontextus
from br_config.ui.tema import SZIN, ikon, logo_ikon, logo_pixmap

OLDALAK = [
    ("attekintes", "Áttekintés", "attekintes", "AttekintesOldal"),
    ("programok", "Programok", "programok", "ProgramokOldal"),
    ("tuning", "Tuning", "tuning", "TuningOldal"),
    ("inditopult", "Indítópult", "inditas", "InditopultOldal"),
    ("nevjegy", "Névjegy", "nevjegy", "NevjegyOldal"),
]


class FoAblak(QMainWindow):
    def __init__(self, ktx: Kontextus):
        super().__init__()
        self.ktx = ktx
        self.setWindowTitle(f"{APP_NEV} {__version__}")
        self.setWindowIcon(logo_ikon())
        self.resize(1180, 780)
        self.setMinimumSize(QSize(900, 600))

        kozep = QWidget()
        fo = QHBoxLayout(kozep)
        fo.setContentsMargins(0, 0, 0, 0)
        fo.setSpacing(0)
        fo.addWidget(self._oldalsav())

        jobb = QSplitter(Qt.Orientation.Vertical)
        jobb.setChildrenCollapsible(False)
        felso = QWidget()
        felso_l = QVBoxLayout(felso)
        felso_l.setContentsMargins(0, 0, 0, 0)
        felso_l.setSpacing(0)
        if ktx.rendszer.windows and not ktx.admin:
            felso_l.addWidget(self._admin_szalag())
        self.lapok = QStackedWidget()
        felso_l.addWidget(self.lapok, 1)
        self.also = QStackedWidget()
        self.also.setVisible(False)
        self.also.setStyleSheet("background: transparent;")
        also_tarto = QWidget()
        also_tarto.setObjectName("alsosav")
        also_tarto.setStyleSheet(f"#alsosav {{ background: {SZIN['hatter']}; border-top: 1px solid "
                                 f"{SZIN['keret']}; }}")
        also_l = QVBoxLayout(also_tarto)
        also_l.setContentsMargins(28, 12, 28, 12)
        also_l.addWidget(self.also)
        self.also_tarto = also_tarto
        also_tarto.hide()
        felso_l.addWidget(also_tarto)
        jobb.addWidget(felso)
        jobb.addWidget(self._naplo_panel())
        jobb.setStretchFactor(0, 4)
        jobb.setStretchFactor(1, 1)
        jobb.setSizes([600, 170])
        fo.addWidget(jobb, 1)
        self.setCentralWidget(kozep)

        self._letrehozva: dict[str, QWidget] = {}
        self._also_savok: dict[str, QWidget] = {}
        ktx.naplo.connect(self.naplo_ir)
        ktx.futas.connect(self._futas)
        ktx.betolt()
        self.valt(0)

    def _oldalsav(self) -> QWidget:
        sav = QWidget()
        sav.setObjectName("oldalsav")
        sav.setFixedWidth(232)
        l = QVBoxLayout(sav)
        l.setContentsMargins(14, 18, 14, 14)
        l.setSpacing(4)
        marka = QHBoxLayout()
        marka.setSpacing(10)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(40))
        logo.setStyleSheet("background: transparent;")
        logo.setAccessibleName(f"{APP_NEV} logó")
        marka.addWidget(logo)
        nevek = QVBoxLayout()
        nevek.setSpacing(0)
        nevek.addWidget(cimke(APP_NEV, "markanev"))
        nevek.addWidget(cimke(f"by {KESZITO}", "keszito"))
        marka.addLayout(nevek, 1)
        l.addLayout(marka)
        l.addSpacing(22)

        self.csoport = QButtonGroup(self)
        self.csoport.setExclusive(True)
        for i, (_, felirat, ikon_nev, _) in enumerate(OLDALAK):
            g = QPushButton(felirat)
            g.setCheckable(True)
            g.setCursor(Qt.CursorShape.PointingHandCursor)
            g.setIcon(ikon(ikon_nev, SZIN["halvany"], SZIN["kiemelt"]))
            g.setIconSize(QSize(20, 20))
            g.setToolTip(f"{felirat} (Ctrl+{i + 1})")
            g.setShortcut(f"Ctrl+{i + 1}")
            self.csoport.addButton(g, i)
            l.addWidget(g)
        self.csoport.idClicked.connect(self.valt)
        l.addStretch(1)

        self.proba = QCheckBox("Próba mód")
        self.proba.setToolTip("Bekapcsolva semmi nem fut le: a BR Config csak kiírja a naplóba, "
                              "milyen parancsokat futtatna.")
        self.proba.setStyleSheet(f"color: {SZIN['halvany']};")
        self.proba.toggled.connect(self._proba)
        l.addWidget(self.proba)
        jogok = "Rendszergazda" if self.ktx.admin else "Normál felhasználó"
        allapot = cimke(f"{self.ktx.rendszer.nev} · {jogok}", "keszito", sortores=True)
        l.addWidget(allapot)
        return sav

    def _admin_szalag(self) -> QWidget:
        tarto = QWidget()
        tl = QVBoxLayout(tarto)
        tl.setContentsMargins(28, 16, 28, 0)
        szalag = QWidget()
        szalag.setObjectName("szalag")
        l = QHBoxLayout(szalag)
        l.setContentsMargins(14, 10, 10, 10)
        kep = QLabel()
        kep.setPixmap(ikon("pajzs", SZIN["figyelem"]).pixmap(18, 18))
        l.addWidget(kep)
        l.addWidget(QLabel("Néhány beállításhoz (driverek, telemetria, hibernálás) rendszergazdai "
                           "jog kell."), 1)
        g = gomb("Újraindítás rendszergazdaként", ikon_nev="pajzs")
        g.clicked.connect(self._admin_ujraindit)
        l.addWidget(g)
        tl.addWidget(szalag)
        return tarto

    def _admin_ujraindit(self) -> None:
        import ctypes
        import subprocess

        argumentumok = subprocess.list2cmdline(sys.argv if getattr(sys, "frozen", False)
                                               else ["-m", "br_config"])
        program = sys.executable
        if getattr(sys, "frozen", False):
            argumentumok = subprocess.list2cmdline(sys.argv[1:])
        kod = ctypes.windll.shell32.ShellExecuteW(None, "runas", program,
                                                              argumentumok, None, 1)
        if kod > 32:
            self.close()

    def _naplo_panel(self) -> QWidget:
        panel = QWidget()
        l = QVBoxLayout(panel)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        fej = QWidget()
        fej.setObjectName("naplofej")
        fl = QHBoxLayout(fej)
        fl.setContentsMargins(16, 6, 10, 6)
        kep = QLabel()
        kep.setPixmap(ikon("naplo", SZIN["halvany"]).pixmap(16, 16))
        fl.addWidget(kep)
        fl.addWidget(QLabel("Napló"))
        self.folyamat = QProgressBar()
        self.folyamat.setRange(0, 0)
        self.folyamat.setFixedWidth(160)
        self.folyamat.setTextVisible(False)
        self.folyamat.hide()
        fl.addSpacing(10)
        fl.addWidget(self.folyamat)
        self.allapot = QLabel("")
        fl.addWidget(self.allapot, 1)
        torles = gomb("Törlés")
        torles.setProperty("szerep", "link")
        fl.addWidget(torles)
        l.addWidget(fej)
        self.naplo = QPlainTextEdit()
        self.naplo.setObjectName("naplo")
        self.naplo.setReadOnly(True)
        self.naplo.setMaximumBlockCount(5000)
        self.naplo.setAccessibleName("Napló")
        self.naplo.setPlaceholderText("Itt jelenik meg minden parancs és a kimenete.")
        torles.clicked.connect(self.naplo.clear)
        l.addWidget(self.naplo, 1)
        return panel

    def naplo_ir(self, szoveg: str) -> None:
        self.naplo.appendPlainText(szoveg)
        sb = self.naplo.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _futas(self, fut: bool) -> None:
        self.folyamat.setVisible(fut)
        self.allapot.setText("Folyamatban…" if fut else "")

    def _proba(self, be: bool) -> None:
        self.ktx.proba = be
        self.naplo_ir("Próba mód bekapcsolva: semmi nem fut le." if be
                      else "Próba mód kikapcsolva.")

    def _oldal(self, kulcs: str, osztaly: str) -> QWidget:
        if kulcs not in self._letrehozva:
            modul = import_module(f"br_config.ui.oldalak.{kulcs}")
            oldal = getattr(modul, osztaly)(self.ktx)
            gorgeto = QScrollArea()
            gorgeto.setWidgetResizable(True)
            gorgeto.setFrameShape(QScrollArea.Shape.NoFrame)
            tarto = QWidget()
            tl = QVBoxLayout(tarto)
            tl.setContentsMargins(28, 24, 28, 24)
            tl.addWidget(oldal)
            gorgeto.setWidget(tarto)
            self.lapok.addWidget(gorgeto)
            self._letrehozva[kulcs] = gorgeto
            also_sav: Callable[[], QWidget] | None = getattr(oldal, "also_sav", None)
            if also_sav is not None:
                w = also_sav()
                self.also.addWidget(w)
                self._also_savok[kulcs] = w
        return self._letrehozva[kulcs]

    def valt(self, index: int) -> None:
        kulcs, _, _, osztaly = OLDALAK[index]
        self.lapok.setCurrentWidget(self._oldal(kulcs, osztaly))
        if (g := self.csoport.button(index)) is not None:
            g.setChecked(True)
        if kulcs in self._also_savok:
            self.also.setCurrentWidget(self._also_savok[kulcs])
            self.also.setVisible(True)
            self.also_tarto.show()
        else:
            self.also_tarto.hide()
