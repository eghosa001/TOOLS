"""Forward-only, keyless Solana new-pool cohort and paper wallet.
No wallet, private key, order submission, trading SDK, or brokerage integration.
Cohort includes ALL pools observed in the sampled new-pool feed, including
unqualified pools and later disappearing tokens. Never backfill discoveries.
API snapshots are NOT executable quotes, execution losses are uncertain.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone,timedelta
import json
import math
import os
from pathlib import Path
import time
from urllib.parse import urlencode,quote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ROOT=Path(__file__).resolve().parent
STATE=ROOT/"onchain_forward_state.json"
REPORT=ROOT/"onchain_forward_report.json"
GT="https://api.geckoterminal.com/api/v2"
GO="https://api.gopluslabs.io/api/v1/solana/token_security"
SOL="So11111111111111111111111111111111111111112"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT="Es9vMFrzaCERtqNJrsiKijTQfLXFP8Lshj4Vz3fV7jX"
QUOTES={SOL,USDC,USDT}
MIN_LIQ=50000.0
MIN_VOL5=12000.0
FEE_SIDE=.015   # 1.5% per side hypothetical DEX friction incl fee/slippage
STOP_LOSS=.10
TAKE_PROFIT=.25
MAX_HOLD_S=2*3600
STAKE_FRACTION=.10
MAX_NEW_PAGES=2
MAX_SECURITY_PER_RUN=3
MAX_TRACKING=20
DAY_S=24*3600

def utc(epoch):
    return datetime.fromtimestamp(epoch,timezone.utc).isoformat()

def ts(text):
    return datetime.fromisoformat(str(text).replace("Z","+00:00")).timestamp()

def number(x):
    try:
        z=float(x)
        return z if math.isfinite(z) else None
    except (ValueError,TypeError):
        return None

def blank():
    return {"version":1,"created_at":None,"last_observed_at":None,"last_attempt_at":None,
            "gaps":[],"pools":{},"paper":{"wallet":150.,"position":None,
            "closed_trades":[],"day":None,"week":None,"day_equity":150.,
            "week_equity":150.,"peak_equity":150.,"daily_lock":False,
            "weekly_lock":False,"permanent_lock":False,"last_entry_at":None},
            "provider_errors":[],"observations":0}

def request(url,attempts=3):
    """Whitelisted public GETs; never sends user secrets or orders."""
    if not (url.startswith(GT+"/networks/solana/") or
            url.startswith(GO+"?")):
        raise ValueError("Provider not on safe GET allowlist")
    for attempt in range(attempts):
        try:
            req=Request(url,headers={"Accept":"application/json;version=20230203",
                                     "User-Agent":"research-paper-only/1.0"})
            with urlopen(req,timeout=25) as res:
                data=json.load(res)
            if not isinstance(data,dict):
                raise ValueError("Malformed API response")
            return data
        except (HTTPError,URLError,TimeoutError) as exc:
            if attempt==attempts-1:
                raise RuntimeError("Provider unavailable: "+str(exc)) from exc
            time.sleep(min(4*(attempt+1),8))
    raise RuntimeError("Unreachable")

def parse_pools(payload,now):
    data=payload.get("data")
    if not isinstance(data,list):
        raise ValueError("New pools API response missing data list")
    includes={}
    for item in payload.get("included",[]):
        if isinstance(item,dict):
            includes[item.get("id")]=item
    parsed=[]
    for p in data:
        if not isinstance(p,dict):
            continue
        attrs=p.get("attributes") or {}
        rel=p.get("relationships") or {}
        key=p.get("id")
        address=attrs.get("address") or (key.split("_",1)[-1] if isinstance(key,str) else None)
        if not address or not isinstance(address,str) or len(address)<30:
            continue
        base=(rel.get("base_token") or {}).get("data") or {}
        quote_token=(rel.get("quote_token") or {}).get("data") or {}
        b=includes.get(base.get("id"),{})
        q=includes.get(quote_token.get("id"),{})
        mint=(b.get("attributes") or {}).get("address")
        quote_mint=(q.get("attributes") or {}).get("address")
        if not mint and isinstance(base.get("id"),str):
            mint=base["id"].split("_",1)[-1]
        if not quote_mint and isinstance(quote_token.get("id"),str):
            quote_mint=quote_token["id"].split("_",1)[-1]
        if not mint:
            continue
        try:
            created=ts(attrs["pool_created_at"])
        except (KeyError,ValueError,TypeError):
            continue
        if created>now+300:
            continue
        tx=(attrs.get("transactions") or {}).get("m5") or {}
        v=(attrs.get("volume_usd") or {}).get("m5")
        parsed.append({"pool":address,"mint":mint,"quote":quote_mint,
             "symbol":(b.get("attributes") or {}).get("symbol"),
             "created":created,"price":number(attrs.get("base_token_price_usd")),
             "liquidity":number(attrs.get("reserve_in_usd")),
             "volume5":number(v),"buys5":int(number(tx.get("buys")) or 0),
             "sells5":int(number(tx.get("sells")) or 0),
             "at":now})
    return parsed

def security_ok(data):
    """Fail-closed Solana GoPlus fields. Missing is never equivalent to safe."""
    if not isinstance(data,dict):
        return False,"unknown_payload"
    for key in ("mintable","freezable","closable","balance_mutable_authority",
                "non_transferable","transfer_hook"):
        val=data.get(key)
        # transfer_hook absence is not a positive safety assertion; optional,
        # while unknown permission status is disqualifying.
        if key=="transfer_hook":
            if val not in (None,{},"",False):
                return False,"hook_present"
            continue
        if key=="non_transferable":
            if str(val) not in ("0","False","false"):
                return False,"transferability_unknown_or_blocked"
            continue
        if not isinstance(val,dict) or str(val.get("status"))!="0":
            return False,key+"_not_explicitly_safe"
    if str(data.get("default_account_state")) not in ("1",):
        return False,"default_state_not_initialized"
    holders=data.get("holders")
    if not isinstance(holders,list) or not holders:
        return False,"holder_distribution_unknown"
    perc=[number(x.get("percent")) for x in holders if isinstance(x,dict)]
    if not perc or any(x is None for x in perc):
        return False,"holder_concentration_unavailable"
    # GoPlus holder percent uses fraction of supply (0..1).
    if any(x<0 or x>1 for x in perc):
        return False,"invalid_holder_percent"
    if sum(sorted(perc,reverse=True)[:10])>.50:
        return False,"top10_concentrated"
    return True,"passed"

def check_token(mint):
    url=GO+"?"+urlencode({"contract_addresses":mint})
    payload=request(url)
    if str(payload.get("code")) not in ("1","0","200"):
        return False,"provider_rejected"
    table=payload.get("result")
    if not isinstance(table,dict):
        return False,"missing_security_result"
    obj=table.get(mint) or table.get(mint.lower())
    return security_ok(obj)

def candidate(p,now):
    age=now-p["created"]
    return (0<=age<=75*60 and p["quote"] in QUOTES and
            p["mint"] not in QUOTES and
            p["price"] is not None and p["price"]>0 and
            p["liquidity"] is not None and p["liquidity"]>=MIN_LIQ and
            p["volume5"] is not None and p["volume5"]>=MIN_VOL5 and
            p["buys5"]>=25 and p["sells5"]>=10 and
            p["buys5"]<=5*max(p["sells5"],1))

def equity(paper,quote=None):
    value=float(paper["wallet"])
    pos=paper["position"]
    if pos:
        latest=(quote or {}).get("price") if quote else None
        if latest is None or latest<=0:
            latest=pos["last_price"]
        value += pos["stake"]*((latest/pos["entry"])*(1-FEE_SIDE)-1)
    return value

def guards(paper,now,mark):
    day=utc(now)[:10]
    week=datetime.fromtimestamp(now,timezone.utc).date()
    week=(week-timedelta(days=week.weekday())).isoformat()
    if paper["day"]!=day:
        paper["day"]=day
        paper["day_equity"]=mark
        paper["daily_lock"]=False
    if paper["week"]!=week:
        paper["week"]=week
        paper["week_equity"]=mark
        paper["weekly_lock"]=False
    paper["peak_equity"]=max(paper["peak_equity"],mark)
    if mark<=.98*paper["day_equity"]:
        paper["daily_lock"]=True
    if mark<=.96*paper["week_equity"]:
        paper["weekly_lock"]=True
    if mark<=.94*paper["peak_equity"]:
        paper["permanent_lock"]=True

def close(paper,now,price,reason,impact=0.):
    pos=paper["position"]
    if not pos:
        return
    # exit price is snapshot proxy, further adverse modeled impact (0..100%)
    liquidation=max(0.,price*(1-impact))
    recovered=pos["stake"]*(liquidation/pos["entry"])*(1-FEE_SIDE)
    paper["wallet"]+=recovered
    net=recovered-pos["stake_gross"]
    paper["closed_trades"].append({"pool":pos["pool"],"mint":pos["mint"],
        "entry_at":utc(pos["opened"]),"closed_at":utc(now),
        "reason":reason,"net_usd":round(net,6),
        "net_pct_on_stake":round(100*net/pos["stake_gross"],4)})
    paper["position"]=None

def mark_position(state,observed,now):
    paper=state["paper"]
    pos=paper["position"]
    if not pos:
        return
    p=observed.get(pos["pool"])
    if p and p["price"] is not None and p["price"]>0:
        pos["missing"]=0
        pos["last_price"]=p["price"]
        pos["last_liquidity"]=p["liquidity"]
        pos["last_seen"]=now
        mark=equity(paper,p)
        guards(paper,now,max(mark,0.01))
        if p["liquidity"] is not None and p["liquidity"]<5000:
            close(paper,now,p["price"],"liquidity_evaporation",impact=.75)
        elif p["price"]/pos["entry"]<=1-STOP_LOSS:
            # 10% stop is only a threshold, no guaranteed execution
            close(paper,now,p["price"],"stop_snapshot",impact=.05)
        elif p["price"]/pos["entry"]>=1+TAKE_PROFIT:
            close(paper,now,p["price"],"take_profit_snapshot",impact=.02)
        elif now-pos["opened"]>=MAX_HOLD_S:
            close(paper,now,p["price"],"two_hour_time_exit",impact=.02)
        elif paper["permanent_lock"]:
            close(paper,now,p["price"],"risk_lock_exit",impact=.05)
    else:
        pos["missing"]+=1
        if pos["missing"]>=2:
            close(paper,now,0.,"twice_unpriced_pessimistic_writeoff",impact=1.)
    guards(paper,now,max(equity(paper,p),.01))

def record_snapshot(state,rows,now):
    # permanently retain all observed entries even if token is unsafe or vanishes
    tracked=state["pools"]
    observed={}
    for p in rows:
        key=p["pool"]
        observed[key]=p
        old=tracked.get(key)
        if old is None:
            tracked[key]={"pool":key,"mint":p["mint"],"quote":p["quote"],
                "created":utc(p["created"]),"first_seen_at":utc(now),
                "last_seen_at":utc(now),"first_price":p["price"],
                "first_liquidity_usd":p["liquidity"],
                "last_price":p["price"],"last_liquidity_usd":p["liquidity"],
                "observed_count":1,"status":"observed_unscreened",
                "security_status":"not_checked"}
        else:
            old["last_seen_at"]=utc(now)
            old["last_price"]=p["price"]
            old["last_liquidity_usd"]=p["liquidity"]
            old["observed_count"]+=1
    return observed

def followup(state,observed,now):
    # A rate-limited subset, tracked explicitly to avoid assuming unseen survivors.
    tracked=state["pools"]
    eligible=[(k,v) for k,v in tracked.items()
              if k not in observed and v["status"] not in ("followed_24h","liquidity_lost") and
              now-ts(v["first_seen_at"])>=24*3600]
    eligible.sort(key=lambda kv:(kv[1].get("followup_count",0),
                                 kv[1]["first_seen_at"],kv[0]))
    samples=eligible[:MAX_TRACKING]
    if not samples:
        return
    addresses=",".join(quote(k,safe="") for k,_ in samples)
    payload=request(GT+"/networks/solana/pools/multi/"+addresses)
    live=parse_pools(payload,now) if payload.get("included") else []
    by={p["pool"]:p for p in live}
    for key,old in samples:
        old["followup_count"]=old.get("followup_count",0)+1
        p=by.get(key)
        if p is None:
            # "not in response" is not proof of rug; preserve as missing.
            old["status"]="followup_missing_unresolved"
            continue
        old["last_liquidity_usd"]=p["liquidity"]
        old["last_price"]=p["price"]
        old["last_seen_at"]=utc(now)
        old["status"]="liquidity_lost" if (p["liquidity"] or 0)<1000 else "followed_24h"

def fresh_feed(now):
    results=[]
    for page in range(1,MAX_NEW_PAGES+1):
        url=GT+"/networks/solana/new_pools?"+urlencode({"include":"base_token,quote_token,dex","page":page})
        payload=request(url)
        results.extend(parse_pools(payload,now))
        if page<MAX_NEW_PAGES:
            time.sleep(6)  # stay under public 10rpm guidance
    return results

def observation(state,rows,now,sec_check,detail):
    if state["version"]!=1:
        raise ValueError("Unknown version")
    if state["last_observed_at"] and now<=ts(state["last_observed_at"]):
        raise RuntimeError("Non-monotonic forward time")
    if state["last_observed_at"] and now-ts(state["last_observed_at"])>45*60:
        state["gaps"].append({"since":state["last_observed_at"],"until":utc(now),
                              "reason":"scheduler_gap_no_backfill"})
    if len(state["gaps"])>50:
        state["gaps"]=state["gaps"][-50:]
    state["created_at"]=state["created_at"] or utc(now)
    observed=record_snapshot(state,rows,now)
    paper=state["paper"]
    # Monitor open position even if pool dropped from the new-pools feed.
    pos=paper["position"]
    if pos and pos["pool"] not in observed:
        try:
            updated=detail(pos["pool"],now)
            if updated: observed[pos["pool"]]=updated
        except Exception as err:
            state["provider_errors"].append({"at":utc(now),"kind":"position_detail", "reason":str(err)[:100]})
            # Fail closed: treat as missing, not filled at old price.
    mark_position(state,observed,now)
    if paper["position"] is None:
        guards(paper,now,max(equity(paper),.01))
    # Selection is at observed time; EXECUTION occurs only at a later observation.
    pending=paper.get("pending")
    if pending:
        if now-pending["signaled_at"]>60*60:
            paper["pending"]=None
        elif now>pending["signaled_at"]+60 and paper["position"] is None:
            p=observed.get(pending["pool"])
            if p is None:
                try: p=detail(pending["pool"],now)
                except Exception: p=None
            if p is not None and p["price"] and p["liquidity"] and p["liquidity"]>=MIN_LIQ/2 and \
               not(paper["daily_lock"] or paper["weekly_lock"] or paper["permanent_lock"]):
                if paper["last_entry_at"] is None or now-paper["last_entry_at"]>=DAY_S:
                    gross=min(paper["wallet"]*STAKE_FRACTION,15.)
                    if gross>1:
                        paper["wallet"]-=gross
                        paper["position"]={"pool":p["pool"],"mint":p["mint"],
                            "entry":p["price"]*(1+FEE_SIDE),
                            "stake":gross*(1-FEE_SIDE),
                            "stake_gross":gross,"opened":now,
                            "last_price":p["price"],"last_liquidity":p["liquidity"],
                            "last_seen":now,"missing":0}
                        paper["last_entry_at"]=now
                        state["pools"][p["pool"]]["status"]="paper_entered"
            paper["pending"]=None
    if paper["position"] is None and paper.get("pending") is None and not \
       (paper["daily_lock"] or paper["weekly_lock"] or paper["permanent_lock"]):
        new=[p for p in rows if state["pools"][p["pool"]]["first_seen_at"]==utc(now) and candidate(p,now)]
        # deterministically rank by real observed 5m volume; no price future used
        new.sort(key=lambda p:(-p["volume5"],p["pool"]))
        for p in new[:MAX_SECURITY_PER_RUN]:
            try: ok,reason=sec_check(p["mint"])
            except Exception as err: ok,reason=False,"security_feed_error"
            state["pools"][p["pool"]]["security_status"]=reason
            if ok:
                paper["pending"]={"pool":p["pool"],"signaled_at":now}
                state["pools"][p["pool"]]["status"]="signal_pending_next_observation"
                break
            state["pools"][p["pool"]]["status"]="security_rejected"
    state["last_observed_at"]=utc(now)
    state["observations"]+=1
    if len(state["provider_errors"])>30:
        state["provider_errors"]=state["provider_errors"][-30:]
    return state

def pool_detail(address,now):
    payload=request(GT+"/networks/solana/pools/"+quote(address,safe="")+"?include=base_token,quote_token")
    item=payload.get("data")
    if not isinstance(item,dict):
        return None
    return (parse_pools({"data":[item],"included":payload.get("included",[])},now) or [None])[0]

def summarize(s,now):
    paper=s["paper"]
    amounts=[float(x["net_usd"]) for x in paper["closed_trades"]]
    return {"last_observed_at":s["last_observed_at"],
            "mode":"forward-only public Solana pool snapshots / no real trades",
            "wallet_start_usd":150.0,"cash_usd":round(paper["wallet"],4),
            "modeled_open_equity_usd":round(equity(paper),4),
            "open_position":bool(paper["position"]),"pending":bool(paper.get("pending")),
            "closed_trades":len(amounts),"wins":sum(x>0 for x in amounts),
            "losses":sum(x<0 for x in amounts),
            "total_closed_trade_net_usd":round(sum(amounts),4),
            "observations":s["observations"],
            "distinct_pools_observed":len(s["pools"]),
            "security_rejected":sum(v["status"]=="security_rejected" for v in s["pools"].values()),
            "followed_24h":sum(v["status"]=="followed_24h" for v in s["pools"].values()),
            "liquidity_lost_observed":sum(v["status"]=="liquidity_lost" for v in s["pools"].values()),
            "missing_followups_unresolved":sum(v["status"]=="followup_missing_unresolved" for v in s["pools"].values()),
            "daily_lock":paper["daily_lock"],"weekly_lock":paper["weekly_lock"],
            "permanent_lock":paper["permanent_lock"],
            "scheduler_gap_events":len(s["gaps"]),
            "assumptions":{"per_side_friction":FEE_SIDE,
                "10pct_stop_is_not_guaranteed":True,
                "first_seen_is_when_provider_listed_pool_not_block_creation":True,
                "sampling_is_incomplete_and_rate_limited":True,
                "every_observed_pool_retained_including_disappearing_pools":True,
                "unobserved_launches_omitted_by_sampling":True,
                "no_historical_backfill_or_offchain_order_execution":True}}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--smoke",action="store_true")
    parser.add_argument("--state",type=Path,default=STATE)
    parser.add_argument("--report",type=Path,default=REPORT)
    args=parser.parse_args()
    now=time.time()
    rows=fresh_feed(now)
    if not rows:
        raise RuntimeError("Public new pools feed empty, fail closed")
    if args.smoke:
        print(json.dumps({"status":"live_public_feed_ok","sample_count":len(rows),
            "sample_pool":rows[0]["pool"],"no_state_mutated":True}))
        return
    state=json.loads(args.state.read_text()) if args.state.exists() else blank()
    state=observation(state,rows,now,check_token,pool_detail)
    # Follow-up failure never invents a cohort outcome; main observation remains.
    try: followup(state,{x["pool"]:x for x in rows},now)
    except Exception as exc:
        state["provider_errors"].append({"at":utc(now),"kind":"followup","reason":str(exc)[:100]})
    args.state.parent.mkdir(parents=True,exist_ok=True)
    args.state.write_text(json.dumps(state,sort_keys=True,separators=(",",":"))+"\n")
    report=summarize(state,now)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,sort_keys=True))
if __name__=="__main__":
    main()
