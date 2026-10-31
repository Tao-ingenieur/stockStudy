"""Read official TDX .day records using only the Python standard library."""

import math
import re
import struct
import zipfile
import zlib
from datetime import datetime
from pathlib import Path

from ..models import DailyBar, Security

RECORD = struct.Struct("<IIIIIfII")
FILENAME = re.compile(r"^(sh|sz)(\d{6})\.day$", re.IGNORECASE)


def stock_security(filename: str) -> Security | None:
    match = FILENAME.fullmatch(filename)
    if not match:
        return None
    market, code = match[1].lower(), match[2]
    # Shanghai 6 / Shenzhen 00,30 stock universe.
    if (market == "sh" and code.startswith("6")) or (
        market == "sz" and code.startswith(("00", "30"))
    ):
        return Security(market, code)
    return None


def parse_records(data: bytes, *, label: str = "TDX data") -> list[DailyBar]:
    if len(data) % RECORD.size:
        raise ValueError(f"{label}: byte count is not a multiple of {RECORD.size}")
    bars = []
    for raw_date, opening, high, low, close, amount, volume, _ in RECORD.iter_unpack(data):
        day = datetime.strptime(str(raw_date), "%Y%m%d").date()
        if not math.isfinite(amount) or amount < 0:
            raise ValueError(f"{label}: invalid turnover amount on {day}")
        if low > high or not low <= opening <= high or not low <= close <= high:
            raise ValueError(f"{label}: inconsistent OHLC on {day}")
        if bars and day <= bars[-1].date:
            raise ValueError(f"{label}: dates must be strictly increasing")
        bars.append(DailyBar(day, opening, high, low, close, amount, volume))
    return bars


class TdxSource:
    """Accept a ZIP or a directory containing vipdoc/sh/lday or sh/lday."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self._archive: zipfile.ZipFile | None = None
        self._files: dict[Security, Path | zipfile.ZipInfo] = {}
        if self.path.is_file() and self.path.suffix.lower() == ".zip":
            try:
                self._archive = zipfile.ZipFile(self.path)
                for entry in self._archive.infolist():
                    normalized = entry.filename.replace("\\", "/")
                    if not entry.is_dir() and "/lday/" in "/" + normalized.lower():
                        self._add(normalized.rsplit("/", 1)[-1], entry)
            except Exception:
                self.close()
                raise
        elif self.path.is_dir():
            for entry in sorted(self.path.rglob("*")):
                if entry.is_file() and entry.parent.name.lower() == "lday":
                    self._add(entry.name, entry)
        else:
            raise ValueError(f"Data path is not a ZIP or directory: {self.path}")
        if not self._files:
            self.close()
            raise ValueError(f"No supported Shanghai/Shenzhen .day files found in {self.path}")

    def _add(self, filename: str, entry: Path | zipfile.ZipInfo) -> None:
        security = stock_security(filename)
        if security is not None:
            if security in self._files:
                raise ValueError(f"Duplicate security {security.symbol}; select a single dataset")
            self._files[security] = entry

    def securities(self) -> list[Security]:
        return sorted(self._files, key=lambda s: (s.market, s.code))

    def read_bars(self, security: Security, limit: int) -> list[DailyBar]:
        if limit < 1:
            raise ValueError("Read limit must be positive")
        entry = self._files[security]
        size = entry.file_size if isinstance(entry, zipfile.ZipInfo) else entry.stat().st_size
        if size % RECORD.size:
            raise ValueError(f"{security.symbol}: file size is not a multiple of 32")
        # A ZIP seek still decompresses preceding bytes, but only the required tail is parsed.
        try:
            stream = self._archive.open(entry) if self._archive is not None else entry.open("rb")
            with stream:
                stream.seek(max(0, size - limit * RECORD.size))
                data = stream.read()
        except (zipfile.BadZipFile, zlib.error) as exc:
            raise ValueError(f"{security.symbol}: damaged ZIP member: {exc}") from exc
        return parse_records(data, label=security.symbol)

    def close(self) -> None:
        if self._archive is not None:
            self._archive.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
