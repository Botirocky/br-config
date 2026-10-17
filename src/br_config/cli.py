__lazy_modules__ = ["argparse"]

import argparse

from br_config import (
    APP_NEV,
    KESZITO,
    __version__,
    csomagkezelok,
    driverek,
    gep,
    katalogus,
    tweakek,
)
from br_config.rendszer import felismer


def _info() -> int:
    rendszer = felismer()
    info = gep.felismer_gep(rendszer)
    print(f"{APP_NEV} {__version__} – {KESZITO}")
    print(f"Rendszer:   {rendszer.nev} ({rendszer.csalad()})")
    print(f"Processzor: {info.cpu.nev} [{info.cpu.gyarto}]")
    for g in info.gpuk:
        print(f"Videókártya: {g.nev} [{g.gyarto}]")
    print(f"Memória:    {info.ram_gb} GB")
    print(f"Laptop:     {'igen' if info.laptop else 'nem'}")
    kezelok = csomagkezelok.elerheto_kezelok(rendszer)
    print(f"Csomagkezelők: {', '.join(k.nev for k in kezelok) or 'nincs'}")
    fo = kezelok[0] if kezelok else None
    telepitett = csomagkezelok.telepitett(fo) if fo else set()
    print("\nDriver-ajánlások:")
    for a in driverek.ajanlasok(info, rendszer, telepitett, fo):
        jel = {True: "✔", False: "✘", None: "•"}[a.telepitve]
        print(f"  {jel} {a.nev}: {a.leiras}")
    return 0


def _lista() -> int:
    rendszer = felismer()
    kezelok = csomagkezelok.elerheto_kezelok(rendszer)
    for p in katalogus.elerheto(kezelok):
        kezelo, azonosito = p.forras(kezelok) or (None, "")
        print(f"{p.kategoria:<14} {p.nev:<24} {kezelo.nev if kezelo else '':<8} {azonosito}")
    return 0


def _tweakek() -> int:
    rendszer = felismer()
    kezelok = csomagkezelok.elerheto_kezelok(rendszer)
    k = tweakek.Kornyezet(rendszer, kezelok[0] if kezelok else None)
    for t in tweakek.tamogatott(k):
        allapot = "művelet" if t.egyszeri else {True: "BE", False: "ki", None: "?"}[t.allapot(k)]
        print(f"{t.kategoria:<22} {allapot:<8} {t.nev}")
    return 0


def main(argv: list[str] | None = None) -> int:
    elemzo = argparse.ArgumentParser(prog="br-config-cli", description=f"{APP_NEV} parancssor")
    elemzo.add_argument("--version", action="version", version=f"{APP_NEV} {__version__}")
    al = elemzo.add_subparsers(dest="parancs", required=True)
    al.add_parser("info", help="gép- és driverinformáció")
    al.add_parser("programok", help="telepíthető programok listája")
    al.add_parser("tweakek", help="tuning-beállítások és állapotuk")
    args = elemzo.parse_args(argv)
    return {"info": _info, "programok": _lista, "tweakek": _tweakek}[args.parancs]()


if __name__ == "__main__":
    raise SystemExit(main())
