from collections.abc import Callable

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QThread,
    Signal,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from br_config.ui.tema import SZIN, ikon


class Kapcsolo(QAbstractButton):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._pozicio = 0.0
        self._animacio = QPropertyAnimation(self, b"pozicio", self)
        self._animacio.setDuration(180)
        self._animacio.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animal)

    def sizeHint(self) -> QSize:
        return QSize(48, 28)

    def _get_pozicio(self) -> float:
        return self._pozicio

    def _set_pozicio(self, ertek: float) -> None:
        self._pozicio = ertek
        self.update()

    pozicio = Property(float, _get_pozicio, _set_pozicio)

    def _animal(self, be: bool) -> None:
        self._animacio.stop()
        self._animacio.setEndValue(1.0 if be else 0.0)
        self._animacio.start()

    def beallit(self, be: bool) -> None:
        self.blockSignals(True)
        self.setChecked(be)
        self.blockSignals(False)
        self._pozicio = 1.0 if be else 0.0
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sav = QRectF(2, 4, 44, 20)
        ki, be = QColor(SZIN["keret_eros"]), QColor(SZIN["kiemelt"])
        szin = QColor(
            int(ki.red() + (be.red() - ki.red()) * self._pozicio),
            int(ki.green() + (be.green() - ki.green()) * self._pozicio),
            int(ki.blue() + (be.blue() - ki.blue()) * self._pozicio),
        )
        if not self.isEnabled():
            szin.setAlpha(110)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(szin)
        p.drawRoundedRect(sav, 10, 10)
        x = 4 + self._pozicio * 24
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QRectF(x, 6, 16, 16))
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QColor(SZIN["info"]))
            p.drawRoundedRect(QRectF(0.5, 2.5, 47, 23), 11.5, 11.5)


class Jelveny(QLabel):
    def __init__(self, szoveg: str, tipus: str = "semleges", parent: QWidget | None = None):
        super().__init__(szoveg, parent)
        self.setObjectName("jelveny")
        self.setProperty("tipus", tipus)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def frissit(self, szoveg: str, tipus: str) -> None:
        self.setText(szoveg)
        self.setProperty("tipus", tipus)
        self.style().unpolish(self)
        self.style().polish(self)


class Kartya(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("kartya")
        self.elrendezes = QVBoxLayout(self)
        self.elrendezes.setContentsMargins(16, 14, 16, 14)
        self.elrendezes.setSpacing(6)


def gomb(szoveg: str, szerep: str = "", ikon_nev: str | None = None) -> QPushButton:
    g = QPushButton(szoveg)
    g.setCursor(Qt.CursorShape.PointingHandCursor)
    if szerep:
        g.setProperty("szerep", szerep)
    if ikon_nev:
        szin = SZIN["kiemelt_szoveg"] if szerep == "fo" else SZIN["szoveg"]
        if szerep == "veszely":
            szin = SZIN["hiba"]
        g.setIcon(ikon(ikon_nev, szin))
    return g


def cimke(szoveg: str, nev: str = "", sortores: bool = False) -> QLabel:
    c = QLabel(szoveg)
    if nev:
        c.setObjectName(nev)
    c.setWordWrap(sortores)
    c.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return c


def fejlec(cim: str, alcim: str) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    l = QVBoxLayout(w)
    l.setContentsMargins(0, 0, 0, 8)
    l.setSpacing(4)
    l.addWidget(cimke(cim, "cim"))
    l.addWidget(cimke(alcim, "alcim", sortores=True))
    return w


def sor(*widgetek: QWidget, nyujt: int | None = None) -> QHBoxLayout:
    l = QHBoxLayout()
    l.setSpacing(10)
    for i, w in enumerate(widgetek):
        l.addWidget(w, 1 if i == nyujt else 0)
    return l


class _Feladat(QThread):
    sor = Signal(str)
    eredmeny = Signal(object)
    hiba = Signal(str)

    def __init__(self, fv: Callable, parent: QObject | None = None):
        super().__init__(parent)
        self._fv = fv

    def run(self) -> None:
        try:
            self.eredmeny.emit(self._fv(self.sor.emit))
        except Exception as e:
            self.hiba.emit(f"{type(e).__name__}: {e}")


class Hatter(QObject):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._futok: set[_Feladat] = set()

    def indit(self, fv: Callable[[Callable[[str], None]], object],
              kesz: Callable[[object], None] | None = None,
              sor: Callable[[str], None] | None = None,
              hiba: Callable[[str], None] | None = None) -> _Feladat:
        f = _Feladat(fv, self)
        if sor:
            f.sor.connect(sor)
        if kesz:
            f.eredmeny.connect(kesz)
        if hiba:
            f.hiba.connect(hiba)
        f.finished.connect(lambda: self._futok.discard(f))
        f.finished.connect(f.deleteLater)
        self._futok.add(f)
        f.start()
        return f

    def fut(self) -> bool:
        return any(f.isRunning() for f in self._futok)
