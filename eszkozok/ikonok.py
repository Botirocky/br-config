import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

GYOKER = Path(__file__).resolve().parent.parent
LOGO = GYOKER / "src" / "br_config" / "kepek" / "logo.svg"
CEL = GYOKER / "assets"
MERETEK = (16, 24, 32, 48, 64, 128, 256, 512)


def render(renderer: QSvgRenderer, meret: int) -> QImage:
    kep = QImage(meret, meret, QImage.Format.Format_ARGB32)
    kep.fill(Qt.GlobalColor.transparent)
    festo = QPainter(kep)
    festo.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(festo, QRectF(0, 0, meret, meret))
    festo.end()
    return kep


def main() -> int:
    QGuiApplication(sys.argv[:1])
    renderer = QSvgRenderer(str(LOGO))
    CEL.mkdir(exist_ok=True)
    for meret in MERETEK:
        render(renderer, meret).save(str(CEL / f"ikon-{meret}.png"))
    (CEL / "ikon.svg").write_bytes(LOGO.read_bytes())
    Image.open(CEL / "ikon-256.png").save(
        CEL / "ikon.ico", sizes=[(m, m) for m in (16, 24, 32, 48, 64, 128, 256)])
    print(f"Ikonok elkészültek: {CEL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
