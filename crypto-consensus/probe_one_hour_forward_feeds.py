"""Read-only live feed compatibility check for 1h forward ETH paper research."""
import ccxt
from datetime import datetime,timezone

def at(ms):
    return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat()

e=ccxt.krakenfutures({"enableRateLimit":True})
try:
    e.load_markets()
    print("MARKET",e.market("ETH/USD:USD")["id"],e.market("ETH/USD:USD")["precision"]["amount"],e.market("ETH/USD:USD")["limits"])
    for symbol,tf,params in [
        ("ETH/USD:USD","1h",{}),
        ("BTC/USD:USD","12h",{}),
        ("ETH/USD:USD","1h",{"price":"mark"}),
        ("ETH/USD:USD","1h",{"price":"funding_rate"}),
    ]:
        try:
            rows=e.fetch_ohlcv(symbol,tf,limit=600,params=params)
            print("OHLCV_FEED",symbol,tf,params,"count",len(rows),"first",at(rows[0][0]),"last",at(rows[-1][0]),"sample",rows[-1])
        except Exception as exc:
            print("OHLCV_FAILED",symbol,tf,params,type(exc).__name__,str(exc)[:260])
    try:
        since=e.milliseconds()-35*86400000
        rows=e.fetch_funding_rate_history("ETH/USD:USD",since=since,limit=1000)
        print("FUNDING_HISTORY",len(rows),"first",at(rows[0]["timestamp"]) if rows else None,"last",at(rows[-1]["timestamp"]) if rows else None,"sample",rows[-1] if rows else None)
    except Exception as exc:
        print("FUNDING_HISTORY_FAILED",type(exc).__name__,str(exc)[:300])
    try:
        book=e.fetch_order_book("ETH/USD:USD",limit=10)
        print("ORDERBOOK",book["bids"][0],book["asks"][0],book.get("timestamp"))
    except Exception as exc:
        print("ORDERBOOK_FAILED",type(exc).__name__,str(exc)[:250])
finally:
    e.close()
