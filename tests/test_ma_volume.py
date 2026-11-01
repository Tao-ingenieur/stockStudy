import contextlib
import csv
import io
import json
import tempfile
import tkinter as tk
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from stockstudy.application import analyze, export_analysis, make_request
from stockstudy.cli import main
from stockstudy.models import Security
from stockstudy.readers.tdx import TdxSource
from stockstudy.service import scan
from stockstudy.strategies import Strategy, screen
from stockstudy.windows import StockStudyApp
from test_breakout import sample, write_data


def data():
    rows = [replace(b, open=1000, high=1000, low=1000, close=1000, volume=100) for b in sample()]
    rows[-1] = replace(rows[-1], high=1100, close=1100, volume=150)
    return rows


def strategy(**changes):
    values = dict(name="ma-cross", trend_filter=False, volume_filter=True)
    values.update(changes)
    return Strategy(**values)


class MAVolumeTests(unittest.TestCase):
    security = Security("sh", "688001")

    def test_disabled_keeps_original_crossover_without_volume(self):
        rows = [replace(b, volume=0) for b in data()]
        result = screen(self.security, rows, strategy(volume_filter=False))[0]
        self.assertIsNone(result.volume)
        self.assertIsNone(result.volume_ratio)
        self.assertEqual(Strategy(name="ma-cross").required_bars, 120)
        self.assertFalse(Strategy(name="ma-cross").volume_filter)
        self.assertEqual(screen(self.security, rows, strategy()), [])

    def test_exact_multiple_prior_window_and_unrounded_comparison(self):
        rows = data()
        match = screen(self.security, rows, strategy())[0]
        self.assertEqual(match.average_volume, 100)
        self.assertEqual(match.volume_ratio, Decimal("1.5"))
        self.assertEqual(match.volume_window_end, rows[-2].date)
        self.assertEqual(match.volume_window_start, rows[-6].date)
        self.assertEqual(screen(self.security, rows[:-1] + [replace(rows[-1], volume=149)], strategy()), [])
        precise = [replace(b, volume=1000000) for b in rows]
        precise[-1] = replace(precise[-1], volume=1499999)
        self.assertEqual(screen(self.security, precise, strategy()), [])
        # Volume is only a confirmation; no crossover still means no result.
        no_cross = [replace(b, close=1000) for b in rows]
        self.assertEqual(screen(self.security, no_cross, strategy()), [])

    def test_volume_and_trend_filters_are_independent(self):
        rows = data()
        self.assertEqual(len(screen(self.security, rows, strategy())), 1)
        self.assertEqual(screen(self.security, rows, strategy(trend_filter=True)), [])
        self.assertEqual(strategy(volume_period=30).required_bars, 31)
        self.assertEqual(strategy(volume_filter=False, volume_period=300).required_bars, 21)
        self.assertEqual(screen(self.security, rows, strategy(volume_period=30)), [])
        # Extra volume history must not expand the price validation window.
        extended = [replace(rows[0], date=rows[0].date.replace(day=1), open=0, low=0, high=0, close=0)] + rows
        self.assertEqual(len(screen(self.security, extended, strategy(volume_period=21))), 1)

    def test_parameter_errors_and_zero_mean_are_reported(self):
        for changes in ({"volume_period": 0}, {"volume_multiple": Decimal(0)},
                        {"volume_multiple": Decimal("NaN")}, {"volume_multiple": Decimal("Infinity")}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                strategy(**changes)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_data(root, [replace(b, volume=0) for b in data()])
            with TdxSource(root) as source:
                result = scan(source, strategy())
            self.assertEqual(result.invalid_volume, ["sh688001"])
            with TdxSource(root) as source:
                result = scan(source, strategy(volume_filter=False))
            self.assertEqual(len(result.matches), 1)
            self.assertEqual(result.invalid_volume, [])
            request = make_request(str(root), "20", "10", "", strategy_name="ma-cross",
                                   trend_filter=False, volume_filter=False, volume_period="bad", volume_multiple="NaN")
            self.assertFalse(request.strategy.volume_filter)

    def test_export_records_enabled_state_and_disabled_values_are_blank(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_data(root / "data", data())
            for enabled in (True, False):
                request = make_request(str(root / "data"), "20", "10", "", strategy_name="ma-cross",
                                       trend_filter=False, volume_filter=enabled)
                outcome = analyze(request)
                self.assertEqual(outcome.summary["volume_filter"], enabled)
                self.assertEqual(outcome.rows[0]["volume_filter"], enabled)
                self.assertEqual(outcome.rows[0]["volume_ratio"], 1.5 if enabled else None)
                self.assertEqual(outcome.summary["volume_period"], 5 if enabled else None)
                exported = export_analysis(outcome, root / "exports")
                self.assertTrue(exported.name.startswith("淘金人股票分析_"))
                with (exported / "matches.csv").open(encoding="utf-8-sig", newline="") as stream:
                    row = next(csv.DictReader(stream))
                self.assertEqual(row["volume"], "150" if enabled else "")
                self.assertEqual(row["volume_window_end"], data()[-2].date.isoformat() if enabled else "")

    def test_cli_volume_filter_is_explicit_and_threshold_is_used(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_data(root / "data", data())
            for flags, count in (([], 1), (["--volume-filter"], 1),
                                 (["--volume-filter", "--volume-multiple", "2"], 0)):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = main(["scan", "--data", str(root / "data"), "--strategy", "ma-cross",
                                 "--no-trend-filter", "--quiet", *flags])
                self.assertEqual(code, 0)
                self.assertIn(f"matches {count}", output.getvalue())
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["scan", "--data", str(root / "data"), "--strategy", "ma-cross",
                                       "--volume-filter", "--volume-multiple", "NaN"]), 1)

    def test_gui_independent_parameters_toggle_and_result_language(self):
        root = tk.Tk()
        root.withdraw()
        app = StockStudyApp(root)
        try:
            self.assertIn("淘金人股票分析", root.title())
            app.strategy_label.set(app.t("ma-cross")); app._strategy_changed()
            self.assertFalse(app.ma_volume_filter.get())
            self.assertTrue(all(e.instate(["disabled"]) for e in app.ma_volume_entries))
            app.ma_volume_filter.set(True); app._ma_volume_changed()
            self.assertFalse(any(e.instate(["disabled"]) for e in app.ma_volume_entries))
            app.ma_volume_period.set("7"); app.ma_volume_multiple.set("2")
            app.volume_period.set("3"); app.volume_multiple.set("4")
            with tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                write_data(directory, data())
                request = make_request(str(directory), "20", "10", "", strategy_name="ma-cross",
                                       trend_filter=False, volume_filter=True)
                app.outcome = analyze(request)
                app._refresh_text(); app._render_rows()
                self.assertIn("volume_ratio", app.table["columns"])
                self.assertIn("前5条均量 × 1.5", app.detail.get())
                app.language.set("en"); app.switch_language()
                self.assertIn("Taojinren", root.title())
                self.assertIn("volume_ratio", app.table["columns"])
                self.assertIn("independent of MA120", app.t("help_body"))
                self.assertEqual(app.ma_volume_period.get(), "7")
                app.strategy_label.set(app.t("breakout")); app._strategy_changed()
                self.assertEqual(app.volume_period.get(), "3")
                app.strategy_label.set(app.t("ma-cross")); app._strategy_changed()
                self.assertEqual(app.ma_volume_multiple.get(), "2")
                app.outcome = analyze(make_request(str(directory), "20", "10", "", strategy_name="ma-cross", trend_filter=False))
                app._refresh_text(); app._render_rows()
                self.assertNotIn("volume_ratio", app.table["columns"])
                self.assertIn("not tested", app.detail.get())
        finally:
            root.destroy()
