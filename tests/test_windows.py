import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from stockstudy.application import analyze, make_request
from stockstudy.service import ScanCancelled
from stockstudy.windows import StockStudyApp
from test_tdx import record


class DesktopOperationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.data = self.directory / "sh/lday/sh688001.day"
        self.data.parent.mkdir(parents=True)
        self.data.write_bytes(record(low=1333))

    def tearDown(self):
        self.temp.cleanup()

    def request(self, **changes):
        fields = dict(data=str(self.directory / "sh"), output=str(self.directory / "output"),
                      mode="pattern", lookback="1", threshold="40", references="40,20,10,5", as_of="2026-10-30")
        fields.update(changes)
        return make_request(**fields)

    def test_invalid_parameters_are_reported_before_scanning(self):
        for changes in ({"lookback": "0"}, {"as_of": "wrong-date"},
                        {"mode": "pattern-drop", "threshold": "100"},
                        {"mode": "pattern-drop", "references": "5,0"},
                        {"data": str(self.directory / "missing.zip")}, {"output": ""}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.request(**changes)

    def test_analysis_produces_report_and_rows(self):
        progress = []
        outcome = analyze(self.request(), progress=lambda done, total: progress.append((done, total)))
        self.assertEqual(outcome.summary["matches"], 1)
        self.assertEqual(outcome.rows[0]["low"], "13.33")
        self.assertTrue((outcome.directory / "matches.csv").is_file())
        self.assertEqual(progress, [(1, 1)])

    def test_cancelled_analysis_does_not_create_report(self):
        with self.assertRaises(ScanCancelled):
            analyze(self.request(), cancelled=lambda: True)
        self.assertFalse((self.directory / "output").exists())

    def test_unused_drop_settings_do_not_block_basic_strategy(self):
        self.assertEqual(self.request(threshold="", references="").strategy.name, "pattern")


class DesktopWidgetTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = StockStudyApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_strategy_controls_and_defaults(self):
        self.assertEqual(self.app.lookback.get(), "1")
        self.assertTrue(self.app.threshold_entry.instate(["disabled"]))
        self.app.mode.set("价格形态 + 跌幅")
        self.app._mode_changed()
        self.assertEqual(self.app.lookback.get(), "100")
        self.assertFalse(self.app.threshold_entry.instate(["disabled"]))

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
            data.write_bytes(record(low=1333))
            self.app.data.set(str(directory / "sh"))
            self.app.output.set(str(directory / "output"))
            self.app.start()
            self.assertTrue(self.app.start_button.instate(["disabled"]))
            deadline = time.monotonic() + 5
            while self.app.running and time.monotonic() < deadline:
                self.root.update()
                time.sleep(0.01)
            self.assertFalse(self.app.running)
            self.assertEqual(len(self.app.table.get_children()), 1)
            self.assertFalse(self.app.csv_button.instate(["disabled"]))
            self.app.search.set("not-a-stock")
            self.app._render_rows()
            self.assertEqual(len(self.app.table.get_children()), 0)
