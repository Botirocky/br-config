from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from br_config import tweakek
from br_config.ui.elemek import Jelveny, Kapcsolo, Kartya, cimke, fejlec, gomb
from br_config.ui.kontextus import Kontextus


class TweakSor(QWidget):
    def __init__(self, tweak: tweakek.Tweak, ktx: Kontextus, ujratolt: Callable[[], None]):
        super().__init__()
        self.tweak = tweak
        self.ktx = ktx
        self.ujratolt = ujratolt
        self.setStyleSheet("background: transparent;")
        sor = QHBoxLayout(self)
        sor.setContentsMargins(0, 8, 0, 8)
        sor.setSpacing(14)
        szoveg = QVBoxLayout()
        szoveg.setSpacing(3)
        fej = QHBoxLayout()
        fej.setSpacing(8)
        fej.addWidget(cimke(tweak.nev, "kartyaertek"))
        if tweak.ujrainditas:
            fej.addWidget(Jelveny("Újraindítás után él", "semleges"))
        fej.addStretch(1)
        szoveg.addLayout(fej)
        szoveg.addWidget(cimke(tweak.leiras, "leiras", sortores=True))
        sor.addLayout(szoveg, 1)
        self.vezerlo: Kapcsolo | QPushButton
        if tweak.egyszeri:
            self.vezerlo = gomb("Futtatás", ikon_nev="lejatszas")
            self.vezerlo.clicked.connect(self._futtat)
        else:
            self.vezerlo = Kapcsolo()
            self.vezerlo.setEnabled(False)
            self.vezerlo.toggled.connect(self._kapcsol)
        self.vezerlo.setAccessibleName(tweak.nev)
        self.vezerlo.setToolTip(self._parancsok())
        sor.addWidget(self.vezerlo, 0, Qt.AlignmentFlag.AlignVCenter)

    def _parancsok(self) -> str:
        k = self.ktx.tweak_kornyezet()
        sorok = ["Bekapcsolás:" if not self.tweak.egyszeri else "Futtatja:"]
        sorok += [l.szoveg() for l in self.tweak.bekapcsol(k)]
        if self.tweak.kikapcsol:
            sorok += ["", "Kikapcsolás:"] + [l.szoveg() for l in self.tweak.kikapcsol(k)]
        return "\n".join(sorok)

    def allapot_beallit(self, allapot: bool | None) -> None:
        if isinstance(self.vezerlo, Kapcsolo):
            self.vezerlo.beallit(bool(allapot))
            self.vezerlo.setEnabled(not self.ktx.foglalt)

    def foglalt(self, fut: bool) -> None:
        self.vezerlo.setEnabled(not fut)

    def _futtat(self) -> None:
        self.ktx.futtat(self.tweak.bekapcsol(self.ktx.tweak_kornyezet()), self.tweak.nev)

    def _kapcsol(self, be: bool) -> None:
        k = self.ktx.tweak_kornyezet()
        lepesek = self.tweak.bekapcsol(k) if be else (self.tweak.kikapcsol or (lambda _: []))(k)
        cim = f"{self.tweak.nev}: {'bekapcsolás' if be else 'kikapcsolás'}"
        if not self.ktx.futtat(lepesek, cim, lambda siker: self._utana(be, siker)):
            self._vissza(be)

    def _vissza(self, be: bool) -> None:
        if isinstance(self.vezerlo, Kapcsolo):
            self.vezerlo.beallit(not be)

    def _utana(self, be: bool, siker: bool) -> None:
        if not siker or self.ktx.proba:
            self._vissza(be)
        self.ujratolt()


class TuningOldal(QWidget):
    def __init__(self, ktx: Kontextus):
        super().__init__()
        self.ktx = ktx
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(12)
        l.addWidget(fejlec("Tuning",
                           "Teljesítmény, energia, hálózat és adatvédelem. Minden kapcsoló "
                           "visszaállítható. Vidd az egeret egy kapcsoló fölé, és látod, "
                           "pontosan mit futtat."))
        self.sorok: list[TweakSor] = []
        k = ktx.tweak_kornyezet()
        lista = tweakek.tamogatott(k)
        if not lista:
            l.addWidget(cimke("Ehhez a rendszerhez még nincs elérhető beállítás.", "leiras"))
        for kategoria in tweakek.KATEGORIAK:
            elemek = [t for t in lista if t.kategoria == kategoria]
            if not elemek:
                continue
            l.addWidget(cimke(kategoria.upper(), "szekcio"))
            kartya = Kartya()
            kartya.elrendezes.setSpacing(0)
            for i, t in enumerate(elemek):
                if i:
                    elvalaszto = QWidget()
                    elvalaszto.setFixedHeight(1)
                    elvalaszto.setStyleSheet("background: #334155;")
                    kartya.elrendezes.addWidget(elvalaszto)
                s = TweakSor(t, ktx, self.frissit)
                self.sorok.append(s)
                kartya.elrendezes.addWidget(s)
            l.addWidget(kartya)
        l.addStretch(1)
        ktx.futas.connect(self._foglalt)
        self.frissit()

    def frissit(self) -> None:
        kapcsolos = [s for s in self.sorok if not s.tweak.egyszeri]
        k = self.ktx.tweak_kornyezet()

        def lekerdez(_: Callable[[str], None]) -> dict[str, bool | None]:
            eredmeny = {}
            for s in kapcsolos:
                try:
                    eredmeny[s.tweak.id] = s.tweak.allapot(k)
                except Exception:
                    eredmeny[s.tweak.id] = None
            return eredmeny

        def kesz(allapotok: object) -> None:
            if isinstance(allapotok, dict):
                for s in kapcsolos:
                    s.allapot_beallit(allapotok.get(s.tweak.id))

        self.ktx.hatter.indit(lekerdez, kesz)

    def _foglalt(self, fut: bool) -> None:
        for s in self.sorok:
            s.foglalt(fut)
