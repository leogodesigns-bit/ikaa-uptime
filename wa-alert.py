#!/usr/bin/env python3
"""WhatsApp alert straight through Meta's Cloud API (no Railway app in the path).

  wa-alert.py "<what happened>" "<details>"

Env: WA_TOKEN, WA_PHONE_NUMBER_ID, ALERT_TO (comma-separated, e.g. 919403345612).
Template: WA_TEMPLATE, default ikaa_new_order_alert (the approved Utility template;
ikaa_ops_alert and ikaa_store_status_update came back Marketing and are not used)."""
import datetime, json, os, sys, urllib.request

what, details = (sys.argv[1:3] + ['', ''])[:2]
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%d %b %Y, %H:%M IST')
clip = lambda s: (s or '-').replace('\n', ' ').strip()[:900] or '-'
ok = True
for to in [t.strip() for t in os.environ['ALERT_TO'].split(',') if t.strip()]:
    name = os.environ.get('WA_TEMPLATE') or 'ikaa_new_order_alert'
    if name == 'ikaa_new_order_alert':
        # The approved UTILITY template (store alerts are never Marketing, so "Stop
        # promotions" can never silence them). Its slots carry the alert:
        # "New Ikaa website order {{1}} for Rs{{2}}. Items: {{3}} City: {{4}} Delivery: {{5}}"
        params = ['(store alert, not an order) ' + clip(what)[:150], '0', clip(details), now, 'Ikaa monitoring: see the details above']
        comps = [{'type': 'body', 'parameters': [{'type': 'text', 'text': t} for t in params]},
                 {'type': 'button', 'sub_type': 'url', 'index': '0', 'parameters': [{'type': 'text', 'text': 'c0'}]}]
    else:
        comps = [{'type': 'body', 'parameters': [{'type': 'text', 'text': clip(what)}, {'type': 'text', 'text': clip(details)}, {'type': 'text', 'text': now}]}]
    body = {'messaging_product': 'whatsapp', 'to': to, 'type': 'template', 'template': {
        'name': name, 'language': {'code': 'en'}, 'components': comps}}
    req = urllib.request.Request(f"https://graph.facebook.com/v21.0/{os.environ['WA_PHONE_NUMBER_ID']}/messages", data=json.dumps(body).encode(),
                                 headers={'Authorization': 'Bearer ' + os.environ['WA_TOKEN'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print('whatsapp sent to …' + to[-3:], json.loads(r.read()).get('messages', [{}])[0].get('id', '')[:12])
    except Exception as e:  # noqa: BLE001 — report and carry on to the next number
        ok = False
        print('whatsapp FAILED to …' + to[-3:], getattr(e, 'read', lambda: b'')()[:300])
sys.exit(0 if ok else 1)
