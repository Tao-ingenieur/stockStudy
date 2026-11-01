import contextlib
import csv
import io
import tempfile
import unittest
from datetime import date
from pathlib import Path

from stockstudy.application import analyze, export_analysis, make_request
from stockstudy.cli import main
from stockstudy.limit_prices import load_limit_prices
from stockstudy.models import Security
from stockstudy.readers.tdx import TdxSource
from stockstudy.service import scan
from stockstudy.strategies import Strategy
from test_tdx import record

HEADER = "market,code,date,limit_up_price\n"


class LimitPriceTests(unittest.TestCase):
    def test_csv_parses_exact_cents_and_explicit_unlimited(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "limits.csv"
            path.write_text(HEADER + "sz,000001,2026-10-30,11.03\nbj,920001,2026-10-30,none\n", encoding="utf-8-sig")
            book = load_limit_prices(path)
            self.assertEqual(book.entries[Security("sz", "000001"), date(2026, 10, 30)], 1103)
            self.assertIsNone(book.entries[Security("bj", "920001"), date(2026, 10, 30)])
            self.assertEqual(len(book.sha256), 64)

    def test_invalid_prices_dates_duplicates_and_empty_template_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "limits.csv"
            for value in ("", "0", "-1", "NaN", "Infinity", "11.031"):
                with self.subTest(value=value):
                    path.write_text(HEADER + f"sz,000001,2026-10-30,{value}\n", encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_limit_prices(path)
            for content in (HEADER, HEADER + "sz,1,2026-10-30,11.03\n",
                            HEADER + "sz,000001,bad-date,11.03\n",
                            HEADER + "sz,000001,2026-10-30,11.03\n" * 2):
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_limit_prices(path)

    def test_missing_unlimited_wrong_date_and_inconsistent_prices_are_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root / "sz/lday"
            directory.mkdir(parents=True)
            for code in ("000001", "000002", "000004", "000005", "000006", "000007"):
                (directory / f"sz{code}.day").write_bytes(record(low=1102, high=1103))
            day = date(2026, 10, 30)
            limits = {(Security("sz", "000001"), day): 1103,
                      (Security("sz", "000002"), day): None,
                      (Security("sz", "000004"), day): 1102,
                      (Security("sz", "000006"), date(2026, 10, 29)): 1103,
                      (Security("sz", "000007"), day): 1200}
            with TdxSource(root) as source:
                result = scan(source, Strategy(name="limit-up"), limit_prices=limits)
            self.assertEqual(len(result.matches), 1)
            self.assertEqual(result.matches[0].security.code, "000001")
            self.assertEqual(result.unlimited, ["sz000002"])
            self.assertEqual(result.missing_limits, ["sz000005", "sz000006"])
            self.assertEqual([e["kind"] for e in result.errors], ["limit_data_error"])
            self.assertEqual(result.scanned, 6)

    def test_application_and_cli_use_price_book_and_export_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root / "data/sz/lday"
            directory.mkdir(parents=True)
            (directory / "sz000001.day").write_bytes(record(low=1100, high=1103))
            path = root / "limits.csv"
            path.write_text(HEADER + "sz,000001,2026-10-30,11.03\n", encoding="utf-8")
            request = make_request(str(root / "data"), "unused", "unused", "", strategy_name="limit-up", limit_prices_path=path)
            outcome = analyze(request)
            self.assertEqual(outcome.summary["matches"], 1)
            self.assertEqual(outcome.rows[0]["limit_up_price"], "11.03")
            self.assertEqual(outcome.summary["limit_prices_sha256"], load_limit_prices(path).sha256)
            exported = export_analysis(outcome, root / "exports")
            with (exported / "matches.csv").open(encoding="utf-8-sig", newline="") as stream:
                self.assertIn("limit_up_price", csv.DictReader(stream).fieldnames)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["scan", "--data", str(root / "data"), "--strategy", "limit-up", "--limit-prices", str(path), "--quiet"]), 0)
                self.assertEqual(main(["scan", "--data", str(root / "data"), "--strategy", "limit-up", "--quiet"]), 1)
            path.write_text(HEADER + "sz,000001,2026-10-29,11.03\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "--data", str(root / "data"), "--strategy", "limit-up", "--limit-prices", str(path), "--quiet"]), 2)
            with self.assertRaises(ValueError):
                make_request(str(root / "data"), "", "", "", strategy_name="limit-up")
