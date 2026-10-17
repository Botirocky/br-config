from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from br_config import katalogus
from br_config.ui.elemek import Jelveny, Kartya, cimke, fejlec, gomb
from br_config.ui.kontextus import Kontextus
from br_config.ui.tema import ikon

MIND = "Minden kategória"


class ProgramSor(Kartya):
    def __init__(self, program: katalogus.Program, forras: str):
        super().__init__()
        self.program = program
        self.elrendezes.setContentsMargins(14, 10, 14, 10)
        sor = QHBoxLayout()
        sor.setSpacing(12)
        self.jelolo = QCheckBox()
        self.jelolo.setAccessibleName(f"{program.nev} kijelölése")
        self.jelolo.setCursor(Qt.CursorShape.PointingHandCursor)
        sor.addWidget(self.jelolo, 0, Qt.AlignmentFlag.AlignVCenter)
        szoveg = QVBoxLayout()
        szoveg.setSpacing(2)
        szoveg.addWidget(cimke(program.nev, "kartyaertek"))
        szoveg.addWidget(cimke(program.leiras, "leiras", sortores=True))
        sor.addLayout(szoveg, 1)
        self.allapot = Jelveny("", "ok")
        self.allapot.hide()
        sor.addWidget(self.allapot, 0, Qt.AlignmentFlag.AlignVCenter)
        sor.addWidget(Jelveny(forras, "info"), 0, Qt.AlignmentFlag.AlignVCenter)
        self.elrendezes.addLayout(sor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.jelolo.toggle()
        super().mousePressEvent(event)

    def telepitve(self, igen: bool) -> None:
        self.allapot.setVisible(igen)
        if igen:
            self.allapot.frissit("Telepítve", "ok")


class ProgramokOldal(QWidget):
    def __init__(self, ktx: Kontextus):
        super().__init__()
        self.ktx = ktx
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(12)
        l.addWidget(fejlec("Programok",
                           "Jelöld ki, amit telepítenél, és egy kattintással mind felkerül. "
                           "A rendszer saját csomagkezelőjét használom, ha nincs benne, a "
                           "Flatpakot vagy a wingetet."))
        szuro = QHBoxLayout()
        szuro.setSpacing(10)
        self.kereso = QLineEdit()
        self.kereso.setPlaceholderText("Keresés név vagy leírás alapján…")
        self.kereso.setAccessibleName("Programok keresése")
        self.kereso.addAction(ikon("kereses"), QLineEdit.ActionPosition.LeadingPosition)
        self.kereso.setClearButtonEnabled(True)
        self.kategoria = QComboBox()
        self.kategoria.setAccessibleName("Kategória")
        szuro.addWidget(self.kereso, 1)
        szuro.addWidget(self.kategoria)
        l.addLayout(szuro)

        self.lista = QVBoxLayout()
        self.lista.setSpacing(8)
        l.addLayout(self.lista)
        self.ures = cimke("Nincs a keresésnek megfelelő program.", "leiras")
        self.ures.hide()
        l.addWidget(self.ures)
        l.addStretch(1)

        self.sorok: list[ProgramSor] = []
        programok = katalogus.elerheto(ktx.kezelok)
        if not ktx.kezelok:
            l.insertWidget(1, cimke("Nem találtam támogatott csomagkezelőt (winget, pacman, apt, "
                                    "dnf, zypper vagy flatpak).", "leiras", sortores=True))
        kategoriak = list(dict.fromkeys(p.kategoria for p in programok))
        self.kategoria.addItems([MIND, *kategoriak])
        for p in programok:
            kezelo, _ = p.forras(ktx.kezelok) or (None, "")
            s = ProgramSor(p, kezelo.nev if kezelo else "")
            s.jelolo.toggled.connect(self._szamol)
            self.sorok.append(s)
            self.lista.addWidget(s)

        self.kereso.textChanged.connect(self._szur)
        self.kategoria.currentTextChanged.connect(self._szur)
        ktx.telepitett_kesz.connect(self._allapotok)
        ktx.futas.connect(lambda _: self._szamol())
        self._allapotok()

    def also_sav(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        sav = QHBoxLayout(w)
        sav.setContentsMargins(0, 0, 0, 0)
        sav.setSpacing(10)
        self.szamlalo = cimke("Nincs kijelölve semmi", "leiras")
        self.frissit = gomb("Minden frissítése", ikon_nev="frissites")
        self.eltavolit = gomb("Eltávolítás", "veszely", "kuka")
        self.telepit = gomb("Kijelöltek telepítése", "fo", "lejatszas")
        self.frissit.clicked.connect(self._frissit)
        self.eltavolit.clicked.connect(self._eltavolit)
        self.telepit.clicked.connect(self._telepit)
        sav.addWidget(self.szamlalo, 1)
        for g in (self.frissit, self.eltavolit, self.telepit):
            sav.addWidget(g)
        QTimer.singleShot(0, self._szamol)
        return w

    def _kijelolt(self) -> list[katalogus.Program]:
        return [s.program for s in self.sorok if s.jelolo.isChecked()]

    def _szamol(self) -> None:
        if not hasattr(self, "telepit"):
            return
        db = len(self._kijelolt())
        self.szamlalo.setText(f"{db} program kijelölve" if db else "Nincs kijelölve semmi")
        fut = self.ktx.foglalt
        self.telepit.setEnabled(bool(db) and not fut)
        self.eltavolit.setEnabled(bool(db) and not fut)
        self.frissit.setEnabled(bool(self.ktx.kezelok) and not fut)

    def _szur(self) -> None:
        szoveg = self.kereso.text().strip().lower()
        kat = self.kategoria.currentText()
        lathato = 0
        for s in self.sorok:
            p = s.program
            jo = (kat == MIND or p.kategoria == kat) and (
                not szoveg or szoveg in p.nev.lower() or szoveg in p.leiras.lower())
            s.setVisible(jo)
            lathato += jo
        self.ures.setVisible(lathato == 0)

    def _allapotok(self) -> None:
        for s in self.sorok:
            talalat = s.program.forras(self.ktx.kezelok)
            if talalat is None:
                continue
            kezelo, azonosito = talalat
            s.telepitve(azonosito in self.ktx.telepitett.get(kezelo.nev, set()))

    def _vege(self, siker: bool) -> None:
        if siker:
            for s in self.sorok:
                s.jelolo.setChecked(False)

    def _telepit(self) -> None:
        csoportok = katalogus.csoportosit(self._kijelolt(), self.ktx.kezelok)
        lepesek = [lepes for k, ids in csoportok.items() for lepes in k.telepit(ids)]
        self.ktx.futtat(lepesek, "Programok telepítése", self._vege)

    def _eltavolit(self) -> None:
        nevek = ", ".join(p.nev for p in self._kijelolt())
        valasz = QMessageBox.question(
            self, "Eltávolítás", f"Biztosan eltávolítod ezeket?\n\n{nevek}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel)
        if valasz != QMessageBox.StandardButton.Yes:
            return
        csoportok = katalogus.csoportosit(self._kijelolt(), self.ktx.kezelok)
        lepesek = [lepes for k, ids in csoportok.items() for lepes in k.eltavolit(ids)]
        self.ktx.futtat(lepesek, "Programok eltávolítása", self._vege)

    def _frissit(self) -> None:
        lepesek = [lepes for k in self.ktx.kezelok for lepes in k.frissit_mindent()]
        self.ktx.futtat(lepesek, "Minden program frissítése")
