"""Full SEC quarterly numeric dataset + complete company-facts files for 8 peers."""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
PEERS = {
    "CRM": 1108524,
    "NOW": 1373715,
    "ADBE": 796343,
    "INTU": 896878,
    "WDAY": 1327811,
    "TEAM": 1650372,
    "HUBS": 1404655,
    "SNOW": 1640147,
}


def retrieve(url, path):
    if path.exists():
        return
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": os.environ.get(
                "SEC_USER_AGENT", "AnalystPortfolio research contact portfolio@example.com"
            )
        },
    )
    temp = path.with_suffix(path.suffix + ".part")
    with urllib.request.urlopen(req, timeout=180) as r, temp.open("wb") as f:
        shutil.copyfileobj(r, f)
    temp.replace(path)
    time.sleep(0.25)  # Well below SEC's ten requests/second limit; no parallel downloader.


def run():
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    report = ROOT / "reports"
    report.mkdir(exist_ok=True)
    sources = []
    # Full population for a closed historical quarter, not a toy peer-only CSV.
    url = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/2025q4.zip"
    archive = raw / "2025q4.zip"
    retrieve(url, archive)
    if not zipfile.is_zipfile(archive):
        raise ValueError("SEC returned non-ZIP response")
    with zipfile.ZipFile(archive) as z:
        for name in ["sub.txt", "num.txt", "tag.txt", "pre.txt"]:
            with z.open(name) as src, (raw / name).open("wb") as dst:
                shutil.copyfileobj(src, dst)
    sources.append((url, archive))
    for ticker, cik in PEERS.items():
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
        path = raw / (ticker + ".json")
        retrieve(url, path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("cik") != cik:
            raise ValueError("Wrong company returned")
        sources.append((url, path))
        print(ticker, data["entityName"], flush=True)
    manifest = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {
                "url": url,
                "file": p.name,
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for url, p in sources
        ],
    }
    (report / "source_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    run()
