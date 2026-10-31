"""Interactive console launcher for double-clicking the Windows executable."""

import sys
import traceback
from pathlib import Path

from . import __version__
from .cli import find_workspace, main as cli_main


def interactive() -> int:
    workspace = find_workspace()
    data = workspace / "stock_data" / "tongdaxin" / "hsjday.zip"
    output = workspace / "output"
    while True:
        print(f"\nStockStudy {__version__} 股票日线筛选")
        print(f"行情数据：{data}\n结果目录：{output}")
        print("1 价格形态筛选（最近 1 条记录）")
        print("2 价格形态与跌幅筛选（最近 100 条记录）")
        print("3 修改行情和结果目录\n4 查看命令行帮助\n0 退出")
        choice = input("请选择 [0-4]：").strip()
        if choice == "0":
            return 0
        if choice == "3":
            entered = input("行情 ZIP 或解压目录（回车保留）：").strip().strip('"')
            if entered:
                data = Path(entered).expanduser().resolve()
            entered = input("结果目录（回车保留）：").strip().strip('"')
            if entered:
                output = Path(entered).expanduser().resolve()
            continue
        if choice == "4":
            try:
                cli_main(["--help"])
            except SystemExit as stopped:
                if stopped.code:
                    raise
        elif choice in {"1", "2"}:
            print("\n正在分析，请稍候……", flush=True)
            status = cli_main([
                "scan", "--strategy", "pattern" if choice == "1" else "pattern-drop",
                "--data", str(data), "--output-dir", str(output),
            ])
            print({0: "分析完成，结果位置见上方 Reports。", 1: "分析未完成，请查看上方错误及数据路径。",
                   2: "分析完成，部分文件读取失败，请查看 summary.json。"}[status])
        else:
            print("请输入 0 到 4。")
            continue
        input("按回车返回菜单……")


def main(argv=None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments:
        return cli_main(arguments)
    try:
        return interactive()
    except (EOFError, KeyboardInterrupt):
        return 0
    except Exception:
        traceback.print_exc()
        try:
            input("程序发生错误，请保留上方错误信息。按回车退出……")
        except (EOFError, KeyboardInterrupt):
            pass
        return 1
