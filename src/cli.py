import argparse
import sys
import zipfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import __version__
from .names import load_names
from .reports import write_report
from .service import scan
from .sources import SOURCE_FACTORIES, open_source
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
    parser = argparse.ArgumentParser(description=f"StockStudy {__version__} 本地日线筛选")
    parser.add_argument("--version", "-version", "-V", action="version", version=f"StockStudy {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sources", help="列出数据源和规划状态")
    command = commands.add_parser("scan", help="扫描本地日线")
    command.add_argument("--workspace", type=Path, help="包含 stock_data/output 的工作区")
    command.add_argument("--source", choices=sorted(SOURCE_FACTORIES), default="tdx")
    command.add_argument("--data", type=Path, help="通达信 ZIP 或解压目录")
    command.add_argument("--strategy", choices=["pattern", "pattern-drop"], default="pattern")
    command.add_argument("--lookback", type=positive_int, help="最近记录数；两种模式默认分别为 1 / 100")
    command.add_argument("--drop-threshold", default="0.4", help="严格大于的跌幅阈值，默认 0.4")
    command.add_argument("--reference-days", default="40,20,10,5", help="历史参考位置，逗号分隔")
    command.add_argument("--as-of", type=date.fromisoformat, help="只扫描最后一条记录恰为该日期的股票 YYYY-MM-DD")
    command.add_argument("--names", type=Path, help="自定义 market,code,name CSV")
    command.add_argument("--output-dir", type=Path, help="分析结果根目录")
    command.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "sources":
        print("tdx       implemented: 通达信 .day 目录 / ZIP（沪深股票）")
        print("csv       planned: 标准 CSV 文件")
        print("akshare   planned: AKShare 数据适配器")
        print("tushare   planned: Tushare 数据适配器")
        print("baostock  planned: BaoStock 数据适配器")
        return 0
    workspace = (args.workspace or find_workspace()).resolve()
    data_path = args.data or workspace / "stock_data" / "tongdaxin" / "hsjday.zip"
    output_dir = args.output_dir or workspace / "output"
    try:
        strategy = Strategy(
            args.strategy, args.lookback or (100 if args.strategy == "pattern-drop" else 1),
            Decimal(args.drop_threshold), tuple(int(n.strip()) for n in args.reference_days.split(",")),
        )
        names = load_names(args.names)
        source = open_source(args.source, data_path)
        try:
            def progress(done, total):
                if not args.quiet and (done % 1000 == 0 or done == total):
                    print(f"Scanned {done}/{total}", file=sys.stderr)
            result = scan(source, strategy, as_of=args.as_of, progress=progress)
        finally:
            source.close()
        report_dir = write_report(
            result, strategy, names, output_dir,
            source_name=args.source, data_path=data_path,
            as_of=args.as_of.isoformat() if args.as_of else None,
        )
    except (OSError, ValueError, InvalidOperation, zipfile.BadZipFile, EOFError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    failures = sum(e["kind"] == "read_error" for e in result.errors)
    exclusions = sum(e["kind"] == "date_mismatch" for e in result.errors)
    print(f"Read {result.scanned}; matches {len(result.matches)}; read errors {failures}; date exclusions {exclusions}")
    print(f"Reports: {report_dir.resolve()}")
    # Date exclusions are reported, but are not data read failures.
    return 2 if failures else 0
