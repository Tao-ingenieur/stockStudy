from datetime import date
from typing import Callable

from .models import ScanResult, Security, SecurityInfo
from .readers.base import DailyBarSource
from .strategies import Strategy, screen


class ScanCancelled(Exception):
    """User cancelled before a complete report was produced."""


def scan(
    source: DailyBarSource,
    strategy: Strategy,
    *,
    as_of: date | None = None,
    progress: Callable[[int, int], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
    security_info: dict[Security, SecurityInfo] | None = None,
    include_delisted: bool = False,
) -> ScanResult:
    """as_of requires each security's last record to have exactly that date."""
    result = ScanResult()
    securities = source.securities()
    for index, security in enumerate(securities, start=1):
        if cancelled and cancelled():
            raise ScanCancelled()
        info = security_info.get(security) if security_info is not None else None
        if info and info.status == "delisted" and not include_delisted:
            result.delisted_excluded.append(security.symbol)
            if progress:
                progress(index, len(securities))
            continue
        if security_info is not None and (info is None or info.status == "unknown"):
            result.unknown_status.append(security.symbol)
        try:
            bars = source.read_bars(security, strategy.required_bars)
            if not bars:
                result.empty += 1
            else:
                latest = bars[-1].date
                result.dates[security] = latest
                if as_of is None or latest == as_of:
                    if len(bars) < strategy.required_bars:
                        result.insufficient_history.append(security.symbol)
                    elif bars[-1].close <= 0 or bars[-strategy.required_bars].close <= 0:
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
    result.matches.sort(key=lambda m: (-m.date.toordinal(), -m.gain_ratio, m.security.market, m.security.code))
    return result
