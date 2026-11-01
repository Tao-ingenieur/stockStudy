import contextlib
import csv
import io
import json
import tempfile
import tkinter as tk
import unittest
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from stockstudy.application import analyze, export_analysis, make_request
from stockstudy.cli import main
from stockstudy.models import DailyBar, Security
from stockstudy.readers.tdx import RECORD, TdxSource
from stockstudy.service import scan
from stockstudy.strategies import Strategy, screen
from stockstudy.windows import StockStudyApp


def sample():
    start = date(2026, 10, 13)
    rows = [DailyBar(start + timedelta(days=i), 1000, 1100, 900, 1000, 10000, 100) for i in range(21)]
    # A bearish latest candle still closes above the previous highs.
    rows[-1] = replace(rows[-1], open=1250, high=1300, close=1200, volume=150)
    return rows


def write_data(root, rows):
    path = root / "sh/lday/sh688001.day"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(RECORD.pack(int(b.date.strftime("%Y%m%d")), b.open, b.high, b.low,
                                         b.close, b.amount, b.volume, 0) for b in rows))
    return path


class BreakoutTests(unittest.TestCase):
    security = Security("sh", "688001")

    def test_windows_exclude_latest_and_bearish_candle_is_allowed(self):
        rows = sample()
        match = screen(self.security, rows, Strategy(name="breakout"))[0]
        self.assertEqual(match.prior_high, 1100)
        self.assertEqual(match.prior_high_date, rows[-2].date)
        self.assertEqual(match.volume_ratio, Decimal("1.5"))
        self.assertEqual(match.average_volume, 100)
        self.assertEqual(match.price_window_start, rows[0].date)
        self.assertEqual(match.price_window_end, rows[-2].date)
        self.assertEqual(match.volume_window_start, rows[-6].date)
        self.assertEqual(match.volume_window_end, rows[-2].date)
        self.assertEqual(match.date, rows[-1].date)

    def test_strict_price_and_inclusive_exact_volume_boundary(self):
        rows = sample()
        strategy = Strategy(name="breakout")
        self.assertEqual(screen(self.security, rows[:-1] + [replace(rows[-1], close=1100)], strategy), [])
        self.assertEqual(screen(self.security, rows[:-1] + [replace(rows[-1], volume=149)], strategy), [])
        self.assertEqual(len(screen(self.security, rows, strategy)), 1)
        precise = [replace(b, volume=1000000) for b in rows]
        precise[-1] = replace(precise[-1], volume=1499999)
        self.assertEqual(screen(self.security, precise, strategy), [])

    def test_high_not_highest_close_and_one_latest_record_only(self):
        rows = sample()
        rows[5] = replace(rows[5], high=1200)
        self.assertEqual(screen(self.security, rows, Strategy(name="breakout")), [])
        rows[-1] = replace(rows[-1], close=1201)
        self.assertEqual(len(screen(self.security, rows, Strategy(name="breakout"))), 1)
        rows += [replace(rows[-1], date=rows[-1].date + timedelta(days=1), close=1400, high=1400, volume=200)]
        self.assertEqual(len(screen(self.security, rows, Strategy(name="breakout"))), 1)
        self.assertEqual(screen(self.security, rows, Strategy(name="breakout"))[0].date, rows[-1].date)

    def test_history_and_independent_window_lengths(self):
        rows = sample()
        self.assertEqual(screen(self.security, rows[-20:], Strategy(name="breakout")), [])
        strategy = Strategy(name="breakout", breakout_period=3, volume_period=7)
        self.assertEqual(strategy.required_bars, 8)
        self.assertEqual(len(screen(self.security, rows[-8:], strategy)), 1)
        self.assertEqual(screen(self.security, rows[-7:], strategy), [])

    def test_zero_mean_negative_volume_and_invalid_prices_are_skipped(self):
        rows = sample()
        for data in ([replace(b, volume=0) for b in rows],
                     rows[:-1] + [replace(rows[-1], volume=-1)],
                     rows[:-1] + [replace(rows[-1], close=0)],
                     [replace(b, high=0) for b in rows[:-1]] + rows[-1:]):
            self.assertEqual(screen(self.security, data, Strategy(name="breakout")), [])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_data(root, [replace(b, volume=0) for b in rows])
            with TdxSource(root) as source:
                result = scan(source, Strategy(name="breakout"))
            self.assertEqual(result.invalid_volume, ["sh688001"])
            self.assertEqual(result.errors, [])

    def test_parameters_are_validated_before_scanning(self):
        for changes in ({"breakout_period": 0}, {"volume_period": 0},
                        {"volume_multiple": Decimal(0)}, {"volume_multiple": Decimal("-1")},
                        {"volume_multiple": Decimal("NaN")}, {"volume_multiple": Decimal("Infinity")}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                Strategy(name="breakout", **changes)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                make_request(temp, "bad", "bad", "", strategy_name="breakout", volume_multiple="NaN")
            request = make_request(temp, "bad", "bad", "", strategy_name="breakout")
            self.assertEqual(request.strategy.name, "breakout")

    def test_cli_and_export_preserve_explanation_and_empty_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            write_data(data, sample())
            with contextlib.redirect_stdout(io.StringIO()):
                status = main(["scan", "--data", str(data), "--strategy", "breakout", "--quiet",
                               "--output-dir", str(root / "exports")])
            self.assertEqual(status, 0)
            run = next((root / "exports").iterdir())
            rows = json.loads((run / "matches.json").read_text(encoding="utf-8"))
            meta = json.loads((run / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(rows[0]["prior_high"], "11.00")
            self.assertEqual(rows[0]["volume"], 150)
            self.assertEqual(rows[0]["volume_ratio"], 1.5)
            self.assertAlmostEqual(rows[0]["breakout_pct"], 100 / 11, places=5)
            self.assertTrue(meta["windows_exclude_latest"])
            self.assertEqual(meta["required_bars"], 21)
            self.assertEqual(meta["volume_unit"], "shares")
            self.assertNotIn("gain_pct", rows[0])
            request = make_request(str(data), "20", "10", "", strategy_name="breakout", volume_multiple="2")
            empty = analyze(request)
            self.assertEqual(empty.rows, [])
            exported = export_analysis(empty, root / "exports")
            with (exported / "matches.csv").open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertIn("prior_high", reader.fieldnames)
                self.assertIn("volume_window_start", reader.fieldnames)
                self.assertEqual(list(reader), [])

    def test_packaged_cli_returns_parameter_error_exit_code(self):
        import runpy
        import subprocess
        import sys
        module = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/build.py"), run_name="build_test")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            with contextlib.redirect_stdout(io.StringIO()):
                module["build_cli"](directory)
            artifact = directory / "cli/淘金人股票分析.pyz"
            result = subprocess.run([sys.executable, "-B", str(artifact), "scan", "--strategy", "breakout",
                                     "--volume-multiple", "NaN", "--quiet"], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b"volume multiple", result.stderr)
            version = subprocess.run([sys.executable, "-B", str(artifact), "--version"], capture_output=True)
            self.assertEqual(version.returncode, 0)



class BreakoutWidgetTests(unittest.TestCase):
    def test_background_scan_language_filters_export_and_strategy_state(self):
        import time
        from unittest.mock import patch
        root = tk.Tk()
        root.withdraw()
        app = StockStudyApp(root)
        try:
            with tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                write_data(directory / "data", sample())
                app.data.set(str(directory / "data"))
                app.strategy_label.set(app.t("breakout"))
                app._strategy_changed()
                self.assertEqual(len(app.strategy_inputs), 3)
                app.start()
                deadline = time.monotonic() + 5
                while app.running and time.monotonic() < deadline:
                    root.update()
                    time.sleep(.01)
                self.assertFalse(app.running)
                self.assertEqual(len(app.table.get_children()), 1)
                self.assertIn("prior_high", app.table["columns"])
                self.assertIn("无效成交量 0", app.detail.get())
                app.volume_multiple.set("2.5")
                app.language.set("en")
                app.switch_language()
                self.assertEqual(app.volume_multiple.get(), "2.5")
                self.assertEqual(len(app.table.get_children()), 1)
                self.assertIn("2.3 Volume Breakout", app.t("help_body"))
                app.result_market.set("bj")
                app._render_rows()
                self.assertEqual(len(app.table.get_children()), 0)
                app.reset_filters()
                with patch("stockstudy.windows.filedialog.askdirectory", return_value=str(directory / "exports")):
                    app.export_results()
                self.assertEqual(app.exported_info[1], 1)
                app.strategy_label.set(app.t("gain")); app._strategy_changed()
                app.strategy_label.set(app.t("breakout")); app._strategy_changed()
                self.assertEqual(app.volume_multiple.get(), "2.5")
                self.assertEqual(app.outcome.summary["volume_multiple"], "1.5")
        finally:
            root.destroy()
