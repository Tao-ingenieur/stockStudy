import contextlib
import csv
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from stockstudy.cli import main
from stockstudy.names import load_names
from stockstudy.service import scan
from stockstudy.readers.tdx import TdxSource
from stockstudy.strategies import Strategy
from test_tdx import record, gain_records


class ServiceCliTests(unittest.TestCase):
    def test_version_aliases_and_help_show_software_version(self):
        from stockstudy import __version__
        for flag in ("--version", "-version", "-V", "--help"):
            with self.subTest(flag=flag):
                output = io.StringIO()
                with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as stopped:
                    main([flag])
                self.assertEqual(stopped.exception.code, 0)
                self.assertIn(f"StockStudy {__version__}", output.getvalue())

    def make_data(self, root):
        directory = root / "sh" / "lday"
        directory.mkdir(parents=True)
        (directory / "sh688001.day").write_bytes(gain_records())
        return directory

    def test_bad_file_isolated_and_as_of_exclusions_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = self.make_data(root)
            (directory / "sh600000.day").write_bytes(b"broken")
            with TdxSource(root) as source:
                result = scan(source, Strategy(), as_of=date(2026, 10, 29))
            self.assertEqual(result.scanned, 1)
            self.assertEqual(len(result.errors), 2)
            self.assertEqual({e["kind"] for e in result.errors}, {"read_error", "date_mismatch"})
            self.assertEqual(result.matches, [])

    def test_cli_reports_and_runs_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_data(root / "data")
            arguments = ["scan", "--data", str(root / "data"), "--output-dir", str(root / "output"), "--quiet"]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(arguments), 0)
                self.assertEqual(main(arguments), 0)
            runs = list((root / "output").iterdir())
            self.assertEqual(len(runs), 2)
            summary = json.loads((runs[0] / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["matches"], 1)
            self.assertEqual(summary["read_errors"], 0)
            self.assertEqual(summary["missing_name_count"], 0)
            with (runs[0] / "matches.csv").open(encoding="utf-8-sig", newline="") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual((row["code"], row["close"]), ("688001", "14.00"))
            self.assertTrue(row["name"])
            self.assertEqual(float(row["gain_pct"]), 40.0)
            self.assertEqual(row["price_adjustment"], "unadjusted")

    def test_cli_partial_failure_exit_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = self.make_data(root / "data")
            (directory / "sh600000.day").write_bytes(b"x")
            with contextlib.redirect_stdout(io.StringIO()):
                status = main(["scan", "--data", str(root / "data"), "--output-dir", str(root / "output"), "--quiet"])
            self.assertEqual(status, 2)

    def test_short_history_is_reported_and_scan_help_renders(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as stopped:
            main(["scan", "--help"])
        self.assertEqual(stopped.exception.code, 0)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = self.make_data(root / "data")
            (directory / "sh688001.day").write_bytes(record())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "--data", str(root / "data"),
                                      "--output-dir", str(root / "output"), "--quiet"]), 0)
            run = next((root / "output").iterdir())
            summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["insufficient_history_count"], 1)
            self.assertEqual(summary["matches"], 0)
            with (run / "matches.csv").open(encoding="utf-8-sig", newline="") as stream:
                self.assertIn("gain_pct", next(csv.reader(stream)))

    def test_bundled_name_dictionary_keeps_leading_zero(self):
        names = load_names()
        from stockstudy.models import Security
        self.assertEqual(names[Security("sz", "000001")], "平安银行")


if __name__ == "__main__":
    unittest.main()
