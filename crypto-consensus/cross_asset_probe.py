"""Exchange capability probe for cross-asset historical paper backtesting."""
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
import ccxt

CANDIDATES=("BTC/USD:USD","SOL/USD:USD","XRP/USD:USD","DOGE/USD:USD","ADA/USD:USD")
ex=ccxt.krakenfutures({"enableRateLimit":True})
try:
    ex.load_markets()
    for symbol in CANDIDATES:
        if symbol not in ex.markets:
            print("ASSET_PROBE",json.dumps({"symbol":symbol,"status":"not_listed"}))
            continue
        market=ex.market(symbol)
        row={"symbol":symbol,"market_id":market["id"],"active":market.get("active"),
             "linear":market.get("linear"),"contract_size":market.get("contractSize"),
             "precision_amount":market.get("precision",{}).get("amount"),
             "min_amount":market.get("limits",{}).get("amount",{}).get("min"),
             "min_cost":market.get("limits",{}).get("cost",{}).get("min")}
        url=f"https://futures.kraken.com/api/charts/v1/analytics/{market['id']}/open-interest?interval=14400"
        try:
            with urlopen(Request(url,headers={"User-Agent":"crypto-consensus-crossasset/1.0"}),timeout=35) as resp:
                data=json.load(resp)
            r=data.get("result",{})
            timestamps=r.get("timestamp",[])
            row["oi_points"]=len(timestamps)
            row["oi_more"]=r.get("more")
            row["oi_errors"]=data.get("errors")
            if timestamps:
                row["oi_oldest"]=datetime.fromtimestamp(timestamps[0],timezone.utc).isoformat()
                row["oi_newest"]=datetime.fromtimestamp(timestamps[-1],timezone.utc).isoformat()
                row["oi_example"]=r.get("data",[])[:1]
        except Exception as exc:
            row["oi_error"]=str(exc)[:220]
        print("ASSET_PROBE",json.dumps(row,sort_keys=True))
finally:
    ex.close()
