"""Fetch real official Kraken ETH/SOL 4h open-interest for 1h research.

Public API only; no exchange secrets and no simulated positioning data.
Fail on truncated, stale, gapped or mismatched market metadata.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen

import ccxt
import pandas as pd

from quality_candidate_features import parse_official_oi

MARKETS={"ETH/USD:USD":"PF_ETHUSD","SOL/USD:USD":"PF_SOLUSD"}
START=pd.Timestamp("2026-01-02T00:00:00Z")
END=pd.Timestamp("2026-11-22T00:00:00Z")


def fetch(exchange,symbol):
    contract=MARKETS[symbol]
    m=exchange.market(symbol)
    if m["id"]!=contract or not m.get("active") or not m.get("linear"):
        raise ValueError(f"Unexpected or disabled genuine Kraken future: {symbol}")
    if float(m.get("contractSize",0))!=1:
        raise ValueError("Unexpected futures contract amount conversion")
    url=f"https://futures.kraken.com/api/charts/v1/analytics/{contract}/open-interest?interval=14400"
    request=Request(url,headers={"User-Agent":"crypto-1h-quality-research/1.0"})
    with urlopen(request,timeout=45) as response:
        doc=json.load(response)
    if doc.get("errors") or doc["result"].get("more"):
        raise ValueError(f"Official open-interest response not complete {symbol}")
    table=parse_official_oi(doc)
    if table.iloc[0]["known_at"]>START or table.iloc[-1]["known_at"]<END:
        raise ValueError(f"Official Kraken OI does not cover test period {symbol}")
    doc["research_contract"]=contract
    return doc,{"contract":contract,"symbol":symbol,"source":url,
                "points":len(table),
                "start_utc":table.iloc[0]["known_at"].isoformat(),
                "end_utc":table.iloc[-1]["known_at"].isoformat(),
                "market_amount_precision":m["precision"]["amount"]}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dir",required=True)
    p.add_argument("--manifest",required=True)
    opts=p.parse_args()
    root=Path(opts.dir)
    root.mkdir(parents=True,exist_ok=True)
    ex=ccxt.krakenfutures({"enableRateLimit":True})
    manifest={}
    try:
        ex.load_markets()
        for symbol,contract in MARKETS.items():
            data,meta=fetch(ex,symbol)
            b=(json.dumps(data,sort_keys=True,separators=(",",":"))+"\n").encode()
            meta["sha256"]=hashlib.sha256(b).hexdigest()
            (root/(contract+".json")).write_bytes(b)
            manifest[symbol]=meta
            print("ONEH_REAL_OI",json.dumps(meta,sort_keys=True))
    finally:
        ex.close()
    Path(opts.manifest).write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    main()
