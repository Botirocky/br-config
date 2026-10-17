from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from br_config import driverek
from br_config.ui.elemek import Jelveny, Kartya, cimke, fejlec, gomb
from br_config.ui.kontextus import Kontextus
from br_config.ui.tema import SZIN, ikon


class AttekintesOldal(QWidget):
    def __init__(self, ktx: Kontextus):
        super().__init__()
        self.ktx = ktx
        self.l = QVBoxLayout(self)
        self.l.setContentsMargins(0, 0, 0, 0)
        self.l.setSpacing(14)
        self.l.addWidget(fejlec("Áttekintés",
                                "A BR Config felismerte a gépedet. Itt látod a hardvert és az "
                                "ajánlott drivereket."))
        self.racs = QGridLayout()
        self.racs.setSpacing(12)
        self.l.addLayout(self.racs)
        self.l.addWidget(cimke("DRIVEREK", "szekcio"))
        self.driver_doboz = QVBoxLayout()
        self.driver_doboz.setSpacing(10)
        self.l.addLayout(self.driver_doboz)
        self.l.addStretch(1)
        self._betoltes = cimke("Gép felismerése…", "leiras")
        self.racs.addWidget(self._betoltes, 0, 0)
        ktx.gep_kesz.connect(self._kartyak)
        ktx.telepitett_kesz.connect(self._driverek)
        ktx.futas.connect(self._foglalt)
        self._gombok: list = []
        if ktx.gep is not None:
            self._kartyak()

    def _kartya(self, cim: str, ertek: str, ikon_nev: str, sor: int, oszlop: int) -> None:
        k = Kartya()
        fej = QHBoxLayout()
        kep = QLabel()
        kep.setPixmap(ikon(ikon_nev, SZIN["kiemelt"]).pixmap(18, 18))
        fej.addWidget(kep)
        fej.addWidget(cimke(cim.upper(), "kartyacim"), 1)
        k.elrendezes.addLayout(fej)
        k.elrendezes.addWidget(cimke(ertek, "kartyaertek", sortores=True))
        k.elrendezes.addStretch(1)
        self.racs.addWidget(k, sor, oszlop)

    def _kartyak(self) -> None:
        self._betoltes.hide()
        g, r = self.ktx.gep, self.ktx.rendszer
        if g is None:
            return
        gpuk = "\n".join(x.nev for x in g.gpuk) or "Nem sikerült felismerni"
        kezelok = ", ".join(k.nev for k in self.ktx.kezelok) or "nincs"
        adatok = [
            ("Rendszer", r.nev, "attekintes"),
            ("Processzor", g.cpu.nev, "driver"),
            ("Videókártya", gpuk, "attekintes"),
            ("Memória", f"{g.ram_gb:g} GB" if g.ram_gb else "ismeretlen", "tuning"),
            ("Gép típusa", "Laptop" if g.laptop else "Asztali gép", "inditas"),
            ("Csomagkezelő", kezelok, "programok"),
        ]
        for i, (cim, ertek, ikon_nev) in enumerate(adatok):
            self._kartya(cim, ertek, ikon_nev, i // 3, i % 3)
        for o in range(3):
            self.racs.setColumnStretch(o, 1)
        self._driverek()

    def _driverek(self) -> None:
        if self.ktx.gep is None:
            return
        while (elem := self.driver_doboz.takeAt(0)) is not None:
            if (w := elem.widget()) is not None:
                w.deleteLater()
        self._gombok = []
        lista = driverek.ajanlasok(self.ktx.gep, self.ktx.rendszer, self.ktx.osszes_telepitett(),
                                   self.ktx.fo)
        if not lista:
            self.driver_doboz.addWidget(cimke("Nincs teendő: nem találtam hiányzó drivert.",
                                              "leiras"))
        for a in lista:
            self.driver_doboz.addWidget(self._driver_sor(a))

    def _driver_sor(self, a: driverek.DriverAjanlas) -> Kartya:
        k = Kartya()
        sor = QHBoxLayout()
        sor.setSpacing(14)
        szoveg = QVBoxLayout()
        szoveg.setSpacing(4)
        szoveg.addWidget(cimke(a.nev, "kartyaertek"))
        szoveg.addWidget(cimke(a.leiras, "leiras", sortores=True))
        if a.csomagok:
            szoveg.addWidget(cimke("Csomagok: " + ", ".join(a.csomagok), "leiras", sortores=True))
        sor.addLayout(szoveg, 1)
        if a.telepitve is True:
            sor.addWidget(Jelveny("Telepítve", "ok"), 0, Qt.AlignmentFlag.AlignVCenter)
        elif a.telepitve is False:
            sor.addWidget(Jelveny("Hiányzik", "hiany"), 0, Qt.AlignmentFlag.AlignVCenter)
        if a.url:
            g = gomb("Megnyitás", ikon_nev="kulso")
            g.clicked.connect(lambda _=False, u=a.url: QDesktopServices.openUrl(QUrl(u)))
            sor.addWidget(g, 0, Qt.AlignmentFlag.AlignVCenter)
        elif a.lepesek:
            g = gomb("Telepítés", "fo", "lejatszas")
            g.setToolTip("\n".join(lepes.szoveg() for lepes in a.lepesek))
            g.clicked.connect(lambda _=False, x=a: self.ktx.futtat(x.lepesek, x.nev))
            g.setEnabled(not self.ktx.foglalt)
            self._gombok.append(g)
            sor.addWidget(g, 0, Qt.AlignmentFlag.AlignVCenter)
        k.elrendezes.addLayout(sor)
        return k

    def _foglalt(self, fut: bool) -> None:
        for g in self._gombok:
            g.setEnabled(not fut)
