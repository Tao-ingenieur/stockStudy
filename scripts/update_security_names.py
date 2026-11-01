"""Refresh the security CSV from exchange lists and attributed disclosures.

Runtime scanning stays offline. Raw downloads are cached outside the repository.
Beijing's CNINFO name list is not an active-listing certificate: its status is unknown
unless supplied by a verified listing export or an explicit delisting disclosure.
"""

import argparse
import csv
import hashlib
import html
import io
import json
import re
import sys
import shutil
import urllib.parse
import urllib.request
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from stockstudy.readers.tdx import stock_security

FIELDS = ["market", "code", "name", "status", "name_checked_at"]
DETAIL_FIELDS = FIELDS + ["listing_date", "delisting_date", "status_source", "status_checked_at", "name_source"]
SH_PARAMS = {"sqlId": "COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L", "isPagination": "true",
             "pageHelp.pageSize": "10000", "pageHelp.pageNo": "1", "type": "inParams", "STOCK_TYPE": "1,8"}
DOWNLOADS = {
    "sse_listed.json": ["https://query.sse.com.cn/sseQuery/commonQuery.do?" + urllib.parse.urlencode(dict(SH_PARAMS, COMPANY_STATUS="2,4,5,7,8"))],
    "sse_delisted.json": ["https://query.sse.com.cn/sseQuery/commonQuery.do?" + urllib.parse.urlencode(dict(SH_PARAMS, COMPANY_STATUS="3"))],
    "szse_listed.xlsx": [f"https://{host}/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1110&TABKEY=tab1" for host in ("www.szse.cn", "www.sse.org.cn")],
    "szse_delisted.xlsx": [f"https://{host}/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1793_ssgs&TABKEY=tab2" for host in ("www.szse.cn", "www.sse.org.cn")],
    "cninfo_bj.json": ["https://www.cninfo.com.cn/new/data/bj_stock.json"],
}
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def clean(value):
    return html.unescape(re.sub(r"<[^>]+>", "", str(value or ""))).strip()


def normalize_date(value):
    value = clean(value)
    if value in {"", "-", "--"}:
        return ""
    if re.fullmatch(r"\d{8}", value):
        value = value[:4] + "-" + value[4:6] + "-" + value[6:]
    return date.fromisoformat(value.replace("/", "-")).isoformat()


