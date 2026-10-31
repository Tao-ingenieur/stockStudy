import unittest
from datetime import date, timedelta
from decimal import Decimal

from stockstudy.models import DailyBar, Security
from stockstudy.strategies import Strategy, price_pattern, screen


class StrategyTests(unittest.TestCase):
    def test_price_shapes_and_two_decimal_normalization(self):
        for cents in (333, 1333, 888, 1212, 1221, 10000):
            with self.subTest(cents=cents):
                self.assertIsNotNone(price_pattern(cents, broad=False))
        self.assertIsNone(price_pattern(1388, broad=False))
        self.assertIsNotNone(price_pattern(1388, broad=True))
        self.assertIsNone(price_pattern(1234, broad=True))
        self.assertIsNone(price_pattern(0, broad=True))

    def test_reference_zero_index_and_strict_threshold(self):
        start = date(2026, 1, 1)
        bars = [DailyBar(start + timedelta(days=i), 1000, 1000, 1000, 1000, 0, 0) for i in range(6)]
        bars[-1] = DailyBar(bars[-1].date, 555, 555, 555, 555, 0, 0)
        security = Security("sh", "688001")
        strategy = Strategy("pattern-drop", 1, Decimal("0.4"), (5,))
        matches = screen(security, bars, strategy)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].reference_date, start)
        # 40% exactly is excluded; a slightly larger reference high is included.
        bars[0] = DailyBar(start, 925, 925, 925, 925, 0, 0)
        self.assertEqual(screen(security, bars, strategy), [])
        bars[0] = DailyBar(start, 926, 926, 926, 926, 0, 0)
        self.assertEqual(len(screen(security, bars, strategy)), 1)

    def test_reference_is_specific_day_not_window_maximum(self):
        start = date(2026, 1, 1)
        bars = [DailyBar(start + timedelta(days=i), 555, 555, 555, 555, 0, 0) for i in range(7)]
        bars[0] = DailyBar(start, 2000, 2000, 2000, 2000, 0, 0)
        self.assertEqual(screen(Security("sz", "000001"), bars, Strategy("pattern-drop", 1, reference_days=(5,))), [])

    def test_lookback_limits_candidates(self):
        bars = [DailyBar(date(2026, 1, i), 333, 333, 333, 333, 0, 0) for i in range(1, 4)]
        matches = screen(Security("sz", "000001"), bars, Strategy(lookback=2))
        self.assertEqual([m.date.day for m in matches], [3, 2])


if __name__ == "__main__":
    unittest.main()
