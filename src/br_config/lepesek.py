__lazy_modules__ = ["shlex", "subprocess"]

import shlex
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Parancs:
    argv: tuple[str, ...]
    root: bool = False
    leiras: str = ""

    def szoveg(self) -> str:
        if sys.platform.startswith("win"):
            return subprocess.list2cmdline(self.argv)
        return shlex.join(self.argv)


@dataclass(frozen=True, slots=True)
class PythonLepes:
    fv: Callable[[], str | None]
    leiras: str

    def szoveg(self) -> str:
        return f"[beépített] {self.leiras}"


type Lepes = Parancs | PythonLepes


def parancs(*argv: str, root: bool = False, leiras: str = "") -> Parancs:
    return Parancs(tuple(argv), root=root, leiras=leiras)
