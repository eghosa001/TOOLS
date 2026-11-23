"""Offline mock specification for live exchange-stop acknowledgement checks.

Does not contact Kraken, submit an order, verify an actual exchange stop or
claim a real reduction in risk. Freqtrade handles exchange-side stops in LIVE
mode, which this repository forbids.
"""

def check_ack(position,stop):
    try:
        if not position or not stop:return False
        if stop.get("status") not in ("open","accepted"):return False
        if stop.get("type")!="stop-market" or stop.get("reduce_only") is not True:return False
        if stop.get("trigger")!="mark" or not stop.get("order_id"):return False
        if stop.get("symbol")!=position["symbol"]:return False
        if stop.get("side") == position["side"]:return False
        if float(stop.get("remaining_qty",0))<float(position["qty"])-1e-10:return False
        price=float(stop["stop_price"]);entry=float(position["entry"])
        if not 0<price:return False
        return price<entry if position["side"]=="buy" else price>entry
    except (TypeError,KeyError,ValueError,ZeroDivisionError):
        return False

def response(position,stop,exchange_reachable=True):
    if not position:return "no_position"
    if not exchange_reachable:return "HALT_UNVERIFIED_OPEN_POSITION"
    if not check_ack(position,stop):return "EMERGENCY_EXIT_AND_HALT"
    return "monitor"
