"""Import supplied daily upper-limit prices; never infer a limit from a percentage."""

import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Security
from .readers.tdx import stock_security


@dataclass(frozen=True)
class LimitPriceBook:
    entries: dict[tuple[Security, date], int | None]
    path: Path
    sha256: str


def load_limit_prices(path: Path) -> LimitPriceBook:
    path = path.resolve()
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    required = {"market", "code", "date", "limit_up_price"}
    if not required <= set(reader.fieldnames or []):
        raise ValueError("Limit-price CSV requires market,code,date,limit_up_price columns")
    entries = {}
    for line, row in enumerate(reader, start=2):
        try:
            market, code = row["market"].strip().lower(), row["code"].strip()
            if len(code) != 6 or not code.isdigit():
                raise ValueError("code must contain six digits")
            security = stock_security(market + code + ".day")
            if security is None:
                raise ValueError("unsupported stock code")
            day = date.fromisoformat(row["date"].strip())
            value = row["limit_up_price"].strip()
            if value.lower() == "none":
                price = None  # Explicitly confirmed unlimited for this security/date.
            else:
                amount = Decimal(value)
                if not amount.is_finite() or amount <= 0:
                    raise ValueError("limit price must be finite and positive, or 'none'")
                cents = amount * 100
                if cents != cents.to_integral_value():
                    raise ValueError("limit price must be an exact number of cents")
                price = int(cents)
            key = security, day
            if key in entries:
                raise ValueError("duplicate security/date")
            entries[key] = price
        except (ValueError, InvalidOperation, AttributeError, TypeError) as exc:
            raise ValueError(f"Limit-price CSV line {line}: {exc}") from None
    if not entries:
        raise ValueError("Limit-price CSV contains no records; fill the template with verified daily prices")
    return LimitPriceBook(entries, path, hashlib.sha256(raw).hexdigest())
