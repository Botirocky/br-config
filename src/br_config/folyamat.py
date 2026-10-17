__lazy_modules__ = ["subprocess"]

import os
import subprocess
import sys
from functools import cache

WINDOWS = sys.platform.startswith("win")


@cache
def oem_kodlap() -> str:
    if not WINDOWS:
        return "utf-8"
    import ctypes

    try:
        return f"cp{ctypes.windll.kernel32.GetOEMCP()}"
    except (AttributeError, OSError):
        return "cp852"


def dekodol(adat: bytes) -> str:
    try:
        return adat.decode("utf-8")
    except UnicodeDecodeError:
        return adat.decode(oem_kodlap(), errors="replace")


def gyermek_kornyezet() -> dict[str, str]:
    kornyezet = dict(os.environ)
    kornyezet["PYTHONIOENCODING"] = "utf-8"
    kornyezet["PYTHONUTF8"] = "1"
    return kornyezet


def ablak_nelkul() -> dict:
    if WINDOWS:
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


def kimenet(argv: list[str], idokorlat: float = 30) -> str:
    try:
        eredmeny = subprocess.run(argv, capture_output=True, timeout=idokorlat,
                                  stdin=subprocess.DEVNULL, env=gyermek_kornyezet(),
                                  **ablak_nelkul())
    except (OSError, subprocess.SubprocessError):
        return ""
    return dekodol(eredmeny.stdout)
