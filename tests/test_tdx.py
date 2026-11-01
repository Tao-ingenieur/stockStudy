import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from stockstudy.models import Security
from stockstudy.readers.tdx import RECORD, TdxSource, parse_records, stock_security


def record(day=20261030, low=1388, high=1400):
    return RECORD.pack(day, high, high, low, high, 123456.0, 12300, 0)


class TdxTests(unittest.TestCase):
    def test_star_market_and_stock_universe(self):
        self.assertEqual(stock_security("sh688001.day"), Security("sh", "688001"))
        self.assertEqual(stock_security("SZ300001.DAY"), Security("sz", "300001"))
        self.assertEqual(stock_security("bj920001.day"), Security("bj", "920001"))
        self.assertEqual(stock_security("bj830799.day"), Security("bj", "830799"))
        for name in ("sh000001.day", "sz399001.day", "bj899050.day", "sh688001.day.bak"):
            self.assertIsNone(stock_security(name))

    def test_record_units_and_validation(self):
        bar = parse_records(record())[0]
        self.assertEqual((bar.date, bar.low, bar.volume), (date(2026, 10, 30), 1388, 12300))
        with self.assertRaises(ValueError):
            parse_records(record() + b"x")
        with self.assertRaises(ValueError):
            parse_records(record(20261301))
        with self.assertRaises(ValueError):
            parse_records(record() + record())

    def test_zip_directory_parity_and_tail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "vipdoc" / "sh" / "lday" / "sh688001.day"
            target.parent.mkdir(parents=True)
            data = record(20261029) + record(20261030, 1389)
            target.write_bytes(data)
            archive_path = root / "bars.zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("sh/lday/sh688001.day", data)
                archive.writestr("sh/lday/sh000001.day", data)
            with TdxSource(root / "vipdoc") as directory, TdxSource(archive_path) as zipped:
                self.assertEqual(directory.securities(), zipped.securities())
                security = directory.securities()[0]
                self.assertEqual(directory.read_bars(security, 1), zipped.read_bars(security, 1))
                self.assertEqual(zipped.read_bars(security, 1)[0].low, 1389)

    def test_duplicate_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "duplicate.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("a/sh/lday/sh688001.day", record())
                archive.writestr("b/sh/lday/sh688001.day", record())
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                TdxSource(archive_path)

    def test_zip_crc_failure_becomes_an_isolated_data_error(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "corrupt.zip"
            original = record()
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_STORED) as archive:
                archive.writestr("sh/lday/sh688001.day", original)
            data = archive_path.read_bytes()
            self.assertEqual(data.count(original), 1)
            archive_path.write_bytes(data.replace(original, b"x" + original[1:]))
            with TdxSource(archive_path) as source:
                with self.assertRaisesRegex(ValueError, "damaged ZIP"):
                    source.read_bars(Security("sh", "688001"), 1)


if __name__ == "__main__":
    unittest.main()
