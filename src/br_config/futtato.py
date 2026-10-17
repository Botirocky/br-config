__lazy_modules__ = ["shlex", "subprocess"]

import shlex
import subprocess
import sys
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass

from br_config.lepesek import Lepes, Parancs, PythonLepes
from br_config.rendszer import Rendszer, rendszergazda, van_program


class FuttatasiHiba(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Csomag:
    lepesek: tuple[Lepes, ...]
    root: bool


def csoportosit(lepesek: Sequence[Lepes]) -> list[Csomag]:
    csomagok: list[Csomag] = []
    aktualis: list[Lepes] = []
    aktualis_root = False
    for lepes in lepesek:
        root = isinstance(lepes, Parancs) and lepes.root
        if aktualis and (root != aktualis_root or not root):
            csomagok.append(Csomag(tuple(aktualis), aktualis_root))
            aktualis = []
        aktualis.append(lepes)
        aktualis_root = root
    if aktualis:
        csomagok.append(Csomag(tuple(aktualis), aktualis_root))
    return csomagok


def emelt_argv(parancsok: Sequence[Parancs], emelo: str = "pkexec") -> list[str]:
    szkript = " && ".join(shlex.join(p.argv) for p in parancsok)
    return [emelo, "sh", "-c", szkript]


def linux_emelo() -> str:
    for nev in ("pkexec", "sudo"):
        if van_program(nev):
            return nev
    raise FuttatasiHiba("Nincs pkexec vagy sudo a rendszeren, a rendszergazdai lépés nem futhat.")


class Futtato:
    def __init__(self, rendszer: Rendszer, kimenet: Callable[[str], None] = print,
                 proba: bool = False):
        self.rendszer = rendszer
        self.kimenet = kimenet
        self.proba = proba

    def futtat(self, lepesek: Sequence[Lepes]) -> bool:
        siker = True
        for csomag in csoportosit(lepesek):
            for lepes in csomag.lepesek:
                self.kimenet(f"$ {lepes.szoveg()}" + ("   [rendszergazda]" if csomag.root else ""))
            if self.proba:
                continue
            try:
                if csomag.root:
                    self._root_csomag(csomag)
                elif isinstance(lepes := csomag.lepesek[0], PythonLepes):
                    if (uzenet := lepes.fv()) is not None:
                        self.kimenet(uzenet)
                else:
                    self._fut(list(lepes.argv))
            except (FuttatasiHiba, OSError) as hiba:
                self.kimenet(f"HIBA: {hiba}")
                siker = False
                break
        self.kimenet("Kész." if siker else "Megszakítva.")
        return siker

    def _root_csomag(self, csomag: Csomag) -> None:
        parancsok = [p for p in csomag.lepesek if isinstance(p, Parancs)]
        if self.rendszer.windows:
            if not rendszergazda():
                raise FuttatasiHiba("Ehhez rendszergazdaként kell futtatni a BR Configot.")
            for p in parancsok:
                self._fut(list(p.argv))
            return
        if rendszergazda():
            for p in parancsok:
                self._fut(list(p.argv))
            return
        self._fut(emelt_argv(parancsok, linux_emelo()))

    def _fut(self, argv: list[str]) -> None:
        for sor in self._sorok(argv):
            self.kimenet(sor)

    def _sorok(self, argv: list[str]) -> Iterator[str]:
        extra = {}
        if sys.platform.startswith("win"):
            extra["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        with subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                              errors="replace", bufsize=1, **extra) as folyamat:
            assert folyamat.stdout is not None
            for sor in folyamat.stdout:
                yield sor.rstrip()
        if folyamat.returncode != 0:
            raise FuttatasiHiba(f"A parancs {folyamat.returncode} kóddal állt le: {argv[0]}")
