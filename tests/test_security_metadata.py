import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.update_security_master import merge_entry, read_xlsx
from stockstudy.models import Security, SecurityInfo
from stockstudy.names import load_security_info, default_names
from stockstudy.readers.tdx import TdxSource
from stockstudy.service import scan
from stockstudy.strategies import Strategy
from test_tdx import record


class SecurityMetadataTests(unittest.TestCase):
    def test_frozen_app_prefers_updatable_adjacent_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            external = directory / "security_names.csv"
            external.write_text("market,code,name,is_delisted\nbj,920680,广道退,true\n", encoding="utf-8")
            with patch("sys.frozen", True, create=True), patch("sys.executable", str(directory / "stockstudy.exe")):
                self.assertEqual(default_names(), external)
                self.assertTrue(load_security_info()[Security("bj", "920680")].is_delisted)

    def test_csv_is_tri_state_and_legacy_names_are_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "names.csv"
            path.write_text("market,code,name,is_delisted\nbj,920001,纬达光电,unknown\nsz,000004,国华退,true\nsz,000001,平安银行,false\n", encoding="utf-8")
            info = load_security_info(path)
            self.assertIsNone(info[Security("bj", "920001")].is_delisted)
            self.assertTrue(info[Security("sz", "000004")].is_delisted)
            self.assertFalse(info[Security("sz", "000001")].is_delisted)
            path.write_text("market,code,name\nsz,000001,平安银行\n", encoding="utf-8")
            self.assertIsNone(load_security_info(path)[Security("sz", "000001")].is_delisted)
            path.write_text("market,code,name,is_delisted\nsz,000001,平安银行,maybe\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_security_info(path)

    def test_delisted_filter_is_explicit_unknown_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = {"sz000004": True, "bj920001": None, "sh688001": False}
            info = {}
            for symbol, flag in files.items():
                target = root / symbol[:2] / "lday" / (symbol + ".day")
                target.parent.mkdir(parents=True)
                target.write_bytes(record(low=1333))
                info[Security(symbol[:2], symbol[2:])] = SecurityInfo(symbol, flag)
            with TdxSource(root) as source:
                result = scan(source, Strategy(), security_info=info)
                self.assertEqual(result.delisted_excluded, ["sz000004"])
                self.assertEqual(result.unknown_status, ["bj920001"])
                self.assertEqual(len(result.matches), 2)
                included = scan(source, Strategy(), security_info=info, include_delisted=True)
                self.assertEqual(len(included.matches), 3)
                self.assertEqual(included.delisted_excluded, [])

    def test_future_delisting_and_relisting_use_effective_dates(self):
        rows = {}
        merge_entry(rows, "2026-11-01", "bj", "920680", "待摘牌", "true", "disclosure", delisting="2026-11-05")
        self.assertEqual(rows["bj", "920680"]["is_delisted"], "false")
        merge_entry(rows, "2026-11-06", "bj", "920680", "已摘牌", "true", "disclosure", delisting="2026-11-05")
        self.assertEqual(rows["bj", "920680"]["is_delisted"], "true")
        merge_entry(rows, "2026-11-06", "bj", "920680", "名称不证明上市", "unknown", "names")
        self.assertEqual(rows["bj", "920680"]["is_delisted"], "true")
        merge_entry(rows, "2026-11-06", "sh", "600001", "重新上市名称", "false", "listed", listing="2026-01-01")
        merge_entry(rows, "2026-11-06", "sh", "600001", "历史名称", "true", "old", delisting="2009-12-29")
        self.assertEqual(rows["sh", "600001"]["name"], "重新上市名称")
        self.assertEqual(rows["sh", "600001"]["is_delisted"], "false")

    def test_exchange_xlsx_sparse_cells_and_inline_strings(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("xl/worksheets/sheet1.xml", '''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
            <row r="1"><c r="A1" t="inlineStr"><is><t>code</t></is></c><c r="C1" t="inlineStr"><is><t>name</t></is></c></row>
            <row r="2"><c r="A2" t="inlineStr"><is><t>000001</t></is></c><c r="C2" t="inlineStr"><is><t>平安银行</t></is></c></row>
            </sheetData></worksheet>''')
        self.assertEqual(read_xlsx(data.getvalue()), [{"code": "000001", "name": "平安银行"}])


if __name__ == "__main__":
    unittest.main()
