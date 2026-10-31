"""Run from source without installing the package."""

import sys
from pathlib import Path

# Expose src as the stockstudy package without an extra source directory level.
__path__ = [str(Path(__file__).resolve().parent / "src")]
if __name__ == "__main__":
    sys.modules["stockstudy"] = sys.modules[__name__]

from stockstudy.version import __version__

from stockstudy.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
