"""Run the standard-library tests from any working directory."""

import sys
import unittest
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
suite = unittest.defaultTestLoader.discover(str(repo / "tests"))
raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
