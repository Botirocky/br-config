__lazy_modules__ = ["json"]

import json
from dataclasses import dataclass, field
from functools import cache
from importlib import resources

from br_config.csomagkezelok import Kezelo

KEZELO_KULCSOK = ("winget", "pacman", "apt", "dnf", "zypper", "flatpak")


@dataclass(frozen=True, slots=True)
class Program:
    id: str
    nev: str
    kategoria: str
    leiras: str
    azonositok: dict[str, str] = field(default_factory=dict)

    def forras(self, kezelok: list[Kezelo]) -> tuple[Kezelo, str] | None:
        for kezelo in kezelok:
            if azonosito := self.azonositok.get(kezelo.nev):
                return kezelo, azonosito
        return None


def katalogus_feldolgoz(adat: list[dict]) -> list[Program]:
    programok = []
    for elem in adat:
        azonositok = {k: elem[k] for k in KEZELO_KULCSOK if elem.get(k)}
        programok.append(Program(elem["id"], elem["nev"], elem["kategoria"], elem["leiras"],
                                 azonositok))
    return programok


@cache
def betolt() -> tuple[Program, ...]:
    szoveg = resources.files("br_config").joinpath("katalogus.json").read_text(encoding="utf-8")
    return tuple(katalogus_feldolgoz(json.loads(szoveg)))


def elerheto(kezelok: list[Kezelo]) -> list[Program]:
    return [p for p in betolt() if p.forras(kezelok) is not None]


def csoportosit(programok: list[Program], kezelok: list[Kezelo]) -> dict[Kezelo, list[str]]:
    csoportok: dict[Kezelo, list[str]] = {}
    for program in programok:
        if (talalat := program.forras(kezelok)) is not None:
            kezelo, azonosito = talalat
            csoportok.setdefault(kezelo, []).append(azonosito)
    return csoportok
