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
    base_date: date
    base_close: int
    gain_ratio: Decimal


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
