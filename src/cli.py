import argparse
import sys
import zipfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import __version__
from .names import load_security_info
from .reports import prepare_report, export_report
from .service import scan
from .readers import SOURCE_FACTORIES, open_source
from .strategies import Strategy


def find_workspace() -> Path:
    starts = (Path.cwd(), Path(sys.executable).resolve().parent, Path(__file__).resolve().parent)
    for start in starts:
        for candidate in (start, *start.parents):
            if (candidate / "stock_data").is_dir() and (candidate / "output").is_dir():
                return candidate
    return Path.cwd()


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=f"股票分析 {__version__} 本地日线筛选")
    parser.add_argument("--version", "-version", "-V", action="version", version=f"股票分析 {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sources", help="列出数据源和规划状态")
    command = commands.add_parser("scan", help="扫描本地日线")
    command.add_argument("--workspace", type=Path, help="包含 stock_data/output 的工作区")
    command.add_argument("--source", choices=sorted(SOURCE_FACTORIES), default="tdx")
    command.add_argument("--data", type=Path, help="通达信 ZIP 或解压目录")
    command.add_argument("--strategy", choices=["gain", "ma-cross"], default="gain")
    command.add_argument("--period", type=positive_int, default=20, help="比较周期 N，按各股票交易记录计数；默认 20，需 N+1 条记录")
    command.add_argument("--gain-threshold", default="10", help="涨幅大于等于此百分比；10 表示 10%%，默认 10")
    command.add_argument("--fast-period", type=positive_int, default=5, help="金叉短期均线周期，默认5")
    command.add_argument("--slow-period", type=positive_int, default=20, help="金叉长期均线周期，默认20")
    command.add_argument("--trend-period", type=positive_int, default=120, help="趋势过滤均线周期，默认120")
    command.add_argument("--no-trend-filter", action="store_true", help="金叉不要求收盘价高于趋势均线；默认要求")
    command.add_argument("--as-of", type=date.fromisoformat, help="只扫描最后一条记录恰为该日期的股票 YYYY-MM-DD；留空使用行情数据中的最新交易日")
    command.add_argument("--names", type=Path, help="自定义 market,code,name,status,name_checked_at CSV")
    command.add_argument("--output-dir", type=Path, help="明确指定后才导出结果到此目录；默认不保存文件")
    command.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "sources":
        print("tdx       implemented: 通达信 .day 目录 / ZIP（沪深北股票）")
        print("csv       planned: 标准 CSV 文件")
        print("akshare   planned: AKShare 数据适配器")
        print("tushare   planned: Tushare 数据适配器")
        print("baostock  planned: BaoStock 数据适配器")
        return 0
    workspace = (args.workspace or find_workspace()).resolve()
    data_path = args.data or workspace / "stock_data" / "tongdaxin" / "hsjday.zip"
    output_dir = args.output_dir
    try:
        if args.strategy == "ma-cross":
            strategy = Strategy(name=args.strategy, fast_period=args.fast_period, slow_period=args.slow_period,
                                trend_filter=not args.no_trend_filter, trend_period=args.trend_period)
        else:
            strategy = Strategy(args.strategy, args.period, Decimal(args.gain_threshold) / 100)
        security_info = load_security_info(args.names)
        names = {security: info.name for security, info in security_info.items()}
        source = open_source(args.source, data_path)
        try:
            def progress(done, total):
                if not args.quiet and (done % 1000 == 0 or done == total):
                    print(f"Scanned {done}/{total}", file=sys.stderr)
            result = scan(source, strategy, as_of=args.as_of, progress=progress)
        finally:
            source.close()
        rows, summary = prepare_report(
            result, strategy, names,
            source_name=args.source, data_path=data_path,
            as_of=args.as_of.isoformat() if args.as_of else None,
            security_info=security_info,
        )
        report_dir = export_report(rows, summary, output_dir) if output_dir is not None else None
    except (OSError, ValueError, InvalidOperation, zipfile.BadZipFile, EOFError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    failures = sum(e["kind"] == "read_error" for e in result.errors)
    exclusions = sum(e["kind"] == "date_mismatch" for e in result.errors)
    print(f"Read {result.scanned}; matches {len(result.matches)}; read errors {failures}; date exclusions {exclusions}")
    print(f"Insufficient history {len(result.insufficient_history)}; invalid close {len(result.invalid_close)}; price basis: unadjusted daily prices")
    if report_dir is not None:
        print(f"Reports: {report_dir.resolve()}")
    else:
        print("Results were not saved. Use --output-dir to export CSV and JSON.")
    # Date exclusions are reported, but are not data read failures.
    return 2 if failures else 0
