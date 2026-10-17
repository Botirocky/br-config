from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QVBoxLayout, QWidget

from br_config import inditas
from br_config.ui.elemek import Jelveny, Kapcsolo, Kartya, cimke, fejlec, gomb
from br_config.ui.kontextus import Kontextus


class InditopultOldal(QWidget):
    def __init__(self, ktx: Kontextus):
        super().__init__()
        self.ktx = ktx
        self.kezelo = inditas.kezelo()
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(12)
        fej = QHBoxLayout()
        fej.addWidget(fejlec("Indítópult",
                             "Ezek a programok indulnak el bejelentkezéskor. Amit nem használsz, "
                             "kapcsold ki, így gyorsabb lesz a rendszerindítás. A kikapcsolás "
                             "visszafordítható, semmit nem törlök."), 1)
        frissit = gomb("Frissítés", ikon_nev="frissites")
        frissit.clicked.connect(self.betolt)
        fej.addWidget(frissit, 0, Qt.AlignmentFlag.AlignTop)
        l.addLayout(fej)
        self.kartya = Kartya()
        self.kartya.elrendezes.setSpacing(0)
        l.addWidget(self.kartya)
        l.addStretch(1)
        self.betolt()

    def betolt(self) -> None:
        while (elem := self.kartya.elrendezes.takeAt(0)) is not None:
            if (w := elem.widget()) is not None:
                w.deleteLater()
        try:
            elemek = self.kezelo.lista()
        except OSError as e:
            elemek = []
            self.ktx.naplo.emit(f"Az indítópult nem olvasható: {e}")
        if not elemek:
            self.kartya.elrendezes.addWidget(cimke("Nincs automatikusan induló program.", "leiras"))
        for i, e in enumerate(elemek):
            if i:
                v = QWidget()
                v.setFixedHeight(1)
                v.setStyleSheet("background: #334155;")
                self.kartya.elrendezes.addWidget(v)
            self.kartya.elrendezes.addWidget(self._sor(e))

    def _sor(self, e: inditas.InditasiElem) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        sor = QHBoxLayout(w)
        sor.setContentsMargins(0, 8, 0, 8)
        sor.setSpacing(12)
        szoveg = QVBoxLayout()
        szoveg.setSpacing(2)
        szoveg.addWidget(cimke(e.nev, "kartyaertek"))
        parancs = cimke(e.parancs, "leiras")
        parancs.setToolTip(e.parancs)
        parancs.setMaximumWidth(620)
        szoveg.addWidget(parancs)
        sor.addLayout(szoveg, 1)
        sor.addWidget(Jelveny(e.forras, "semleges"), 0, Qt.AlignmentFlag.AlignVCenter)
        k = Kapcsolo()
        k.beallit(e.engedelyezve)
        k.setAccessibleName(f"{e.nev} automatikus indítása")
        modosithato = e.modosithato or self.ktx.admin
        k.setEnabled(modosithato)
        if not modosithato:
            k.setToolTip("Ennek a módosításához rendszergazdaként kell futtatni a BR Configot.")
        k.toggled.connect(lambda be, elem=e, kapcsolo=k: self._allit(elem, be, kapcsolo))
        sor.addWidget(k, 0, Qt.AlignmentFlag.AlignVCenter)
        return w

    def _allit(self, e: inditas.InditasiElem, be: bool, k: Kapcsolo) -> None:
        if self.ktx.proba:
            self.ktx.naplo.emit(f"[próba] {e.nev}: automatikus indítás {'be' if be else 'ki'}")
            k.beallit(not be)
            return
        try:
            self.kezelo.beallit(e.azonosito, be)
        except (OSError, ValueError) as hiba:
            k.beallit(not be)
            QMessageBox.warning(self, "Nem sikerült", f"{e.nev}: {hiba}")
            return
        self.ktx.naplo.emit(f"{e.nev}: automatikus indítás {'bekapcsolva' if be else 'kikapcsolva'}")
