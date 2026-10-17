from functools import cache

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

SZIN = {
    "hatter": "#0F172A",
    "felulet": "#1E293B",
    "felulet2": "#273449",
    "keret": "#334155",
    "keret_eros": "#475569",
    "szoveg": "#F8FAFC",
    "halvany": "#94A3B8",
    "kiemelt": "#22C55E",
    "kiemelt_sotet": "#16A34A",
    "kiemelt_szoveg": "#052E16",
    "info": "#38BDF8",
    "figyelem": "#FBBF24",
    "hiba": "#F87171",
}

IKONOK = {
    "attekintes": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "driver": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" '
              'height="5"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "programok": '<path d="M21 8 12 3 3 8v8l9 5 9-5V8Z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
    "tuning": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3"/>'
              '<path d="M1 14h6M9 8h6M17 16h6"/>',
    "inditas": '<path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.8 0"/>',
    "nevjegy": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-5M12 8h.01"/>',
    "kereses": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "frissites": '<path d="M21 12a9 9 0 1 1-2.6-6.4L21 8"/><path d="M21 3v5h-5"/>',
    "pajzs": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>',
    "pipa": '<path d="M20 6 9 17l-5-5"/>',
    "figyelem": '<path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4M12 17h.01"/>',
    "kulso": '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 '
             '2-2h6"/>',
    "lejatszas": '<path d="m6 4 14 8-14 8V4Z"/>',
    "kuka": '<path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/>',
    "naplo": '<path d="m4 17 6-6-6-6M12 19h8"/>',
    "github": '<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.9a3.4 3.4 0 0 0-.9-2.6c3.1-.4 6.4-1.5 '
              '6.4-7A5.4 5.4 0 0 0 20 4.8 5 5 0 0 0 19.9 1S18.7.6 16 2.5a13.4 13.4 0 0 0-7 0C6.3.6 '
              '5.1 1 5.1 1A5 5 0 0 0 5 4.8a5.4 5.4 0 0 0-1.5 3.7c0 5.4 3.3 6.6 6.4 7A3.4 3.4 0 0 0 9 '
              '18.1V22"/>',
}


def svg_ikon_szoveg(nev: str, szin: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
            f'stroke="{szin}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f"{IKONOK[nev]}</svg>")


def _render(svg: bytes, meret: int) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(svg))
    kep = QImage(meret, meret, QImage.Format.Format_ARGB32_Premultiplied)
    kep.fill(Qt.GlobalColor.transparent)
    festo = QPainter(kep)
    festo.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(festo, QRectF(0, 0, meret, meret))
    festo.end()
    return QPixmap.fromImage(kep)


@cache
def ikon(nev: str, szin: str = SZIN["halvany"], aktiv: str | None = None) -> QIcon:
    i = QIcon()
    for meret in (16, 20, 24, 32, 48):
        i.addPixmap(_render(svg_ikon_szoveg(nev, szin).encode(), meret), QIcon.Mode.Normal,
                    QIcon.State.Off)
        if aktiv:
            i.addPixmap(_render(svg_ikon_szoveg(nev, aktiv).encode(), meret), QIcon.Mode.Normal,
                        QIcon.State.On)
    return i


@cache
def logo_svg() -> bytes:
    from importlib import resources

    return resources.files("br_config").joinpath("kepek/logo.svg").read_bytes()


def logo_pixmap(meret: int) -> QPixmap:
    return _render(logo_svg(), meret)


def logo_ikon() -> QIcon:
    i = QIcon()
    for meret in (16, 24, 32, 48, 64, 128, 256):
        i.addPixmap(logo_pixmap(meret))
    return i


def betutipus() -> QFont:
    csaladok = set(QFontDatabase.families())
    for nev in ("Inter", "Inter Variable", "Segoe UI Variable Text", "Segoe UI", "Noto Sans",
                "Cantarell", "DejaVu Sans"):
        if nev in csaladok:
            f = QFont(nev)
            break
    else:
        f = QFont()
    f.setPointSizeF(10.5)
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    return f


