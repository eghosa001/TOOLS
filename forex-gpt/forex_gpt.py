#!/usr/bin/env python3
"""Paper-only, manually triggered Forex GPT check and risk advice. No trades."""
import argparse
import datetime as dt
import json
import math
import os
import sys
import urllib.error
import urllib.request

MODEL = "gpt-6-luna"
FEATURES = ("CFTC_lev_money_net_share", "CFTC_weekly_net_change",
            "GBPUSD_2d_momentum_bp", "GBPUSD_5d_momentum_bp",
            "GBPUSD_10d_momentum_bp", "GBPUSD_5d_high_low_pips",
            "EURUSD_5d_momentum_bp", "USDJPY_5d_momentum_bp",
            "GBPUSD_last_completed_H1_range_pips")
FORMAT = {
    "type": "object",
    "properties": {
        "choice": {"type": "string", "enum": ["SKIP", "KEEP_2D", "KEEP_5D"]},
        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
        "confidence": {"type": "number"},
        "risk_reason": {"type": "string"}
    },
    "required": ["choice", "risk_level", "confidence", "risk_reason"],
    "additionalProperties": False
}
SYSTEM = (
    "You are a paper-only second-opinion risk reviewer for a GBPUSD weekly CFTC "
    "leveraged-money positioning model. You have no order authority. Use only "
    "past-known features in the supplied snapshot. Never invent news, live "
    "prices or future returns. No direction reversals. Choose SKIP, KEEP_2D "
    "or KEEP_5D, and assess potential severe losses and volatility explicitly. "
    "Previous historical GPT vetoes reduced total losing dollars but did NOT "
    "reduce worst loss or drawdown, so never claim proven risk reduction. "
    "Make a brief, concrete recommendation and calibrated confidence."
)

def validate_snapshot(x, now=None):
    if not isinstance(x, dict) or x.get("base_side") not in ("BUY", "SELL"):
        raise ValueError("Must provide a JSON object with BUY or SELL base_side")
    ts = x.get("utc_signal")
    if not isinstance(ts, str):
        raise ValueError("Missing UTC signal")
    try:
        stamp = dt.datetime.fromisoformat(ts.replace("Z", "+00:00").replace(" ", "T"))
        asof = dt.date.fromisoformat(x.get("CFTC_asof_date", ""))
    except (ValueError, TypeError):
        raise ValueError("Malformed CFTC report date / UTC timestamp") from None
    if stamp.tzinfo is None or stamp.utcoffset() != dt.timedelta(0):
        raise ValueError("Signal must explicitly be UTC")
    now = now or dt.datetime.now(dt.timezone.utc)
    if not dt.timedelta(0) <= now - stamp <= dt.timedelta(minutes=90):
        raise ValueError("Expired signal; cannot run paid inference on stale reports")
    if asof.weekday() != 1 or stamp != dt.datetime.combine(
            asof + dt.timedelta(days=8), dt.time(9), dt.timezone.utc):
        raise ValueError("CFTC report must be eligible Tue+8d, Wed09 UTC")
    for key in FEATURES:
        v = x.get(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError("Missing or invalid past-only feature: " + key)
    change = x["CFTC_weekly_net_change"]
    if not .005 <= abs(change) <= 2 or ((change > 0) != (x["base_side"] == "BUY")):
        raise ValueError("Ineligible or contradictory CPU positioning signal")
    return x

def call_api(method, endpoint, payload=None):
    secret = os.environ.get("OPENAI_API_KEY", "").strip()
    if not secret.startswith("sk-") or len(secret) < 30:
        raise ValueError("OPENAI_API_KEY not configured")
    req = urllib.request.Request(
        "https://api.openai.com/v1" + endpoint,
        data=json.dumps(payload).encode() if payload else None,
        method=method,
        headers={"Authorization": "Bearer " + secret, "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=65 if payload else 15) as res:
            return json.loads(res.read(128000))
    except urllib.error.HTTPError as err:
        raise RuntimeError("OpenAI HTTP status " + str(err.code)) from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("API connection unavailable") from None

def run_check():
    result = call_api("GET", "/models/" + MODEL)
    if result.get("id") != MODEL:
        raise RuntimeError("Unexpected API model ID")
    return {"connection": "verified", "model": MODEL, "paid_predictions": 0,
            "live_orders": 0}

def run_paper():
    raw = os.environ.get("SNAPSHOT_JSON", "")
    if not raw or len(raw) > 9000:
        raise ValueError("Paper prediction requires a fresh snapshot_json input")
    snapshot = validate_snapshot(json.loads(raw))
    response = call_api("POST", "/responses", {
        "model": MODEL, "instructions": SYSTEM,
        "input": [{"role": "user", "content": json.dumps(snapshot)}],
        "store": False, "max_output_tokens": 420,
        "text": {"format": {"type": "json_schema", "name": "forex_risk_assessment",
                            "schema": FORMAT, "strict": True}}
    })
    if response.get("status") != "completed":
        raise RuntimeError("GPT response incomplete")
    texts = [c.get("text", "")
             for item in response.get("output", []) if item.get("type") == "message"
             for c in item.get("content", []) if c.get("type") == "output_text"]
    if len(texts) != 1:
        raise RuntimeError("GPT response unavailable")
    result = json.loads(texts[0])
    if set(result) != set(FORMAT["required"]) or result.get("choice") not in (
            "SKIP", "KEEP_2D", "KEEP_5D"):
        raise RuntimeError("GPT returned invalid choice")
    if result.get("risk_level") not in ("low", "medium", "high"):
        raise RuntimeError("GPT returned invalid risk level")
    conf = result.get("confidence")
    if isinstance(conf, bool) or not isinstance(conf, (float, int)) or not 0 <= conf <= 1:
        raise RuntimeError("GPT returned invalid confidence")
    if not isinstance(result.get("risk_reason"), str) or not 8 <= len(result["risk_reason"]) <= 350:
        raise RuntimeError("GPT returned invalid reason")
    return {"status": "SHADOW_ONLY", "signal_utc": snapshot["utc_signal"],
            "CPU_side": snapshot["base_side"], "GPT_advice": result,
            "token_usage": response.get("usage", {}), "CPU_changed": False,
            "live_orders": 0, "paper_orders": 0}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("check", "paper"), default="check")
    args = parser.parse_args()
    try:
        result = run_check() if args.mode == "check" else run_paper()
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, RuntimeError, json.JSONDecodeError) as err:
        print("FOREX GPT FAILED: " + str(err), file=sys.stderr)
        print("No trades placed; CPU strategy unchanged.", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
