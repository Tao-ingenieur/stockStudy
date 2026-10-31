"""Pure functions shared by CLI and future application frontends."""

from dataclasses import dataclass
from decimal import Decimal

from .models import DailyBar, Match, Security


@dataclass(frozen=True, slots=True)
class Strategy:
    name: str = "pattern"
    lookback: int = 1
    drop_threshold: Decimal = Decimal("0.4")
    reference_days: tuple[int, ...] = (40, 20, 10, 5)

    def __post_init__(self) -> None:
        if self.name not in {"pattern", "pattern-drop"}:
            raise ValueError("Unknown strategy: " + self.name)
        if self.lookback < 1:
            raise ValueError("lookback must be positive")
        if not self.drop_threshold.is_finite() or not 0 <= self.drop_threshold < 1:
            raise ValueError("drop threshold must be between 0 (inclusive) and 1")
        if not self.reference_days or any(n < 1 for n in self.reference_days):
            raise ValueError("reference days must be positive")

    @property
    def required_bars(self) -> int:
        return self.lookback + (max(self.reference_days) if self.name == "pattern-drop" else 0)


def price_pattern(cents: int, *, broad: bool) -> str | None:
    if cents <= 0:
        return None
    whole, fractional = divmod(cents, 100)
    tens, units = divmod(fractional, 10)
    if tens == units and (broad or whole % 10 == units):
        return "decimal-pair" if broad else "triple-digit"
    if 10 <= whole <= 99 and fractional in (whole, (whole % 10) * 10 + whole // 10):
        return "mirror-pair"
    return None


def screen(security: Security, bars: list[DailyBar], strategy: Strategy) -> list[Match]:
    matches = []
    for i in range(len(bars) - 1, max(-1, len(bars) - strategy.lookback - 1), -1):
        bar = bars[i]
        pattern = price_pattern(bar.low, broad=strategy.name == "pattern-drop")
        if pattern is None:
            continue
        if strategy.name == "pattern":
            matches.append(Match(security, bar.date, bar.low, pattern))
            continue
        for offset in strategy.reference_days:
            if i - offset < 0:
                continue
            reference = bars[i - offset]
            if reference.high > 0 and (
                Decimal(reference.high - bar.low) > strategy.drop_threshold * reference.high
            ):
                matches.append(Match(
                    security, bar.date, bar.low, pattern, offset, reference.date, reference.high,
                ))
                break
    return matches
