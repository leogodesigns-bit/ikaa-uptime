#!/usr/bin/env python3
"""Every 5 minutes (GitHub Actions): is each Ikaa site up? A site counts as down after 2
failed checks in a row; then one WhatsApp, and one more when it is back. State is kept
in state.json, committed by the workflow only when something changes (plus a monthly
keep-alive commit, so GitHub never disables the schedule for inactivity)."""
import json, os, subprocess, sys, time, datetime, urllib.request

CHECKS = [
    ('Website home', 'https://www.ikaajewellery.com/', None),
    ('Product page', 'https://www.ikaajewellery.com/products/IK-EAR-036', None),
    ('Website + database', 'https://www.ikaajewellery.com/api/health', 'ok'),
    ('Checkout (pay.)', 'https://pay.ikaajewellery.com/health', 'ok'),
    ('Invoices (bill.)', 'https://bill.ikaajewellery.com/health', 'status'),
]
STATE = 'state.json'

def check(url, key):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'ikaa-uptime/1 (+github actions)', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read(200000)
            if r.status != 200: return False, f'HTTP {r.status}'
            if key:
                j = json.loads(body)
                if j.get(key) not in (True, 'ok'): return False, f'health says {j.get(key)!r}'
            return True, f'{round((time.time() - t0) * 1000)} ms'
    except urllib.error.HTTPError as e:
        return False, f'HTTP {e.code}'
    except Exception as e:  # noqa: BLE001
        return False, type(e).__name__ + ': ' + str(e)[:120]

def alert(what, details, urgent=False):
    print('ALERT:', what, '—', details)
    if os.environ.get('WA_TOKEN') or os.environ.get('SMTP_USER') or os.environ.get('SETU_SEND_SECRET'):
        # Site down is urgent (goes at once, day or night); back up is not.
        subprocess.run([sys.executable, 'notify.py', what, details] + (['--urgent'] if urgent else []))   # WhatsApp + email

def main():
    try: state = json.load(open(STATE))
    except Exception: state = {}
    now = datetime.datetime.now(datetime.timezone.utc)
    before = json.dumps(state, sort_keys=True)
    for name, url, key in CHECKS:
        ok, info = check(url, key)
        if not ok:   # one retry a little later, so a single blip is not a failed check
            time.sleep(20); ok, info = check(url, key)
        s = state.setdefault(url, {'fails': 0, 'alerted': False, 'down_since': None})
        print(('UP  ' if ok else 'DOWN'), name, url, info)
        if ok:
            if s['alerted']:
                mins = round((now - datetime.datetime.fromisoformat(s['down_since'])).total_seconds() / 60) if s['down_since'] else '?'
                alert(f'{name} is back up', f'{url} answers again ({info}); it was down about {mins} min.')
            s.update(fails=0, alerted=False, down_since=None)
        else:
            s['fails'] += 1
            s['down_since'] = s['down_since'] or now.isoformat(timespec='seconds')
            if s['fails'] >= 2 and not s['alerted']:
                alert(f'{name} is down', f'{url}: {info} ({s["fails"]} checks in a row).', urgent=True)
                s['alerted'] = True
    last = state.get('_keepalive')
    if not last or (now - datetime.datetime.fromisoformat(last)).days >= 30:
        state['_keepalive'] = now.isoformat(timespec='seconds')
    if json.dumps(state, sort_keys=True) != before:
        json.dump(state, open(STATE, 'w'), indent=1, sort_keys=True)
        print('state changed')

main()
