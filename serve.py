#!/usr/bin/env python3
"""Static server + tiny same-origin data proxy for the GME site.
Endpoints: /api/chart?range=6mo&interval=1d (Yahoo), /api/shares (SEC EDGAR), /api/short (FINRA).
Responses cached in memory for 5 min. Run: python3 serve.py [port]"""
import json, sys, time, urllib.request, urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# SEC requires a descriptive User-Agent with a real contact email: https://www.sec.gov/os/accessing-edgar-data
# Set SEC_USER_AGENT (e.g. "Your Name you@yourdomain.com"); the default below is a placeholder contact.
SEC_UA = os.environ.get("SEC_USER_AGENT") or "gme-site fan tracker AJ gme-site@example.com"
WEB_UA = "Mozilla/5.0 (X11; Linux x86_64) gme-fan-site/1.0"
CACHE, TTL = {}, 300
ALLOWED = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d", "1y": "1d", "5y": "1wk", "max": "1mo"}

def http(url, data=None, headers=None):
    h = {"User-Agent": SEC_UA if "sec.gov" in url else WEB_UA}; h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def chart(rng):
    rng = rng if rng in ALLOWED else "6mo"
    d = http(f"https://query1.finance.yahoo.com/v8/finance/chart/GME?range={rng}&interval={ALLOWED[rng]}")
    return d

def shares():
    d = http("https://data.sec.gov/api/xbrl/companyconcept/CIK0001326380/dei/EntityCommonStockSharesOutstanding.json")
    last = sorted(d["units"]["shares"], key=lambda x: (x["end"], x["filed"]))[-1]
    return {"shares": last["val"], "asOf": last["end"], "form": last["form"], "filed": last["filed"], "accn": last["accn"],
            "source": "SEC EDGAR XBRL (dei:EntityCommonStockSharesOutstanding)"}

def short():
    end = time.strftime("%Y-%m-%d"); start = time.strftime("%Y-%m-%d", time.localtime(time.time() - 120 * 86400))
    body = json.dumps({"limit": 20, "compareFilters": [{"compareType": "equal", "fieldName": "symbolCode", "fieldValue": "GME"}],
                       "dateRangeFilters": [{"fieldName": "settlementDate", "startDate": start, "endDate": end}]}).encode()
    rows = http("https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest", data=body,
                headers={"Content-Type": "application/json", "Accept": "application/json"})
    rows = sorted(rows, key=lambda x: x["settlementDate"])
    return {"rows": [{"date": r["settlementDate"], "short": r["currentShortPositionQuantity"],
                      "prev": r["previousShortPositionQuantity"], "adv": r["averageDailyVolumeQuantity"],
                      "dtc": r["daysToCoverQuantity"]} for r in rows],
            "source": "FINRA Consolidated Short Interest API"}

def filings():
    d = http("https://data.sec.gov/submissions/CIK0001326380.json")
    r = d["filings"]["recent"]; out = []
    for i in range(min(40, len(r["form"]))):
        acc = r["accessionNumber"][i].replace("-", "")
        out.append({"form": r["form"][i], "date": r["filingDate"][i], "desc": r["primaryDocDescription"][i],
                    "url": f"https://www.sec.gov/Archives/edgar/data/1326380/{acc}/{r['accessionNumber'][i]}-index.htm"})
    return {"filings": out, "source": "SEC EDGAR submissions API"}

class H(SimpleHTTPRequestHandler):
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if not u.path.startswith("/api/"):
            return super().do_GET()
        q = urllib.parse.parse_qs(u.query)
        key = u.path + "|" + q.get("range", [""])[0]
        try:
            if key in CACHE and time.time() - CACHE[key][0] < TTL:
                payload = CACHE[key][1]
            else:
                fn = {"/api/chart": lambda: chart(q.get("range", ["6mo"])[0]), "/api/shares": shares, "/api/short": short, "/api/filings": filings}.get(u.path)
                if not fn:
                    self.send_error(404); return
                payload = json.dumps(fn()).encode(); CACHE[key] = (time.time(), payload)
            self.send_response(200)
        except Exception as e:
            payload = json.dumps({"error": str(e)}).encode(); self.send_response(502)
        self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(payload)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f"Serving GME site on http://localhost:{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
