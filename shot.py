import sys
from playwright.sync_api import sync_playwright
w = int(sys.argv[1]) if len(sys.argv) > 1 else 1280
out = sys.argv[2] if len(sys.argv) > 2 else 'preview.png'
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception: b = p.chromium.launch(channel='chrome')
    pg = b.new_page(viewport={'width': w, 'height': 900}, device_scale_factor=1)
    logs = []; pg.on('console', lambda m: logs.append(f'{m.type}: {m.text}')); pg.on('pageerror', lambda e: logs.append(f'PAGEERROR: {e}'))
    pg.goto('http://localhost:8080/', wait_until='networkidle'); pg.wait_for_timeout(2500)
    pg.add_style_tag(content='.orbit{animation:none!important}')
    pg.screenshot(path=out, full_page=True)
    for i in ['priceVal','chg','mcap','shares','si','siPct','dtc','priceStatus','filingsStatus']: print(i, '=>', pg.evaluate(f"document.getElementById('{i}')?.textContent"))
    print('\n'.join(logs)); b.close()
