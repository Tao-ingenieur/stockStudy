"""Application operations independent of the desktop widgets."""

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

from .names import load_security_info
from .readers import open_source
from .reports import write_report
from .service import ScanCancelled, scan
from .strategies import Strategy


@dataclass(frozen=True)
class AnalysisRequest:
    data: Path
    output: Path
    strategy: Strategy
    as_of: date | None = None
    include_delisted: bool = False


@dataclass(frozen=True)
class AnalysisOutcome:
    directory: Path
    summary: dict
    rows: list[dict]


def make_request(data, output, mode, lookback, threshold, references, as_of, include_delisted=False) -> AnalysisRequest:
    if not data.strip():
        raise ValueError("请选择通达信 ZIP 文件或解压后的数据目录。")
    data_path = Path(data.strip().strip('"')).expanduser().resolve()
    if not data_path.exists():
        raise ValueError(f"行情路径不存在：\n{data_path}")
    if not output.strip():
        raise ValueError("请选择分析结果保存目录。")
    output_path = Path(output.strip().strip('"')).expanduser().resolve()
    if output_path.exists() and not output_path.is_dir():
        raise ValueError("结果保存路径必须是文件夹。")
    try:
        count = int(lookback)
        ratio = Decimal(threshold) / 100 if mode == "pattern-drop" else Decimal("0.4")
        offsets = tuple(int(item.strip()) for item in references.replace("，", ",").split(",")) if mode == "pattern-drop" else (40, 20, 10, 5)
        strategy = Strategy(mode, count, ratio, offsets)
    except (ValueError, InvalidOperation):
        raise ValueError("请检查参数：记录数和参考位置须为正整数，跌幅阈值须在 0% 到 100% 之间。") from None
    try:
        day = date.fromisoformat(as_of.strip()) if as_of.strip() else None
    except ValueError:
        raise ValueError("末条日期请使用 YYYY-MM-DD 格式，或留空。") from None
    return AnalysisRequest(data_path, output_path, strategy, day, include_delisted)


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
    directory = write_report(result, request.strategy, names, request.output,
        source_name="tdx", data_path=request.data, as_of=request.as_of.isoformat() if request.as_of else None,
        security_info=security_info)
    return AnalysisOutcome(directory,
        json.loads((directory / "summary.json").read_text(encoding="utf-8")),
        json.loads((directory / "matches.json").read_text(encoding="utf-8")))
