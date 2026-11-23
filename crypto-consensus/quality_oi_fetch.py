"""Download Kraken's official 4h ETH open-interest historical chart, no keys."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

import pandas as pd

from quality_candidate_features import parse_official_oi

SOURCE = "https://futures.kraken.com/api/charts/v1/analytics/PF_ETHUSD/open-interest?interval=14400"
START = pd.Timestamp("2026-01-05T00:00:00Z")
LAST = pd.Timestamp("2026-11-22T00:00:00Z")


def fetch() -> dict:
    request = urllib.request.Request(
        SOURCE, headers={"User-Agent": "crypto-consensus-free-official-oi-audit/1.0"})
    with urllib.request.urlopen(request, timeout=50) as response:
        if response.status != 200:
            raise RuntimeError("Official Kraken OI endpoint not available")
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError("Kraken OI API explicitly reported errors")
    table = parse_official_oi(data)
    if table.iloc[0]["known_at"] > START:
        raise RuntimeError("Official open-interest history starts too late for January tests")
    if table.iloc[-1]["known_at"] < LAST:
        raise RuntimeError("Official open-interest history is stale")
    if data["result"].get("more"):
        raise RuntimeError("Official OI history is truncated; refuse unpaged first block")
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    opts = p.parse_args()
    data = fetch()
    output = Path(opts.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
    output.write_bytes(raw)
    r = data["result"]
    print(json.dumps({
        "source": SOURCE,
        "status": "actual_verified_exchange_open_interest_no_imputation",
        "points": len(r["timestamp"]),
        "oldest_observation_utc": datetime.fromtimestamp(
            int(r["timestamp"][0]), timezone.utc).isoformat(),
        "newest_observation_utc": datetime.fromtimestamp(
            int(r["timestamp"][-1]), timezone.utc).isoformat(),
        "download_sha256": hashlib.sha256(raw).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