def stilus() -> str:
    s = SZIN
    return f"""
QWidget {{ background: {s['hatter']}; color: {s['szoveg']}; }}
QToolTip {{ background: {s['felulet2']}; color: {s['szoveg']}; border: 1px solid {s['keret']};
           padding: 6px 8px; border-radius: 6px; }}
#oldalsav {{ background: #0B1120; border-right: 1px solid {s['keret']}; }}
#oldalsav QPushButton {{ background: transparent; color: {s['halvany']}; border: none;
    text-align: left; padding: 10px 14px; border-radius: 8px; font-weight: 500; min-height: 24px; }}
#oldalsav QPushButton:hover {{ background: {s['felulet']}; color: {s['szoveg']}; }}
#oldalsav QPushButton:checked {{ background: {s['felulet']}; color: {s['szoveg']};
    border-left: 3px solid {s['kiemelt']}; padding-left: 11px; }}
#oldalsav QPushButton:focus-visible {{ outline: 2px solid {s['kiemelt']}; }}
#markanev {{ font-size: 17px; font-weight: 700; background: transparent; }}
#keszito {{ color: {s['halvany']}; font-size: 12px; background: transparent; }}
#cim {{ font-size: 22px; font-weight: 700; background: transparent; }}
#alcim {{ color: {s['halvany']}; font-size: 13px; background: transparent; }}
#szekcio {{ font-size: 13px; font-weight: 600; color: {s['halvany']}; background: transparent;
    letter-spacing: 0.5px; padding-top: 8px; }}
#kartya {{ background: {s['felulet']}; border: 1px solid {s['keret']}; border-radius: 12px; }}
#kartya QLabel {{ background: transparent; }}
#kartya:hover {{ border-color: {s['keret_eros']}; }}
#kartyacim {{ color: {s['halvany']}; font-size: 12px; font-weight: 600; }}
#kartyaertek {{ font-size: 15px; font-weight: 600; }}
#leiras {{ color: {s['halvany']}; font-size: 12.5px; }}
#jelveny {{ border-radius: 10px; padding: 2px 10px; font-size: 11.5px; font-weight: 600; }}
#jelveny[tipus="ok"] {{ background: rgba(34,197,94,0.15); color: #4ADE80; }}
#jelveny[tipus="hiany"] {{ background: rgba(251,191,36,0.15); color: {s['figyelem']}; }}
#jelveny[tipus="info"] {{ background: rgba(56,189,248,0.14); color: {s['info']}; }}
#jelveny[tipus="semleges"] {{ background: {s['felulet2']}; color: {s['halvany']}; }}
QPushButton {{ background: {s['felulet2']}; color: {s['szoveg']}; border: 1px solid {s['keret']};
    border-radius: 8px; padding: 8px 16px; font-weight: 600; min-height: 20px; }}
QPushButton:hover {{ background: {s['keret']}; border-color: {s['keret_eros']}; }}
QPushButton:pressed {{ background: {s['felulet']}; }}
QPushButton:focus {{ border: 2px solid {s['kiemelt']}; }}
QPushButton:disabled {{ color: #64748B; background: {s['felulet']}; border-color: {s['felulet2']}; }}
QPushButton[szerep="fo"] {{ background: {s['kiemelt']}; color: {s['kiemelt_szoveg']};
    border: 1px solid {s['kiemelt']}; }}
QPushButton[szerep="fo"]:hover {{ background: #4ADE80; }}
QPushButton[szerep="fo"]:disabled {{ background: #14532D; color: #4B6B57; border-color: #14532D; }}
QPushButton[szerep="veszely"] {{ color: {s['hiba']}; }}
QPushButton[szerep="veszely"]:hover {{ background: rgba(248,113,113,0.12); border-color: {s['hiba']}; }}
QPushButton[szerep="link"] {{ background: transparent; border: none; color: {s['info']};
    padding: 4px 6px; }}
QLineEdit, QComboBox {{ background: {s['felulet']}; border: 1px solid {s['keret']};
    border-radius: 8px; padding: 8px 12px; selection-background-color: {s['kiemelt_sotet']}; }}
QLineEdit:focus, QComboBox:focus {{ border: 2px solid {s['kiemelt']}; padding: 7px 11px; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{ background: {s['felulet']}; border: 1px solid {s['keret']};
    selection-background-color: {s['felulet2']}; outline: none; }}
QCheckBox {{ background: transparent; spacing: 10px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px;
    border: 2px solid {s['keret_eros']}; background: {s['hatter']}; }}
QCheckBox::indicator:hover {{ border-color: {s['kiemelt']}; }}
QCheckBox::indicator:checked {{ background: {s['kiemelt']}; border-color: {s['kiemelt']}; }}
QCheckBox:focus {{ outline: none; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {s['keret']}; border-radius: 4px; min-height: 32px; }}
QScrollBar::handle:vertical:hover {{ background: {s['keret_eros']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QPlainTextEdit#naplo {{ background: #020617; color: #CBD5E1; border: none;
    border-top: 1px solid {s['keret']}; font-family: "JetBrains Mono", "Cascadia Mono", "Consolas",
    "DejaVu Sans Mono", monospace; font-size: 12px; padding: 8px 12px; }}
#naplofej {{ background: #0B1120; border-top: 1px solid {s['keret']}; }}
#naplofej QLabel {{ background: transparent; color: {s['halvany']}; font-weight: 600; }}
#szalag {{ background: rgba(251,191,36,0.10); border: 1px solid rgba(251,191,36,0.35);
    border-radius: 10px; }}
#szalag QLabel {{ background: transparent; color: {s['figyelem']}; }}
QProgressBar {{ background: {s['felulet']}; border: none; border-radius: 3px; max-height: 6px; }}
QProgressBar::chunk {{ background: {s['kiemelt']}; border-radius: 3px; }}
QMessageBox {{ background: {s['felulet']}; }}
QMessageBox QLabel {{ background: transparent; }}
QSplitter::handle {{ background: {s['keret']}; }}
"""
