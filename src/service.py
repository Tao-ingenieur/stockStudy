from datetime import date
from typing import Callable

from .models import ScanResult
from .readers.base import DailyBarSource
from .strategies import Strategy, screen, valid_closes


class ScanCancelled(Exception):
    """User cancelled before a complete report was produced."""


def scan(
    source: DailyBarSource,
    strategy: Strategy,
    *,
    as_of: date | None = None,
    progress: Callable[[int, int], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> ScanResult:
    """as_of requires each security's last record to have exactly that date."""
    result = ScanResult()
    dataset_latest = None
    securities = source.securities()
    for index, security in enumerate(securities, start=1):
        if cancelled and cancelled():
            raise ScanCancelled()
        try:
            bars = source.read_bars(security, strategy.required_bars)
            if not bars:
                result.empty += 1
            else:
                latest = bars[-1].date
                dataset_latest = max(dataset_latest or latest, latest)
                result.dates[security] = latest
                if as_of is None or latest == as_of:
                    if len(bars) < strategy.required_bars:
                        result.insufficient_history.append(security.symbol)
                    elif not valid_closes(bars, strategy):
                        result.invalid_close.append(security.symbol)
                    else:
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
    # Resolve the common date after reading, without decompressing the ZIP twice.
    result.effective_date = as_of or dataset_latest
    if as_of is None and result.effective_date is not None:
        stale = {security.symbol for security, day in result.dates.items()
                 if day != result.effective_date}
        result.matches = [match for match in result.matches if match.security.symbol not in stale]
        result.insufficient_history = [symbol for symbol in result.insufficient_history if symbol not in stale]
        result.invalid_close = [symbol for symbol in result.invalid_close if symbol not in stale]
        result.errors.extend({"symbol": symbol, "kind": "date_mismatch",
                              "error": f"Latest record differs from dataset latest date {result.effective_date}"}
                             for symbol in sorted(stale))
    result.matches.sort(key=lambda m: (-m.date.toordinal(), -(m.gain_ratio or 0), m.security.market, m.security.code))
    return result
