import csv
import sys
from importlib.resources import files
from pathlib import Path

from .models import Security


def default_names() -> Path:
    # The source checkout has resources alongside src; wheels and zipapps bundle it.
    checkout = Path(__file__).resolve().parents[1] / "resources" / "security_names.csv"
    if checkout.is_file():
        return checkout
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "stockstudy" / "resources" / "security_names.csv"
    return files("stockstudy").joinpath("resources/security_names.csv")


def load_names(path=None) -> dict[Security, str]:
    names = {}
    resource = path if path is not None else default_names()
    with resource.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"market", "code", "name"} <= set(reader.fieldnames or []):
            raise ValueError("Names CSV must contain market,code,name columns")
        for row in reader:
            security = Security(row["market"].strip().lower(), row["code"].strip())
            if security.market not in {"sh", "sz", "bj"} or len(security.code) != 6 or not security.code.isdigit():
                raise ValueError(f"Invalid security in names CSV: {row}")
            if security in names:
                raise ValueError(f"Duplicate name entry: {security.symbol}")
            names[security] = row["name"].strip()
    return names
