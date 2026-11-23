"""Obtain verified actual Kraken Futures 4h open-interest for five markets.

A new official data request is made for each run. Never synthesize backfills
or silently accept missing funding/open-interest history.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

import ccxt
import pandas as pd

from quality_candidate_features import parse_official_oi

CONTRACTS = {
    "BTC/USD:USD": "PF_XBTUSD",
    "SOL/USD:USD": "PF_SOLUSD",
    "XRP/USD:USD": "PF_XRPUSD",
    "DOGE/USD:USD": "PF_DOGEUSD",
    "ADA/USD:USD": "PF_ADAUSD",
}
BEFORE_START = pd.Timestamp("2026-01-01T00:00:00Z")
AFTER_END = pd.Timestamp("2026-11-22T00:00:00Z")


def obtain(exchange, symbol):
    expected = CONTRACTS[symbol]
    market = exchange.market(symbol)
    if (market["id"] != expected or not market.get("active", False)
            or not market.get("linear", False) or float(market["contractSize"]) != 1):
        raise RuntimeError(f"Unapproved or changed futures contract: {symbol}")
    url = (f"https://futures.kraken.com/api/charts/v1/analytics/"
           f"{expected}/open-interest?interval=14400")
    with urlopen(Request(url, headers={
        "User-Agent": "crypto-consensus-multiasset-causal-research/1.0"
    }), timeout=35) as response:
        document = json.load(response)
    observations = parse_official_oi(document)
    if (observations.iloc[0]["known_at"] > BEFORE_START
            or observations.iloc[-1]["known_at"] < AFTER_END
            or document["result"].get("more")):
        raise RuntimeError(f"Unusable or truncated OI history: {symbol}")
    document["research_contract"] = expected
    source = document["result"]
    return document, {
        "symbol": symbol,
        "contract": expected,
        "official_open_interest_source": url,
        "points": len(source["timestamp"]),
        "oldest_utc": datetime.fromtimestamp(
            source["timestamp"][0], timezone.utc).isoformat(),
        "newest_utc": datetime.fromtimestamp(
            source["timestamp"][-1], timezone.utc).isoformat(),
        "precision_amount": market["precision"]["amount"],
        "contract_size": market["contractSize"],
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",required=True)
    p.add_argument("--manifest",required=True)
    a=p.parse_args()
    root=Path(a.directory)
    root.mkdir(parents=True,exist_ok=True)
    ex=ccxt.krakenfutures({"enableRateLimit":True})
    manifest={}
    try:
        ex.load_markets()
        for symbol in CONTRACTS:
            doc, row=obtain(ex, symbol)
            raw=(json.dumps(doc,sort_keys=True,separators=(",",":"))+"\n").encode()
            row["source_sha256"]=hashlib.sha256(raw).hexdigest()
            (root/(CONTRACTS[symbol]+".json")).write_bytes(raw)
            manifest[symbol]=row
            print("VERIFIED_OI",json.dumps(row,sort_keys=True))
    finally:
        ex.close()
    Path(a.manifest).write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    main()
