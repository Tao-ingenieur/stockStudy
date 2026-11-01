"""Pure daily-bar screening rules; no display rounding in signal comparisons."""

from dataclasses import dataclass
from decimal import Decimal

from .models import DailyBar, Match, Security


@dataclass(frozen=True, slots=True)
class Strategy:
    name: str = "gain"
    period: int = 20
    gain_threshold: Decimal = Decimal("0.10")

    fast_period: int = 5
    slow_period: int = 20
    trend_filter: bool = True
    trend_period: int = 120

    def __post_init__(self) -> None:
        if self.name not in {"gain", "ma-cross"}:
            raise ValueError("Unknown strategy: " + self.name)
        if self.name == "ma-cross":
            if not 1 <= self.fast_period < self.slow_period:
                raise ValueError("MA periods must satisfy 1 <= fast < slow")
            if self.trend_filter and self.trend_period < 1:
                raise ValueError("trend period must be positive")
            return
        if self.period < 1:
            raise ValueError("period must be positive")
        if not self.gain_threshold.is_finite() or self.gain_threshold < 0:
            raise ValueError("gain threshold must be finite and nonnegative")

    @property
    def required_bars(self) -> int:
        if self.name == "ma-cross":
            return max(self.slow_period + 1, self.trend_period if self.trend_filter else 0)
        return self.period + 1


def screen(security: Security, bars: list[DailyBar], strategy: Strategy) -> list[Match]:
    if len(bars) < strategy.required_bars:
        return []
    if not valid_closes(bars, strategy):
        return []
    if strategy.name == "ma-cross":
        return screen_ma_cross(security, bars, strategy)
    latest, base = bars[-1], bars[-strategy.required_bars]
    if latest.close <= 0 or base.close <= 0:
        return []
    # Compare integer-cent changes before rounding the displayed percentage.
    if Decimal(latest.close - base.close) >= strategy.gain_threshold * base.close:
        return [Match(security, latest.date, latest.close, base.date, base.close,
                      Decimal(latest.close - base.close) / base.close)]
    return []


def valid_closes(bars: list[DailyBar], strategy: Strategy) -> bool:
    if strategy.name == "ma-cross":
        return all(bar.close > 0 for bar in bars[-strategy.required_bars:])
    return bars[-1].close > 0 and bars[-strategy.required_bars].close > 0


def screen_ma_cross(security: Security, bars: list[DailyBar], strategy: Strategy) -> list[Match]:
    fast, slow = strategy.fast_period, strategy.slow_period
    current_fast = sum(bar.close for bar in bars[-fast:])
    current_slow = sum(bar.close for bar in bars[-slow:])
    previous_fast = sum(bar.close for bar in bars[-fast - 1:-1])
    previous_slow = sum(bar.close for bar in bars[-slow - 1:-1])
    # Cross multiplication avoids rounding of rational SMA values at equality.
    if not (previous_fast * slow <= previous_slow * fast and current_fast * slow > current_slow * fast):
        return []
    trend_sum = sum(bar.close for bar in bars[-strategy.trend_period:]) if strategy.trend_filter else None
    if trend_sum is not None and bars[-1].close * strategy.trend_period <= trend_sum:
        return []
    return [Match(security, bars[-1].date, bars[-1].close, previous_date=bars[-2].date,
                  fast_ma=Decimal(current_fast) / fast, slow_ma=Decimal(current_slow) / slow,
                  previous_fast_ma=Decimal(previous_fast) / fast, previous_slow_ma=Decimal(previous_slow) / slow,
                  trend_ma=Decimal(trend_sum) / strategy.trend_period if trend_sum is not None else None)]
