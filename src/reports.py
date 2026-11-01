import csv
import json
from uuid import uuid4
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .models import ScanResult, Security, SecurityInfo
from .strategies import Strategy


def price(cents: int | None) -> str:
    return "" if cents is None else f"{cents // 100}.{cents % 100:02d}"


def write_report(
    result: ScanResult, strategy: Strategy, names: dict[Security, str], output_dir: Path,
    *, source_name: str, data_path: Path, as_of: str | None,
    security_info: dict[Security, SecurityInfo] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"{stamp}_{strategy.name}_{uuid4().hex[:12]}"
    run_dir.mkdir()
    rows = []
    for item in result.matches:
        high = item.reference_high
        info = security_info.get(item.security) if security_info is not None else None
        rows.append({
            "market": item.security.market, "code": item.security.code,
            "name": names.get(item.security, ""), "date": item.date.isoformat(),
            "status": info.status if info is not None else "unknown",
            "low": price(item.low), "pattern": item.pattern,
            "reference_days": item.reference_days,
            "reference_date": item.reference_date.isoformat() if item.reference_date else "",
            "reference_high": price(high),
            "drop_ratio": round((high - item.low) / high, 8) if high else None,
        })
    columns = ["market", "code", "name", "status", "date", "low", "pattern", "reference_days",
               "reference_date", "reference_high", "drop_ratio"]
    with (run_dir / "matches.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    (run_dir / "matches.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "version": __version__, "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source_name, "data_path": str(data_path.resolve()),
        "price_adjustment": "unadjusted", "volume_unit": "shares", "price_unit": "CNY",
        "strategy": strategy.name, "lookback": strategy.lookback,
        "drop_threshold": str(strategy.drop_threshold), "reference_days": list(strategy.reference_days),
        "required_latest_date": as_of, "securities_total": result.scanned + sum(
            e["kind"] == "read_error" for e in result.errors) + len(result.delisted_excluded),
        "securities_read": result.scanned, "empty_files": result.empty,
        "matches": len(rows), "matched_securities": len({(r["market"], r["code"]) for r in rows}),
        "latest_date_counts": dict(sorted(Counter(d.isoformat() for d in result.dates.values()).items())),
        "missing_name_count": sum(s not in names for s in result.dates),
        "read_errors": sum(e["kind"] == "read_error" for e in result.errors),
        "date_mismatches": sum(e["kind"] == "date_mismatch" for e in result.errors),
        "delisted_excluded_count": len(result.delisted_excluded),
        "delisted_excluded": result.delisted_excluded,
        "unknown_listing_status_count": len(result.unknown_status),
        "unknown_listing_status": result.unknown_status,
        "errors": result.errors,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_dir
