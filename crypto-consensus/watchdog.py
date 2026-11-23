"""Sticky entry-pause watchdog for an isolated, keyless Freqtrade DRY-RUN.

No exchange API, no credentials, and never any order placement.
Missing/stale bot heartbeat or suspicious stop/margin log freezes entries.
"""
import argparse,json,time
from pathlib import Path

TRIGGERS=("failed to create stoploss","failed to create stop-loss",
          "emergency_exit initiated","emergency exit placed","stoploss creation failed",
          "failed to place stoploss","stoploss order rejected",
          "insufficient margin","liquidation")

def evaluate(runtime:Path,now:float,age_limit:int=210):
    f=runtime/"freqtrade.log"
    if not f.exists():
        marker=runtime/"watchdog_start_epoch"
        if not marker.exists():
            marker.write_text(str(now))
        try:
            startup=float(marker.read_text())
        except (ValueError,OSError):
            return "invalid watchdog startup marker"
        if now-startup<240:
            return None
        return "Freqtrade heartbeat log is missing after startup grace period"
    if now-f.stat().st_mtime>age_limit:return "Freqtrade heartbeat log stale"
    try:
        with f.open("rb") as h:
            h.seek(0,2);h.seek(max(0,h.tell()-36000))
            tail=h.read().decode("utf-8","replace").lower()
    except OSError:
        return "cannot read Freqtrade heartbeat log"
    if any(t in tail for t in TRIGGERS):return "potential stoploss, emergency-exit or margin incident"
    return None

def check(runtime:Path,now:float|None=None,age_limit:int=210):
    now=time.time() if now is None else now
    runtime.mkdir(parents=True,exist_ok=True)
    problem=evaluate(runtime,now,age_limit)
    paused=runtime/"PAUSE_ENTRIES"
    if problem and not paused.exists():
        paused.write_text("DO NOT AUTOMATICALLY CLEAR: "+problem+"\n")
    status={"at_utc_epoch":int(now),"paused":paused.exists(),
            "reason":problem or ("existing manual pause" if paused.exists() else None),
            "exchange_side_stop_verified":False,"mode":"KEYLESS_DRY_RUN"}
    (runtime/"watchdog_status.json").write_text(json.dumps(status,sort_keys=True,indent=2)+"\n")
    return status

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--runtime",default="/freqtrade/runtime")
    ap.add_argument("--once",action="store_true")
    ap.add_argument("--age-limit",type=int,default=210)
    x=ap.parse_args()
    while True:
        print(json.dumps(check(Path(x.runtime),age_limit=x.age_limit)),flush=True)
        if x.once:break
        time.sleep(30)

if __name__=="__main__":
    main()
