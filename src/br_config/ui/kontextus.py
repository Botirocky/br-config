from collections.abc import Callable, Sequence

from PySide6.QtCore import QObject, Signal

from br_config import csomagkezelok, gep
from br_config.futtato import Futtato
from br_config.lepesek import Lepes
from br_config.rendszer import felismer, rendszergazda
from br_config.tweakek import Kornyezet
from br_config.ui.elemek import Hatter


class Kontextus(QObject):
    gep_kesz = Signal()
    telepitett_kesz = Signal()
    futas = Signal(bool)
    naplo = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.rendszer = felismer()
        self.kezelok = csomagkezelok.elerheto_kezelok(self.rendszer)
        self.fo = self.kezelok[0] if self.kezelok else None
        self.admin = rendszergazda()
        self.gep: gep.GepInfo | None = None
        self.telepitett: dict[str, set[str]] = {}
        self.proba = False
        self.hatter = Hatter(self)
        self._fut = False

    @property
    def foglalt(self) -> bool:
        return self._fut

    def osszes_telepitett(self) -> set[str]:
        return set().union(*self.telepitett.values()) if self.telepitett else set()

    def tweak_kornyezet(self) -> Kornyezet:
        return Kornyezet(self.rendszer, self.fo)

    def betolt(self) -> None:
        self.hatter.indit(lambda _: gep.felismer_gep(self.rendszer), self._gep_megjott,
                          hiba=self.naplo.emit)
        self.telepitett_frissit()

    def _gep_megjott(self, info: object) -> None:
        self.gep = info if isinstance(info, gep.GepInfo) else gep.GepInfo()
        self.gep_kesz.emit()

    def telepitett_frissit(self) -> None:
        def lekerdez(_: Callable[[str], None]) -> dict[str, set[str]]:
            return {k.nev: csomagkezelok.telepitett(k) for k in self.kezelok}

        self.hatter.indit(lekerdez, self._telepitett_megjott, hiba=self.naplo.emit)

    def _telepitett_megjott(self, adat: object) -> None:
        if isinstance(adat, dict):
            self.telepitett = adat
        self.telepitett_kesz.emit()

    def futtat(self, lepesek: Sequence[Lepes], cim: str,
               utana: Callable[[bool], None] | None = None) -> bool:
        if self._fut:
            self.naplo.emit("Már fut egy művelet, várd meg, amíg befejeződik.")
            return False
        if not lepesek:
            self.naplo.emit(f"{cim}: nincs teendő.")
            if utana:
                utana(True)
            return True
        self._fut = True
        self.futas.emit(True)
        proba = self.proba
        self.naplo.emit(f"── {cim}{' (próba mód, semmi nem fut le)' if proba else ''} ──")

        def munka(kiir: Callable[[str], None]) -> bool:
            return Futtato(self.rendszer, kiir, proba=proba).futtat(lepesek)

        def vege(siker: object) -> None:
            self._fut = False
            self.futas.emit(False)
            if utana:
                utana(bool(siker))
            if not proba:
                self.telepitett_frissit()

        def hiba(uzenet: str) -> None:
            self.naplo.emit(f"HIBA: {uzenet}")
            vege(False)

        self.hatter.indit(munka, vege, sor=self.naplo.emit, hiba=hiba)
        return True