def read_xlsx(data):
    """Read the string/date fields in the exchange's first worksheet without pandas."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.findall(".//x:t", NS)) for si in root.findall("x:si", NS)]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        matrix = []
        for row in sheet.findall(".//x:row", NS):
            values = {}
            for cell in row.findall("x:c", NS):
                column = re.match(r"[A-Z]+", cell.get("r", ""))[0]
                value = cell.find("x:v", NS)
                text = value.text if value is not None else ""
                if cell.get("t") == "s":
                    text = shared[int(text)]
                elif cell.get("t") == "inlineStr":
                    text = "".join(t.text or "" for t in cell.findall(".//x:t", NS))
                values[column] = clean(text)
            matrix.append(values)
    if not matrix:
        raise ValueError("Exchange XLSX is empty")
    header = matrix[0]
    return [{name: row.get(column, "") for column, name in header.items()} for row in matrix[1:]]


def merge_entry(rows, checked_at, market, code, name, status, source, listing="", delisting=""):
    code = clean(code).zfill(6)
    if stock_security(market + code + ".day") is None:
        return
    listing, delisting = normalize_date(listing), normalize_date(delisting)
    key = market, code
    row = rows.setdefault(key, {field: "" for field in DETAIL_FIELDS})
    if status == "delisted" and not delisting:
        raise ValueError(f"Missing effective delisting date for {market}{code}")
    if status == "delisted" and row.get("status") == "listed" and row.get("listing_date", "") > delisting:
        return
    row.update(market=market, code=code, name=clean(name), name_source=source, name_checked_at=checked_at)
    if status == "unknown":
        row["status"] = row.get("status") or "unknown"
        return
    effective_status = "listed" if status == "delisted" and delisting > checked_at else status
    if listing > checked_at:
        effective_status = "unknown"
    row.update(status=effective_status, listing_date=listing or row.get("listing_date", ""),
               delisting_date=delisting, status_source=source, status_checked_at=checked_at)


def download(cache, filename):
    errors = []
    for url in DOWNLOADS[filename]:
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.sse.com.cn/"})
            with opener.open(request, timeout=20) as response:
                data = response.read()
            if filename.endswith(".xlsx"):
                read_xlsx(data)
            else:
                json.loads(data.decode("utf-8-sig"))
            (cache / filename).write_bytes(data)
            (cache / (filename + ".source.json")).write_text(json.dumps({"url": url, "retrieved_at": date.today().isoformat()}), encoding="utf-8")
            return filename, len(data)
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError("\n".join(errors))


def build_master(existing, cache, checked_at, overrides, bse_listed=None):
    rows = {}
    for original in existing:
        key = original["market"], original["code"]
        rows[key] = {field: original.get(field, "") for field in DETAIL_FIELDS}
        rows[key]["status"] = original.get("status") or "unknown"
        rows[key]["name_source"] = original.get("name_source") or "project_reference"
        if rows[key]["status"] != "delisted":
            rows[key].update(status="unknown", status_source="", status_checked_at="")

    def apply(market, code, name, status, source, listing="", delisting=""):
        merge_entry(rows, checked_at, market, code, name, status, source, listing, delisting)

    for filename, status in (("sse_listed.json", "listed"), ("sse_delisted.json", "delisted")):
        payload = json.loads((cache / filename).read_text(encoding="utf-8-sig"))
        records = payload["result"]
        if len(records) < (1000 if status == "listed" else 50):
            raise ValueError(f"Unexpectedly small exchange list: {filename}")
        if len(records) != int(payload["pageHelp"]["total"]):
            raise ValueError(f"Incomplete exchange pagination: {filename}")
        for item in records:
            name = item.get("SEC_NAME_CN")
            if not name or name == "-":
                name = item["COMPANY_ABBR"]
            apply("sh", item["A_STOCK_CODE"], name, status, DOWNLOADS[filename][0], item["LIST_DATE"], item["DELIST_DATE"] if status == "delisted" else "")

    for filename, status in (("szse_listed.xlsx", "listed"), ("szse_delisted.xlsx", "delisted")):
        records = read_xlsx((cache / filename).read_bytes())
        if len(records) < (1000 if status == "listed" else 50):
            raise ValueError(f"Unexpectedly small exchange list: {filename}")
        for item in records:
            if status == "listed":
                apply("sz", item["A股代码"], item["A股简称"], status, DOWNLOADS[filename][0], item["A股上市日期"])
            else:
                apply("sz", item["证券代码"], item["证券简称"], status, DOWNLOADS[filename][0], item["上市日期"], item["终止上市日期"])

    for item in json.loads((cache / "cninfo_bj.json").read_text(encoding="utf-8-sig"))["stockList"]:
        if item.get("category") == "A股":
            apply("bj", item["code"], item["zwjc"], "unknown", DOWNLOADS["cninfo_bj.json"][0])
    if bse_listed:
        for item in bse_listed:
            apply("bj", item["code"], item["name"], "listed", "https://www.bse.cn/nq/listedcompany.html", item.get("listing_date", ""))
    for item in overrides:
        apply(item["market"], item["code"], item["name"], "delisted", item["source"], delisting=item["delisting_date"])
    return [rows[key] for key in sorted(rows)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=REPO.parent / "output/security_metadata" / date.today().isoformat())
    parser.add_argument("--offline", action="store_true", help="Use the five cached exchange/name files without networking")
    parser.add_argument("--checked-at", type=date.fromisoformat, default=date.today())
    parser.add_argument("--bse-listed", type=Path, help="Optional verified BSE listing export: code,name,listing_date")
    args = parser.parse_args()
    cache = args.cache_dir.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    if not args.offline:
        with ThreadPoolExecutor(max_workers=5) as pool:
            tasks = [pool.submit(download, cache, name) for name in DOWNLOADS]
            for task in as_completed(tasks):
                print("Downloaded", *task.result(), flush=True)
    target = REPO / "resources/security_names.csv"
    existing = []
    if target.exists():
        with target.open(encoding="utf-8-sig", newline="") as stream:
            existing = list(csv.DictReader(stream))
    metadata_path = REPO / "resources/security_metadata.json"
    if metadata_path.exists():
        previous = json.loads(metadata_path.read_text(encoding="utf-8"))
        details = {(item["market"], item["code"]): item for item in previous.get("security_details", [])}
        existing = [dict(details.get((item["market"], item["code"]), {}), **item) for item in existing]
    before = cache / "security_names.before.csv"
    if target.exists() and not before.exists():
        before.write_bytes(target.read_bytes())
    with (REPO / "resources/delisting_overrides.csv").open(encoding="utf-8-sig", newline="") as stream:
        overrides = list(csv.DictReader(stream))
    bse_listed = None
    if args.bse_listed:
        with args.bse_listed.open(encoding="utf-8-sig", newline="") as stream:
            bse_listed = list(csv.DictReader(stream))
    rows = build_master(existing, cache, args.checked_at.isoformat(), overrides, bse_listed)
    temporary = target.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)
    temporary.replace(target)
    coverage = dict(Counter(row["market"] + ":" + row["status"] for row in rows))
    manifest = {"checked_at": args.checked_at.isoformat(), "rows": len(rows), "coverage": coverage,
        "limitations": ["CNINFO Beijing names include legacy codes and delisted securities; a name is not proof of active listing.",
                        "Without a verified BSE listing export, Beijing status remains unknown except explicit delisting disclosures.",
                        "Missing from an exchange list does not establish delisting. ST and stale prices do not establish delisting."],
        "raw_files": [{"file": name, "sha256": hashlib.sha256((cache / name).read_bytes()).hexdigest(),
                       "endpoints": urls} for name, urls in DOWNLOADS.items()],
        "csv_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "security_details": rows}
    (REPO / "resources/security_metadata.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for platform in ("windows", "cli"):
        release = REPO.parent / "dist" / platform
        if release.is_dir():
            for name in ("security_names.csv", "security_metadata.json"):
                shutil.copy2(REPO / "resources" / name, release / name)
    print(json.dumps({"rows": len(rows), "coverage": coverage}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
