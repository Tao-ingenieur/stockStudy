import unittest
from datetime import date, timedelta
from decimal import Decimal

from stockstudy.models import DailyBar, Security
from stockstudy.strategies import Strategy, screen


def bars(*closes):
    return [DailyBar(date(2026, 1, 1) + timedelta(days=i), p, p, p, p, 0, 0)
            for i, p in enumerate(closes)]


class StrategyTests(unittest.TestCase):
    security = Security("sz", "000001")

    def test_strict_threshold_and_no_display_rounding(self):
        strategy = Strategy(period=1)
        self.assertEqual(screen(self.security, bars(1000, 1100), strategy), [])
        match = screen(self.security, bars(1000, 1101), strategy)[0]
        self.assertEqual(match.gain_ratio, Decimal("0.101"))
        self.assertEqual((match.base_close, match.close), (1000, 1101))
        self.assertEqual(screen(self.security, bars(1000, 900), strategy), [])

    def test_period_uses_exact_base_close_and_one_latest_result(self):
        data = bars(1000, 3000, 1100, 1400)
        match = screen(self.security, data, Strategy(period=3))[0]
        self.assertEqual(match.base_date, data[0].date)
        self.assertEqual(match.date, data[-1].date)
        self.assertEqual(match.gain_ratio, Decimal("0.4"))
        self.assertEqual(len(screen(self.security, data, Strategy(period=1))), 1)
        self.assertEqual(screen(self.security, data, Strategy(period=4)), [])

    def test_nonpositive_closes_and_insufficient_history(self):
        for data in ([], bars(1000), bars(0, 1400), bars(1000, 0)):
            self.assertEqual(screen(self.security, data, Strategy(period=1)), [])

    def test_threshold_can_exceed_one_hundred_percent(self):
        self.assertEqual(len(screen(self.security, bars(1000, 2600),
                                   Strategy(period=1, gain_threshold=Decimal("1.5")))), 1)
        for kwargs in ({"period": 0}, {"gain_threshold": Decimal("NaN")},
                       {"gain_threshold": Decimal("Infinity")}, {"gain_threshold": Decimal("-0.1")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Strategy(**kwargs)


if __name__ == "__main__":
    unittest.main()
