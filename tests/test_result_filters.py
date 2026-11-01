import json
import tempfile
import unittest
from pathlib import Path

from stockstudy.application import AnalysisOutcome, export_analysis, filter_results


def row(market, code, status="listed", name="Stock"):
    return dict(market=market, code=code, status=status, name=name, date="2026-10-30", close="14.00",
                base_date="2026-10-10", base_close="10.00", gain_ratio=.4, gain_pct=40,
                price_adjustment="unadjusted")


class ResultFilterTests(unittest.TestCase):
    def setUp(self):
        self.rows = [row("sh", "600000", name="Shanghai"), row("sz", "000001", name="Bank"),
                     row("bj", "920001", "unknown", "Beijing"), row("sh", "600001", "delisted", "Old")]

    def test_markets_and_combined_status_search_preserve_order(self):
        self.assertEqual(filter_results(self.rows, market="bj"), [self.rows[2]])
        self.assertEqual(filter_results(self.rows, market="shsz"), [self.rows[0], self.rows[1], self.rows[3]])
        self.assertEqual(filter_results(self.rows, market="sh", status="delisted", query=" OLD "), [self.rows[3]])
        self.assertEqual(filter_results(self.rows, market="bj", status="listed"), [])
        self.assertEqual(filter_results(self.rows, query="2026-10-30"), self.rows)
        self.assertEqual(filter_results(self.rows, query="SZ000001"), [self.rows[1]])

    def test_missing_status_is_unknown_and_invalid_filters_rejected(self):
        missing = dict(self.rows[0]); missing.pop("status")
        self.assertEqual(filter_results([missing], status="unknown"), [missing])
        for filters in ({"market": "invalid"}, {"status": "invalid"}):
            with self.assertRaises(ValueError):
                filter_results(self.rows, **filters)

    def test_filtered_export_is_not_limited_by_preview_and_keeps_original_summary(self):
        rows = [row("bj", str(920000 + i), "unknown") for i in range(2105)] + self.rows[:2]
        summary = dict(strategy="gain", matches=len(rows), securities_read=5500)
        outcome = AnalysisOutcome(summary, rows)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "exports"
            path = export_analysis(outcome, root, filters=dict(market="bj", status="unknown", query=""))
            exported = json.loads((path / "matches.json").read_text(encoding="utf-8"))
            meta = json.loads((path / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(len(exported), 2105)
            self.assertEqual(meta["matches"], 2107)
            self.assertEqual(meta["export_record_count"], 2105)
            self.assertEqual(meta["export_scope"], "filtered")
            self.assertEqual(meta["result_filters"]["market"], "bj")
        self.assertNotIn("export_scope", summary)
        self.assertEqual(len(outcome.rows), 2107)

    def test_zero_match_and_all_exports_are_explicit(self):
        outcome = AnalysisOutcome(dict(strategy="gain", matches=4), self.rows)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            empty = export_analysis(outcome, root, filters=dict(market="bj", status="listed"))
            self.assertEqual(json.loads((empty / "matches.json").read_text(encoding="utf-8")), [])
            self.assertIn("gain_pct", (empty / "matches.csv").read_text(encoding="utf-8-sig"))
            all_rows = export_analysis(outcome, root)
            meta = json.loads((all_rows / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["export_scope"], "all")
            self.assertEqual(meta["export_record_count"], 4)
            self.assertNotIn("result_filters", meta)
