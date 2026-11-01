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


@dataclass(frozen=True)
class AnalysisRequest:
    data: Path
    strategy: Strategy
    as_of: date | None = None


@dataclass(frozen=True)
class AnalysisOutcome:
    summary: dict
    rows: list[dict]


def make_request(data, period, threshold, as_of, language="zh",
                 strategy_name="gain", fast_period="5", slow_period="20", trend_filter=True, trend_period="120",
                 breakout_period="20", volume_period="5", volume_multiple="1.5") -> AnalysisRequest:
    if not data.strip():
        raise ValueError(translate(language, "missing_data"))
    data_path = Path(data.strip().strip('"')).expanduser().resolve()
    if not data_path.exists():
        raise ValueError(translate(language, "bad_path", path=data_path))
    try:
        if strategy_name == "breakout":
            strategy = Strategy(name="breakout", breakout_period=int(breakout_period),
                                volume_period=int(volume_period), volume_multiple=Decimal(volume_multiple))
        elif strategy_name == "ma-cross":
            strategy = Strategy(name=strategy_name, fast_period=int(fast_period), slow_period=int(slow_period),
                                trend_filter=trend_filter, trend_period=int(trend_period) if trend_filter else 120)
        else:
            strategy = Strategy(name=strategy_name, period=int(period), gain_threshold=Decimal(threshold) / 100)
    except (ValueError, InvalidOperation):
        raise ValueError(translate(language, {"ma-cross": "bad_ma_parameters", "breakout": "bad_breakout_parameters"}.get(strategy_name, "bad_parameters"))) from None
    try:
        day = date.fromisoformat(as_of.strip()) if as_of.strip() else None
    except ValueError:
        raise ValueError(translate(language, "bad_date")) from None
    return AnalysisRequest(data_path, strategy, day)


def analyze(request: AnalysisRequest, *, progress: Callable[[int, int], None] | None = None,
            cancelled: Callable[[], bool] | None = None) -> AnalysisOutcome:
    security_info = load_security_info()
    names = {security: info.name for security, info in security_info.items()}
    source = open_source("tdx", request.data)
    try:
        result = scan(source, request.strategy, as_of=request.as_of, progress=progress, cancelled=cancelled)
    finally:
        source.close()
    if cancelled and cancelled():
        raise ScanCancelled()
    rows, summary = prepare_report(result, request.strategy, names,
        source_name="tdx", data_path=request.data, as_of=request.as_of.isoformat() if request.as_of else None,
        security_info=security_info)
    return AnalysisOutcome(summary, rows)


MARKET_FILTERS = {"all": None, "sh": {"sh"}, "sz": {"sz"}, "bj": {"bj"}, "shsz": {"sh", "sz"}}


def filter_results(rows: list[dict], *, market="all", query="", board="all") -> list[dict]:
    """Filter completed results in memory; do not alter the analysis or its order."""
    if market not in MARKET_FILTERS or board not in BOARD_FILTERS:
        raise ValueError("Unknown result filter")
    markets = MARKET_FILTERS[market]
    term = query.strip().casefold()
    return [row for row in rows
            if (markets is None or row["market"] in markets)
            and (board == "all" or board_for(row["market"], row["code"]) == board)
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
