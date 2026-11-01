import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from stockstudy.application import analyze, export_analysis, make_request
from stockstudy.service import ScanCancelled
from stockstudy.windows import StockStudyApp
from test_tdx import record, gain_records


class DesktopOperationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.data = self.directory / "sh/lday/sh688001.day"
        self.data.parent.mkdir(parents=True)
        self.data.write_bytes(gain_records())

    def tearDown(self):
        self.temp.cleanup()

    def request(self, **changes):
        fields = dict(data=str(self.directory / "sh"),
                      period="20", threshold="10", as_of="2026-10-30")
        fields.update(changes)
        return make_request(**fields)

    def test_invalid_parameters_are_reported_before_scanning(self):
        for changes in ({"period": "0"}, {"as_of": "wrong-date"},
                        {"threshold": "NaN"},
                        {"threshold": "-1"},
                        {"data": str(self.directory / "missing.zip")}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.request(**changes)

    def test_analysis_stays_in_memory_until_export(self):
        progress = []
        outcome = analyze(self.request(), progress=lambda done, total: progress.append((done, total)))
        self.assertEqual(outcome.summary["matches"], 1)
        self.assertEqual(outcome.rows[0]["close"], "14.00")
        self.assertFalse((self.directory / "output").exists())
        exported = export_analysis(outcome, self.directory / "output")
        self.assertTrue((exported / "matches.csv").is_file())
        self.assertTrue((exported / "summary.json").is_file())
        again = export_analysis(outcome, self.directory / "output")
        self.assertNotEqual(exported, again)
        self.assertEqual(progress, [(1, 1)])

    def test_cancelled_analysis_does_not_create_report(self):
        with self.assertRaises(ScanCancelled):
            analyze(self.request(), cancelled=lambda: True)
        self.assertFalse((self.directory / "output").exists())

class DesktopWidgetTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = StockStudyApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_strategy_controls_and_defaults(self):
        self.assertEqual(self.app.period.get(), "20")
        self.assertEqual(self.app.threshold.get(), "10")
        self.assertFalse(self.app.threshold_entry.instate(["disabled"]))
        self.assertEqual(len(self.app.table["columns"]), 8)

    def test_invalid_input_shows_dialog_without_starting_worker(self):
        self.app.data.set("Z:/stockstudy-nonexistent-test.zip")
        with patch("stockstudy.windows.messagebox.showerror") as error:
            self.app.start()
        error.assert_called_once()
        self.assertFalse(self.app.running)

    def test_real_background_scan_populates_searchable_table(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            data = directory / "sh/lday/sh688001.day"
            data.parent.mkdir(parents=True)
            data.write_bytes(gain_records())
            self.app.data.set(str(directory / "sh"))
            self.app.start()
            self.assertTrue(self.app.start_button.instate(["disabled"]))
            deadline = time.monotonic() + 5
            while self.app.running and time.monotonic() < deadline:
                self.root.update()
                time.sleep(0.01)
            self.assertFalse(self.app.running)
            self.assertEqual(len(self.app.table.get_children()), 1)
            self.assertFalse(self.app.export_button.instate(["disabled"]))
            self.assertFalse((directory / "output").exists())
            original = self.app.outcome
            self.app.language.set("en")
            self.app.switch_language()
            self.assertEqual(self.app.settings_frame.cget("text"), "Analysis Settings")
            self.assertIs(self.app.outcome, original)
            self.assertIn("no adjustment factors", self.app.detail.get())
            self.assertEqual(len(self.app.table.get_children()), 1)
            self.app.search.set("not-a-stock")
            self.app._render_rows()
            self.assertEqual(len(self.app.table.get_children()), 0)

    def test_export_cancel_and_export_full_result_after_search(self):
        from stockstudy.application import AnalysisOutcome
        row = {"market": "sz", "code": "000001", "name": "Bank", "status": "listed", "date": "2026-10-30",
               "close": "14.00", "base_date": "2026-10-10", "base_close": "10.00", "gain_ratio": .4,
               "gain_pct": 40, "price_adjustment": "unadjusted"}
        self.app.outcome = AnalysisOutcome({}, [row])
        # Cancelling the picker does not call the exporter.
        with patch("stockstudy.windows.filedialog.askdirectory", return_value=""), patch("stockstudy.windows.export_analysis") as export:
            self.app.export_results()
            export.assert_not_called()
        self.app.search.set("not-a-stock")
        with tempfile.TemporaryDirectory() as temp:
            with patch("stockstudy.windows.filedialog.askdirectory", return_value=temp), patch.object(self.app, "_refresh_text"):
                self.app.export_results(all_results=True)
            import json
            rows = json.loads((self.app.exported_path / "matches.json").read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 1)

    def test_switch_language_keeps_parameters_and_menu_labels(self):
        self.app.period.set("5")
        self.app.threshold.set("3")
        self.app.language.set("en")
        self.app.switch_language()
        self.assertEqual(self.app.period.get(), "5")
        self.assertEqual(self.app.threshold.get(), "3")
        self.assertEqual(self.app.strategy_frame.cget("text"), "Analysis Strategy")
        self.assertEqual(self.app.menubar.entrycget(1, "label"), "File")
        self.assertIn("Stock Analysis", self.root.title())
        self.app.language.set("zh")
        self.app.switch_language()
        self.assertEqual(self.app.results_frame.cget("text"), "分析结果")

    def test_ma_strategy_switch_and_language_preserve_parameters(self):
        self.app.strategy_label.set(self.app.t("ma-cross"))
        self.app._strategy_changed()
        self.assertEqual(self.app.strategy_id, "ma-cross")
        self.assertEqual(len(self.app.table["columns"]), 10)
        self.assertTrue(self.app.trend_filter.get())
        self.app.trend_filter.set(False)
        self.app._trend_changed()
        self.assertTrue(self.app.trend_entry.instate(["disabled"]))
        self.app.fast_period.set("10")
        self.app.language.set("en")
        self.app.switch_language()
        self.assertEqual(self.app.fast_period.get(), "10")
        self.assertFalse(self.app.trend_filter.get())
        self.assertTrue(self.app.trend_entry.instate(["disabled"]))
        self.assertEqual(self.app.strategy_label.get(), "MA Crossover")

    def test_real_ma_analysis_shows_ma_columns_and_exports(self):
        from datetime import date, timedelta
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            data = directory / "sh/lday/sh688001.day"
            data.parent.mkdir(parents=True)
            start = date(2026, 10, 30) - timedelta(days=119)
            data.write_bytes(b"".join(record(int((start + timedelta(days=i)).strftime("%Y%m%d")),
                                            low=1100 if i == 119 else 1000,
                                            high=1100 if i == 119 else 1000) for i in range(120)))
            request = make_request(str(directory / "sh"), "unused", "unused", "2026-10-30", strategy_name="ma-cross")
            outcome = analyze(request)
            self.assertEqual(outcome.summary["matches"], 1)
            self.assertEqual(outcome.summary["required_bars"], 120)
            self.app.outcome = outcome
            self.app._refresh_text()
            self.app._render_rows()
            self.assertIn("trend_ma", self.app.table["columns"])
            self.assertIn("MA120", self.app.detail.get())
            exported = export_analysis(outcome, directory / "exports")
            import csv
            with (exported / "matches.csv").open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertIn("previous_fast_ma", rows[0])
            self.assertNotIn("gain_pct", rows[0])
            self.app.strategy_label.set(self.app.t("ma-cross"))
            self.app._strategy_changed()
            self.app.strategy_label.set(self.app.t("gain"))
            self.app._strategy_changed()
            self.assertIn("trend_ma", self.app.table["columns"])
            self.assertIs(self.app.outcome, outcome)

    def test_result_filter_controls_combine_and_reset_without_rescan(self):
        from stockstudy.application import AnalysisOutcome
        from test_result_filters import row
        rows = [row("sh", "600000"), row("sz", "000001"), row("bj", "920001", "unknown")]
        self.app.outcome = AnalysisOutcome({}, rows)
        self.app.market_label.set(self.app.t("market_bj"))
        self.app.status_label.set(self.app.t("status_unknown"))
        with patch("stockstudy.windows.analyze") as analyze:
            self.app._filters_changed()
            self.assertEqual(len(self.app.table.get_children()), 1)
            self.assertEqual(self.app._filtered_rows(), [rows[2]])
            self.app.search.set("no-match")
            self.app._render_rows()
            self.assertEqual(len(self.app.table.get_children()), 0)
            self.app.reset_filters()
            self.assertEqual(len(self.app.table.get_children()), 3)
            analyze.assert_not_called()
        self.assertEqual(len(self.app.outcome.rows), 3)

    def test_filters_survive_language_switch_and_filtered_export(self):
        from stockstudy.application import AnalysisOutcome
        from test_result_filters import row
        rows = [row("sh", "600000"), row("sz", "000001"), row("bj", "920001", "unknown")]
        self.app.outcome = AnalysisOutcome({}, rows)
        self.app.result_market.set("bj")
        self.app.result_status.set("unknown")
        self.app.search.set("920001")
        self.app.language.set("en")
        with patch.object(self.app, "_refresh_text"):
            self.app.switch_language()
        self.assertEqual(self.app.market_label.get(), "Beijing (bj)")
        self.assertEqual(self.app.status_label.get(), "Unknown")
        self.assertEqual(len(self.app.table.get_children()), 1)
        with tempfile.TemporaryDirectory() as temp:
            with patch("stockstudy.windows.filedialog.askdirectory", return_value=temp), patch.object(self.app, "_refresh_text"):
                self.app.export_results()
            import json
            exported = json.loads((self.app.exported_path / "matches.json").read_text(encoding="utf-8"))
            self.assertEqual(exported, [rows[2]])
            self.assertEqual(self.app.exported_info, ("filtered", 1))
