from datetime import date
from typing import Callable

from .models import ScanResult
from .readers.base import DailyBarSource
from .strategies import Strategy, screen


def scan(
    source: DailyBarSource,
    strategy: Strategy,
    *,
    as_of: date | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> ScanResult:
    """as_of requires each security's last record to have exactly that date."""
    result = ScanResult()
    securities = source.securities()
    for index, security in enumerate(securities, start=1):
        try:
            bars = source.read_bars(security, strategy.required_bars)
            if not bars:
                result.empty += 1
            else:
                latest = bars[-1].date
                result.dates[security] = latest
                if as_of is None or latest == as_of:
                    result.matches.extend(screen(security, bars, strategy))
                else:
                    result.errors.append({
                        "symbol": security.symbol,
                        "error": f"Latest record {latest} differs from required date {as_of}",
                        "kind": "date_mismatch",
                    })
            result.scanned += 1
        except (OSError, ValueError, EOFError, RuntimeError) as exc:
            result.errors.append({"symbol": security.symbol, "error": str(exc), "kind": "read_error"})
        if progress:
            progress(index, len(securities))
    result.matches.sort(key=lambda m: (-m.date.toordinal(), m.security.market, m.security.code))
    return result
