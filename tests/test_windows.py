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
        self.assertEqual(len(self.app.table["columns"]), 7)

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
                self.app.export_results()
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
