#!/usr/bin/env python3
"""Writes data.json: a dated snapshot of every dataset the page uses, so the site works as plain
static files (e.g. GitHub Pages). Any source that fails keeps its previous value from data.json.
Set SEC_USER_AGENT to override the SEC-required User-Agent ("name contact")."""
import json, os, time, datetime, serve
RANGES = list(serve.ALLOWED)  # 1d,5d,1mo,6mo,1y,5y,max
try: old = json.load(open("data.json"))
except Exception: old = {}
out = {"generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "charts": {}}
status = {}
for r in RANGES:
    try: out["charts"][r] = serve.chart(r); status[r] = "ok"
    except Exception as e:
        prev = old.get("charts", {}).get(r) or (old.get("chart") if r == "6mo" else None)
        if prev: out["charts"][r] = prev
        status[r] = f"FAILED ({e}); kept previous" if prev else f"FAILED ({e})"
    time.sleep(0.5)
out["chart"] = out["charts"].get("6mo")  # backward compat
for k, fn in [("shares", serve.shares), ("short", serve.short), ("filings", serve.filings)]:
    try: out[k] = fn(); status[k] = "ok"
    except Exception as e:
        if old.get(k) and "error" not in old[k]: out[k] = old[k]; status[k] = f"FAILED ({e}); kept previous"
        else: out[k] = {"error": str(e)}; status[k] = f"FAILED ({e})"
with open("data.json", "w") as f: json.dump(out, f, separators=(",", ":"))
for k, v in status.items(): print(f"{k:8} {v}")
if all(v != "ok" for v in status.values()): raise SystemExit("all sources failed")
