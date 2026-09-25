#!/usr/bin/env python3
"""WhatsApp alert straight through Meta's Cloud API (no Railway app in the path).

  wa-alert.py "<what happened>" "<details>"

Env: WA_TOKEN, WA_PHONE_NUMBER_ID, ALERT_TO (comma-separated, e.g. 919403345612).
Template ikaa_ops_alert (Utility, en): What happened {{1}} / Details {{2}} / Time {{3}}."""
import datetime, json, os, sys, urllib.request

what, details = (sys.argv[1:3] + ['', ''])[:2]
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%d %b %Y, %H:%M IST')
clip = lambda s: (s or '-').replace('\n', ' ').strip()[:900] or '-'
ok = True
for to in [t.strip() for t in os.environ['ALERT_TO'].split(',') if t.strip()]:
    body = {'messaging_product': 'whatsapp', 'to': to, 'type': 'template', 'template': {
        'name': os.environ.get('WA_TEMPLATE', 'ikaa_ops_alert'), 'language': {'code': 'en'},
        'components': [{'type': 'body', 'parameters': [{'type': 'text', 'text': clip(what)}, {'type': 'text', 'text': clip(details)}, {'type': 'text', 'text': now}]}]}}
    req = urllib.request.Request(f"https://graph.facebook.com/v21.0/{os.environ['WA_PHONE_NUMBER_ID']}/messages", data=json.dumps(body).encode(),
                                 headers={'Authorization': 'Bearer ' + os.environ['WA_TOKEN'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print('whatsapp sent to …' + to[-3:], json.loads(r.read()).get('messages', [{}])[0].get('id', '')[:12])
    except Exception as e:  # noqa: BLE001 — report and carry on to the next number
        ok = False
        print('whatsapp FAILED to …' + to[-3:], getattr(e, 'read', lambda: b'')()[:300])
sys.exit(0 if ok else 1)
