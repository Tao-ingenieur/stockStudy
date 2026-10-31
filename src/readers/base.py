from typing import Protocol

from ..models import DailyBar, Security


class DailyBarSource(Protocol):
    """Adapters return chronological, unadjusted bars using the common units."""

    def securities(self) -> list[Security]: ...

    def read_bars(self, security: Security, limit: int) -> list[DailyBar]: ...

    def close(self) -> None: ...
