from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Security:
    market: str
    code: str

    @property
    def symbol(self) -> str:
        return self.market + self.code


@dataclass(frozen=True, slots=True)
class DailyBar:
    """Prices are integer cents; volume is shares; amount is yuan."""

    date: date
    open: int
    high: int
    low: int
    close: int
    amount: float
    volume: int


@dataclass(frozen=True, slots=True)
class SecurityInfo:
    name: str
    status: str = "unknown"
    name_checked_at: date | None = None


@dataclass(frozen=True, slots=True)
class Match:
    security: Security
    date: date
    close: int
    base_date: date | None = None
    base_close: int | None = None
    gain_ratio: Decimal | None = None
    previous_date: date | None = None
    fast_ma: Decimal | None = None
    slow_ma: Decimal | None = None
    previous_fast_ma: Decimal | None = None
    previous_slow_ma: Decimal | None = None
    trend_ma: Decimal | None = None
    limit_up_price: int | None = None


@dataclass(slots=True)
class ScanResult:
    matches: list[Match] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    scanned: int = 0
    empty: int = 0
    insufficient_history: list[str] = field(default_factory=list)
    invalid_close: list[str] = field(default_factory=list)
    dates: dict[Security, date] = field(default_factory=dict)
    delisted_excluded: list[str] = field(default_factory=list)
    unknown_status: list[str] = field(default_factory=list)
    missing_limits: list[str] = field(default_factory=list)
    unlimited: list[str] = field(default_factory=list)
