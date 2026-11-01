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

    def test_inclusive_threshold_and_no_display_rounding(self):
        strategy = Strategy(period=1)
        self.assertEqual(screen(self.security, bars(1000, 1099), strategy), [])
        self.assertEqual(len(screen(self.security, bars(1000, 1100), strategy)), 1)
        self.assertEqual(screen(self.security, bars(10000, 10999), strategy), [])
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

    def test_latest_crossover_from_equality_and_not_persistent_alignment(self):
        strategy = Strategy(name="ma-cross", trend_filter=False)
        match = screen(self.security, bars(*([1000] * 20 + [1100])), strategy)[0]
        self.assertEqual(match.previous_fast_ma, match.previous_slow_ma)
        self.assertGreater(match.fast_ma, match.slow_ma)
        self.assertIsNone(match.trend_ma)
        self.assertEqual(screen(self.security, bars(*([1000] * 19 + [1100, 1200])), strategy), [])
        self.assertEqual(screen(self.security, bars(*([1000] * 21)), strategy), [])

    def test_trend_filter_is_optional_and_requires_full_history(self):
        data = bars(*([2000] * 99 + [1000] * 20 + [1100]))
        self.assertEqual(screen(self.security, data, Strategy(name="ma-cross")), [])
        self.assertEqual(len(screen(self.security, data, Strategy(name="ma-cross", trend_filter=False))), 1)
        self.assertEqual(Strategy(name="ma-cross").required_bars, 120)
        self.assertEqual(Strategy(name="ma-cross", trend_filter=False).required_bars, 21)
        self.assertEqual(screen(self.security, data[-21:], Strategy(name="ma-cross")), [])
        self.assertEqual(len(screen(self.security, bars(*([1000] * 119 + [1100])), Strategy(name="ma-cross"))), 1)

    def test_trend_equality_is_excluded_without_rounding(self):
        data = [1120] * 98 + [1140] + [1000] * 20 + [1100]
        self.assertEqual(sum(data), 1100 * 120)
        self.assertEqual(screen(self.security, bars(*data), Strategy(name="ma-cross")), [])
        data[-1] = 1101
        self.assertEqual(len(screen(self.security, bars(*data), Strategy(name="ma-cross"))), 1)

    def test_ma_windows_with_zero_close_and_invalid_periods(self):
        data = [1000] * 119 + [1100]
        data[50] = 0
        self.assertEqual(screen(self.security, bars(*data), Strategy(name="ma-cross")), [])
        for kwargs in ({"fast_period": 0}, {"fast_period": 20, "slow_period": 20},
                       {"fast_period": 21}, {"trend_period": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Strategy(name="ma-cross", **kwargs)
        self.assertEqual(Strategy(name="ma-cross", slow_period=150).required_bars, 151)


if __name__ == "__main__":
    unittest.main()
