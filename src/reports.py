import csv
import json
from uuid import uuid4
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .models import ScanResult, Security, SecurityInfo
from .strategies import Strategy
from .boards import board_for


def price(cents: int | None) -> str:
    return "" if cents is None else f"{cents // 100}.{cents % 100:02d}"


def prepare_report(
    result: ScanResult, strategy: Strategy, names: dict[Security, str],
    *, source_name: str, data_path: Path, as_of: str | None,
    security_info: dict[Security, SecurityInfo] | None = None,
) -> tuple[list[dict], dict]:
    rows = []
    for item in result.matches:
        info = security_info.get(item.security) if security_info is not None else None
        row = {
            "market": item.security.market, "code": item.security.code,
            "name": names.get(item.security, ""), "date": item.date.isoformat(),
            "board": board_for(item.security.market, item.security.code),
            "status": info.status if info is not None else "unknown",
            "close": price(item.close), "price_adjustment": "unadjusted",
        }
        if strategy.name == "gain":
            row.update(base_date=item.base_date.isoformat(), base_close=price(item.base_close),
                       gain_ratio=float(round(item.gain_ratio, 10)), gain_pct=float(round(item.gain_ratio * 100, 6)))
        else:
            row.update(previous_date=item.previous_date.isoformat(),
                       **{key: format(getattr(item, key) / 100, ".6f") if getattr(item, key) is not None else ""
                          for key in ("fast_ma", "slow_ma", "previous_fast_ma", "previous_slow_ma", "trend_ma")})
        rows.append(row)
    summary = {
        "version": __version__, "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source_name, "data_path": str(data_path.resolve()),
        "price_adjustment": "unadjusted", "volume_unit": "shares", "price_unit": "CNY",
        "strategy": strategy.name, "required_bars": strategy.required_bars,
        "price_basis_note": "Unadjusted daily prices; corporate actions may affect returns and MA signals. Not exchange-published daily change.",
        "insufficient_history_count": len(result.insufficient_history),
        "insufficient_history": result.insufficient_history,
        "invalid_close_count": len(result.invalid_close), "invalid_close": result.invalid_close,
        "required_latest_date": result.effective_date.isoformat() if result.effective_date else as_of, "securities_total": result.scanned + sum(
            e["kind"] == "read_error" for e in result.errors),
        "securities_read": result.scanned, "empty_files": result.empty,
        "matches": len(rows), "matched_securities": len({(r["market"], r["code"]) for r in rows}),
        "latest_date_counts": dict(sorted(Counter(d.isoformat() for d in result.dates.values()).items())),
        "missing_name_count": sum(s not in names for s in result.dates),
        "read_errors": sum(e["kind"] == "read_error" for e in result.errors),
        "date_mismatches": sum(e["kind"] == "date_mismatch" for e in result.errors),
        "errors": result.errors,
    }
    if strategy.name == "gain":
        summary.update(period=strategy.period, gain_threshold_pct=str(strategy.gain_threshold * 100),
                       comparison="latest_close / close_N_records_earlier - 1 >= threshold")
    else:
        summary.update(fast_period=strategy.fast_period, slow_period=strategy.slow_period,
                       trend_filter=strategy.trend_filter, trend_period=strategy.trend_period,
                       comparison="previous_fast_ma <= previous_slow_ma and fast_ma > slow_ma",
                       trend_comparison="close > trend_ma" if strategy.trend_filter else "disabled")
    return rows, summary


def export_report(rows: list[dict], summary: dict, output_dir: Path) -> Path:
    """Persist a completed result only when the caller explicitly requests export."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"股票分析_{stamp}_{uuid4().hex[:12]}"
    run_dir.mkdir()
    columns = ["market", "code", "name", "board", "status", "date", "close"]
    columns += (["previous_date", "fast_ma", "slow_ma", "previous_fast_ma", "previous_slow_ma", "trend_ma"]
                if summary.get("strategy") == "ma-cross" else ["base_date", "base_close", "gain_ratio", "gain_pct"])
    columns += ["price_adjustment"]
    with (run_dir / "matches.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    (run_dir / "matches.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    export_summary = dict(summary)
    export_summary.setdefault("export_scope", "all")
    export_summary.setdefault("export_record_count", len(rows))
    (run_dir / "summary.json").write_text(json.dumps(export_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_dir
