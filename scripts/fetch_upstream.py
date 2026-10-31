"""Download an unmodified, pinned upstream reader as a reference, not a dependency."""

import hashlib
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "vendor" / "pytdx"
REPOSITORY = "https://github.com/rainx/pytdx"
SOURCE_PATH = "pytdx/reader/daily_bar_reader.py"


def main():
    metadata_path = TARGET / "provenance.json"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    opener.addheaders = [("User-Agent", "StockStudy-upstream-reference")]
    if metadata_path.is_file():
        commit = json.loads(metadata_path.read_text(encoding="utf-8"))["commit"]
    else:
        # The repository's default branch is an archive notice with the sources removed.
        url = f"https://api.github.com/repos/rainx/pytdx/commits?sha=master&path={SOURCE_PATH}&per_page=1"
        with opener.open(url, timeout=30) as stream:
            commit = json.load(stream)[0]["sha"]
    url = f"https://raw.githubusercontent.com/rainx/pytdx/{commit}/{SOURCE_PATH}"
    with opener.open(url, timeout=30) as stream:
        content = stream.read()
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "daily_bar_reader.py").write_bytes(content)
    metadata = {
        "repository": REPOSITORY, "commit": commit, "source_path": SOURCE_PATH,
        "download_url": url, "sha256": hashlib.sha256(content).hexdigest(),
        "downloaded_at": datetime.now(timezone.utc).isoformat(), "modified": False,
        "usage": "Reference only; not imported by StockStudy runtime",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    # Fetch the license as declared by GitHub, if one is present.
    try:
        with opener.open(f"https://api.github.com/repos/rainx/pytdx/license?ref={commit}", timeout=30) as stream:
            license_metadata = json.load(stream)
        import base64
        (TARGET / "LICENSE.upstream").write_bytes(base64.b64decode(license_metadata["content"]))
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        print("No standalone upstream license file reported by GitHub; see vendor README.")
    print(f"Saved original reader from {commit}; SHA-256 {metadata['sha256']}")


if __name__ == "__main__":
    main()
