#!/usr/bin/env python3
"""Alert on every channel we have, each independent of the others:

  notify.py "<what happened>" "<details>" [--urgent]

  1. WhatsApp through Setu's owner-alert queue (free inside the 24h window; quiet
     hours 10 PM-8 AM except --urgent); if Setu can't be reached, straight through
     Meta's Cloud API (wa-alert.py; template WA_TEMPLATE)
  2. Email through Gmail's SMTP server (independent of Meta and of Railway)
     Env: SMTP_USER (the Gmail address), SMTP_APP_PASSWORD (a Google app password),
          ALERT_EMAIL (where to send; default SMTP_USER). Skipped when not set.
Exit 0 when at least one channel delivered."""
import datetime, os, smtplib, subprocess, sys
from email.message import EmailMessage

urgent = '--urgent' in sys.argv
args = [a for a in sys.argv[1:] if a != '--urgent']
what, details = (args[:2] + ['', ''])[:2]
here = os.path.dirname(os.path.abspath(__file__))
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%d %b %Y, %H:%M IST')
run = os.environ.get('GITHUB_RUN_URL') or (
    f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    if os.environ.get('GITHUB_RUN_ID') else '')
ok = []

# WhatsApp: through Setu's owner-alert queue first (free inside the 24-hour window,
# a Utility template only for urgent alerts when it is closed, 10 PM - 8 AM only
# urgent ones, each alert once). Only if Setu can't be reached (e.g. Railway down),
# straight through Meta (wa-alert.py) so the alert still gets out.
def via_setu():
    url, secret = os.environ.get('SETU_OWNER_ALERT_URL'), os.environ.get('SETU_SEND_SECRET')
    if not (url and secret): return False
    import json, urllib.request
    body = {'secret': secret, 'tenant_slug': os.environ.get('SETU_TENANT', 'ikaa'), 'kind': os.environ.get('ALERT_KIND', 'ops'),
            'urgent': urgent, 'text': f"{what}: {details}"[:2900], 'dedupe_key': (os.environ.get('GITHUB_RUN_ID', '') + ':' + what)[:120]}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.loads(r.read()); print('setu owner-alert:', j); return j.get('ok') is True
    except Exception as e:  # noqa: BLE001
        print('setu owner-alert FAILED:', type(e).__name__, str(e)[:200]); return False

if via_setu():
    ok.append('whatsapp (Setu queue)')
elif os.environ.get('WA_TOKEN'):
    r = subprocess.run([sys.executable, os.path.join(here, 'wa-alert.py'), what, details])
    if r.returncode == 0: ok.append('whatsapp')

user, pw = os.environ.get('SMTP_USER'), os.environ.get('SMTP_APP_PASSWORD')
if user and pw:
    msg = EmailMessage()
    msg['Subject'] = f'[Ikaa alert] {what}'
    msg['From'] = f'Ikaa monitoring <{user}>'
    msg['To'] = os.environ.get('ALERT_EMAIL') or user
    msg.set_content(f"{what}\n\n{details}\n\nTime: {now}\n" + (f"Run: {run}\n" if run else '')
                    + "\nThis is an automatic message from Ikaa's monitoring (GitHub Actions).\n")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as s:
            s.login(user, pw.replace(' ', ''))
            s.send_message(msg)
        ok.append('email'); print('email sent to', msg['To'])
    except Exception as e:  # noqa: BLE001
        print('email FAILED:', type(e).__name__, str(e)[:200])

print('delivered via:', ', '.join(ok) or 'NOTHING')
sys.exit(0 if ok else 1)
