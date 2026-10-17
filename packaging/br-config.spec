import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

GYOKER = Path(SPECPATH).parent
FORRAS = GYOKER / "src"
WINDOWS = sys.platform.startswith("win")

KIHAGYOTT = [
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras", "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic", "PySide6.Qt3DRender", "PySide6.QtBluetooth", "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtGraphs", "PySide6.QtLocation",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets", "PySide6.QtNetworkAuth",
    "PySide6.QtNfc", "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtPositioning",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQuickControls2",
    "PySide6.QtQuickWidgets", "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtSensors",
    "PySide6.QtSerialBus", "PySide6.QtSerialPort", "PySide6.QtSpatialAudio", "PySide6.QtSql",
    "PySide6.QtStateMachine", "PySide6.QtTest", "PySide6.QtTextToSpeech", "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets", "PySide6.QtWebView", "tkinter", "unittest", "pydoc",
]

a = Analysis(
    [str(FORRAS / "br_config" / "__main__.py")],
    pathex=[str(FORRAS)],
    datas=[
        (str(FORRAS / "br_config" / "katalogus.json"), "br_config"),
        (str(FORRAS / "br_config" / "kepek" / "logo.svg"), "br_config/kepek"),
    ],
    hiddenimports=collect_submodules("br_config"),
    excludes=KIHAGYOTT,
    noarchive=False,
)
FELESLEGES = ("Qt6Pdf", "Qt6Qml", "Qt6Quick", "Qt6VirtualKeyboard", "Qt6EglFS", "qpdf",
              "qtvirtualkeyboard", "libqgtk3", "qtquick", "Qt6OpenGL", "Qt6WlShell",
              "opengl32sw", "Qt6WebEngine", "libgtk-3", "libgdk-3", "libgdk_pixbuf", "libatk",
              "libatspi", "libcairo", "libpango", "libglycin", "libtinysparql", "libcloudproviders",
              "libjson-glib", "libicudata.so.78", "libicuuc.so.78", "libepoxy", "libthai",
              "libdatrie", "libpixman", "libxml2", "libseccomp", "libfontconfig", "libfreetype",
              "libharfbuzz")


def _kell(elem) -> bool:
    return not any(minta.lower() in elem[0].lower() for minta in FELESLEGES)


a.binaries = [b for b in a.binaries if _kell(b)]
a.datas = [d for d in a.datas if _kell(d) and "/translations/qtwebengine" not in d[0]]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BR-Config",
    console=False,
    icon=str(GYOKER / "assets" / ("ikon.ico" if WINDOWS else "ikon-256.png")),
    version=str(GYOKER / "packaging" / "windows" / "verzio.txt") if WINDOWS else None,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="BR-Config")
