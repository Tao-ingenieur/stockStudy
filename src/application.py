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


@dataclass(frozen=True)
class AnalysisRequest:
    data: Path
    strategy: Strategy
    as_of: date | None = None
    include_delisted: bool = False


@dataclass(frozen=True)
class AnalysisOutcome:
    summary: dict
    rows: list[dict]


def make_request(data, period, threshold, as_of, include_delisted=False, language="zh") -> AnalysisRequest:
    if not data.strip():
        raise ValueError(translate(language, "missing_data"))
    data_path = Path(data.strip().strip('"')).expanduser().resolve()
    if not data_path.exists():
        raise ValueError(translate(language, "bad_path", path=data_path))
    try:
        strategy = Strategy(period=int(period), gain_threshold=Decimal(threshold) / 100)
    except (ValueError, InvalidOperation):
        raise ValueError(translate(language, "bad_parameters")) from None
    try:
        day = date.fromisoformat(as_of.strip()) if as_of.strip() else None
    except ValueError:
        raise ValueError(translate(language, "bad_date")) from None
    return AnalysisRequest(data_path, strategy, day, include_delisted)


def analyze(request: AnalysisRequest, *, progress: Callable[[int, int], None] | None = None,
            cancelled: Callable[[], bool] | None = None) -> AnalysisOutcome:
    security_info = load_security_info()
    names = {security: info.name for security, info in security_info.items()}
    source = open_source("tdx", request.data)
    try:
        result = scan(source, request.strategy, as_of=request.as_of, progress=progress, cancelled=cancelled,
                      security_info=security_info, include_delisted=request.include_delisted)
    finally:
        source.close()
    if cancelled and cancelled():
        raise ScanCancelled()
    rows, summary = prepare_report(result, request.strategy, names,
        source_name="tdx", data_path=request.data, as_of=request.as_of.isoformat() if request.as_of else None,
        security_info=security_info)
    return AnalysisOutcome(summary, rows)


def export_analysis(outcome: AnalysisOutcome, output: Path) -> Path:
    return export_report(outcome.rows, outcome.summary, output)
