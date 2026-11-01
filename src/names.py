import csv
import sys
from importlib.resources import files
from pathlib import Path
from datetime import date

from .models import Security, SecurityInfo


def default_names() -> Path:
    if getattr(sys, "frozen", False):
        external = Path(sys.executable).resolve().parent / "security_names.csv"
        if external.is_file():
            return external
    elif Path(sys.argv[0]).suffix.lower() == ".pyz":
        external = Path(sys.argv[0]).resolve().parent / "security_names.csv"
        if external.is_file():
            return external
    # The source checkout has resources alongside src; wheels and zipapps bundle it.
    checkout = Path(__file__).resolve().parents[1] / "resources" / "security_names.csv"
    if checkout.is_file():
        return checkout
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "stockstudy" / "resources" / "security_names.csv"
    return files("stockstudy").joinpath("resources/security_names.csv")


def load_security_info(path=None) -> dict[Security, SecurityInfo]:
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
            flag = row.get("is_delisted", "unknown").strip().lower() or "unknown"
            if flag not in {"true", "false", "unknown"}:
                raise ValueError(f"Invalid is_delisted for {security.symbol}: {flag}")
            def read_date(column):
                value = row.get(column, "").strip()
                return date.fromisoformat(value) if value else None
            names[security] = SecurityInfo(
                row["name"].strip(), {"true": True, "false": False, "unknown": None}[flag],
                read_date("listing_date"), read_date("delisting_date"),
                row.get("status_source", "").strip(), read_date("status_checked_at"),
            )
    return names


def load_names(path=None) -> dict[Security, str]:
    return {security: info.name for security, info in load_security_info(path).items()}
