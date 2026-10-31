from pathlib import Path

from .base import DailyBarSource
from .tdx import TdxSource

SOURCE_FACTORIES = {"tdx": TdxSource}


def open_source(name: str, path: Path) -> DailyBarSource:
    try:
        factory = SOURCE_FACTORIES[name]
    except KeyError:
        raise ValueError(f"Data source is not implemented: {name}") from None
    return factory(path)
