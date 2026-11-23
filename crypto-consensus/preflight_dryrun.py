"""Refuse any non-dry-run, credentialed, or unprotected start."""
import json,sys
from pathlib import Path

def validate(c):
    def fail(reason):raise RuntimeError("UNSAFE CONFIG: "+reason)
    if c.get("dry_run") is not True or c.get("dry_run_wallet")!=150:fail("requires $150 paper wallet")
    if c.get("db_url")!="sqlite:////freqtrade/runtime/tradesv3.dryrun.sqlite":fail("dedicated SQLite required")
    e=c.get("exchange",{})
    if e.get("name")!="krakenfutures" or e.get("pair_whitelist")!=["ETH/USD:USD"]:fail("wrong market")
    if any(e.get(v) for v in ("key","secret","api_key","password")):fail("real credentials forbidden")
    if c.get("trading_mode")!="futures" or c.get("margin_mode")!="isolated":fail("wrong margin mode")
    if c.get("stake_currency")!="USD" or c.get("max_open_trades")!=1:fail("wrong stake")
    if c.get("force_entry_enable",True) is not False:fail("force-enter disabled")
    if c.get("api_server",{}).get("enabled",False):fail("remote API disabled")
    o=c.get("order_types",{})
    for k,v in (("stoploss_on_exchange",True),("stoploss","market"),
                ("stoploss_price_type","mark"),("emergency_exit","market")):
        if o.get(k)!=v:fail("missing stop requirement "+k)
    if int(o.get("stoploss_on_exchange_interval",0))<30:fail("unsafe stop refresh interval")
    return True

if __name__=="__main__":
    validate(json.loads(Path(sys.argv[1]).read_text()))
    print("PASS: isolated $150 DRY-RUN config; mark-trigger stop-market simulated only")
