import sys


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("info", "programok", "tweakek", "--version", "-h",
                                             "--help"):
        from br_config.cli import main as cli_main

        return cli_main(sys.argv[1:])
    from PySide6.QtWidgets import QApplication

    from br_config import APP_NEV, KESZITO, __version__
    from br_config.ui.fo_ablak import FoAblak
    from br_config.ui.kontextus import Kontextus
    from br_config.ui.tema import betutipus, logo_ikon, stilus

    QApplication.setApplicationName(APP_NEV)
    QApplication.setApplicationVersion(__version__)
    QApplication.setOrganizationName(KESZITO)
    QApplication.setDesktopFileName("br-config")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(betutipus())
    app.setWindowIcon(logo_ikon())
    app.setStyleSheet(stilus())
    ablak = FoAblak(Kontextus())
    ablak.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
