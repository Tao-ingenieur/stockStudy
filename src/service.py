from datetime import date
from typing import Callable

from .models import ScanResult, Security, SecurityInfo
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
    security_info: dict[Security, SecurityInfo] | None = None,
    include_delisted: bool = False,
    limit_prices: dict[tuple[Security, date], int | None] | None = None,
) -> ScanResult:
    """as_of requires each security's last record to have exactly that date."""
    if strategy.name == "limit-up" and limit_prices is None:
        raise ValueError("The limit-up strategy requires verified daily upper-limit prices")
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
                    elif not valid_closes(bars, strategy):
                        result.invalid_close.append(security.symbol)
                    elif strategy.name == "limit-up":
                        key = security, latest
                        if key not in limit_prices:
                            result.missing_limits.append(security.symbol)
                        elif limit_prices[key] is None:
                            result.unlimited.append(security.symbol)
                        elif bars[-1].high > limit_prices[key]:
                            result.errors.append({"symbol": security.symbol, "kind": "limit_data_error",
                                                  "error": f"Daily high exceeds supplied limit price on {latest}"})
                        else:
                            result.matches.extend(screen(security, bars, strategy, limit_up_price=limit_prices[key]))
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
    result.matches.sort(key=lambda m: (-m.date.toordinal(), -(m.gain_ratio or 0), m.security.market, m.security.code))
    return result
