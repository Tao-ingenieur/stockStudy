"""Application operations independent of the desktop widgets."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

from .names import load_security_info
from .readers import open_source
from .reports import prepare_report, export_report
from .service import ScanCancelled, scan
from .strategies import Strategy
from .i18n import translate
from .boards import BOARD_FILTERS, board_for
from .limit_prices import load_limit_prices


@dataclass(frozen=True)
class AnalysisRequest:
    data: Path
    strategy: Strategy
    as_of: date | None = None
    include_delisted: bool = False
    limit_prices_path: Path | None = None


@dataclass(frozen=True)
class AnalysisOutcome:
    summary: dict
    rows: list[dict]


def make_request(data, period, threshold, as_of, include_delisted=False, language="zh",
                 strategy_name="gain", fast_period="5", slow_period="20", trend_filter=True, trend_period="120",
                 gain_comparison="ge", limit_prices_path="") -> AnalysisRequest:
    if not data.strip():
        raise ValueError(translate(language, "missing_data"))
    data_path = Path(data.strip().strip('"')).expanduser().resolve()
    if not data_path.exists():
        raise ValueError(translate(language, "bad_path", path=data_path))
    try:
        if strategy_name == "limit-up":
            strategy = Strategy(name=strategy_name)
        elif strategy_name == "ma-cross":
            strategy = Strategy(name=strategy_name, fast_period=int(fast_period), slow_period=int(slow_period),
                                trend_filter=trend_filter, trend_period=int(trend_period) if trend_filter else 120)
        else:
            strategy = Strategy(name=strategy_name, period=int(period), gain_threshold=Decimal(threshold) / 100, gain_comparison=gain_comparison)
    except (ValueError, InvalidOperation):
        raise ValueError(translate(language, "bad_ma_parameters" if strategy_name == "ma-cross" else "bad_parameters")) from None
    try:
        day = date.fromisoformat(as_of.strip()) if as_of.strip() else None
    except ValueError:
        raise ValueError(translate(language, "bad_date")) from None
    limit_path = None
    if strategy_name == "limit-up":
        limit_path = Path(str(limit_prices_path).strip().strip('"')).expanduser().resolve() if str(limit_prices_path).strip() else None
        if limit_path is None or not limit_path.is_file():
            raise ValueError(translate(language, "need_limit_prices"))
    return AnalysisRequest(data_path, strategy, day, include_delisted, limit_path)


def analyze(request: AnalysisRequest, *, progress: Callable[[int, int], None] | None = None,
            cancelled: Callable[[], bool] | None = None) -> AnalysisOutcome:
    security_info = load_security_info()
    names = {security: info.name for security, info in security_info.items()}
    book = load_limit_prices(request.limit_prices_path) if request.strategy.name == "limit-up" else None
    source = open_source("tdx", request.data)
    try:
        result = scan(source, request.strategy, as_of=request.as_of, progress=progress, cancelled=cancelled,
                      security_info=security_info, include_delisted=request.include_delisted,
                      limit_prices=book.entries if book else None)
    finally:
        source.close()
    if cancelled and cancelled():
        raise ScanCancelled()
    rows, summary = prepare_report(result, request.strategy, names,
        source_name="tdx", data_path=request.data, as_of=request.as_of.isoformat() if request.as_of else None,
        security_info=security_info, limit_price_book=book)
    return AnalysisOutcome(summary, rows)


MARKET_FILTERS = {"all": None, "sh": {"sh"}, "sz": {"sz"}, "bj": {"bj"}, "shsz": {"sh", "sz"}}
STATUS_FILTERS = ("all", "listed", "delisted", "unknown")


def filter_results(rows: list[dict], *, market="all", status="all", query="", board="all") -> list[dict]:
    """Filter completed results in memory; do not alter the analysis or its order."""
    if market not in MARKET_FILTERS or status not in STATUS_FILTERS or board not in BOARD_FILTERS:
        raise ValueError("Unknown result filter")
    markets = MARKET_FILTERS[market]
    term = query.strip().casefold()
    return [row for row in rows
            if (markets is None or row["market"] in markets)
            and (board == "all" or board_for(row["market"], row["code"]) == board)
            and (status == "all" or row.get("status", "unknown") == status)
            and (not term or term in (row["market"] + row["code"] + " " +
                                      " ".join(str(row.get(key, "")) for key in
                                               ("market", "code", "name", "date"))).casefold())]


def export_analysis(outcome: AnalysisOutcome, output: Path, *, filters: dict | None = None) -> Path:
    rows = filter_results(outcome.rows, **filters) if filters is not None else outcome.rows
    summary = dict(outcome.summary)
    summary.update(export_scope="filtered" if filters is not None else "all", export_record_count=len(rows))
    if filters is not None:
        summary["result_filters"] = dict(filters)
    return export_report(rows, summary, output)
