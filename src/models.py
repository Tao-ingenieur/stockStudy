from dataclasses import dataclass, field
from datetime import date


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
    is_delisted: bool | None = None
    listing_date: date | None = None
    delisting_date: date | None = None
    status_source: str = ""
    status_checked_at: date | None = None


@dataclass(frozen=True, slots=True)
class Match:
    security: Security
    date: date
    low: int
    pattern: str
    reference_days: int | None = None
    reference_date: date | None = None
    reference_high: int | None = None


@dataclass(slots=True)
class ScanResult:
    matches: list[Match] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    scanned: int = 0
    empty: int = 0
    dates: dict[Security, date] = field(default_factory=dict)
    delisted_excluded: list[str] = field(default_factory=list)
    unknown_status: list[str] = field(default_factory=list)
