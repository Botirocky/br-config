import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from br_config.ui.fo_ablak import OLDALAK, FoAblak
from br_config.ui.kontextus import Kontextus
from br_config.ui.tema import stilus

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def app():
    a = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    a.setStyleSheet(stilus())
    return a


def _var(feltetel, ms: int = 15000) -> bool:
    loop = QEventLoop()
    idozito = QTimer()
    idozito.timeout.connect(lambda: loop.quit() if feltetel() else None)
    idozito.start(50)
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    idozito.stop()
    return feltetel()


@pytest.fixture
def ablak(app):
    w = FoAblak(Kontextus())
    w.show()
    yield w
    _var(lambda: not w.ktx.hatter.fut(), 20000)
    w.close()
    w.deleteLater()
    QCoreApplication.processEvents()


def test_minden_oldal_letrejon_lustan(ablak):
    assert set(ablak._letrehozva) == {"attekintes"}
    for i in range(len(OLDALAK)):
        ablak.valt(i)
    assert set(ablak._letrehozva) == {k for k, *_ in OLDALAK}


def test_gepfelismeres_megerkezik(ablak):
    assert _var(lambda: ablak.ktx.gep is not None)
    assert ablak.ktx.gep.cpu.nev


def test_proba_modban_csak_naplozik(ablak):
    ablak.proba.setChecked(True)
    ablak.valt(1)
    oldal = ablak._letrehozva["programok"].widget().layout().itemAt(0).widget()
    if not oldal.sorok:
        pytest.skip("nincs csomagkezelő ezen a gépen")
    oldal.sorok[0].jelolo.setChecked(True)
    assert oldal.telepit.isEnabled()
    oldal.telepit.click()
    assert _var(lambda: "Kész." in ablak.naplo.toPlainText())
    szoveg = ablak.naplo.toPlainText()
    assert "próba mód" in szoveg
    assert "$ " in szoveg
    assert not oldal.sorok[0].jelolo.isChecked()
