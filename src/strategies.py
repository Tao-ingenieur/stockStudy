"""Close-to-close interval return screening."""

from dataclasses import dataclass
from decimal import Decimal

from .models import DailyBar, Match, Security


@dataclass(frozen=True, slots=True)
class Strategy:
    name: str = "gain"
    period: int = 20
    gain_threshold: Decimal = Decimal("0.10")

    def __post_init__(self) -> None:
        if self.name != "gain":
            raise ValueError("Unknown strategy: " + self.name)
        if self.period < 1:
            raise ValueError("period must be positive")
        if not self.gain_threshold.is_finite() or self.gain_threshold < 0:
            raise ValueError("gain threshold must be finite and nonnegative")

    @property
    def required_bars(self) -> int:
        return self.period + 1


def screen(security: Security, bars: list[DailyBar], strategy: Strategy) -> list[Match]:
    if len(bars) < strategy.required_bars:
        return []
    latest, base = bars[-1], bars[-strategy.required_bars]
    if latest.close <= 0 or base.close <= 0:
        return []
    # Compare integer-cent changes before rounding the displayed percentage.
    if Decimal(latest.close - base.close) > strategy.gain_threshold * base.close:
        return [Match(security, latest.date, latest.close, base.date, base.close,
                      Decimal(latest.close - base.close) / base.close)]
    return []
