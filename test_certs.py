#!/usr/bin/env python3
"""Self-check for certs.py against the live certificates and domain, with no alert secrets.
Fake dates are derived from the real expiries, so renewals never break it."""
import datetime, os, subprocess, sys
from certs import HOSTS, CERT_DAYS, DOMAIN_DAYS, cert_expiry, domain_expiry
env = {k: v for k, v in os.environ.items() if k not in ('WA_TOKEN', 'SMTP_USER', 'SETU_SEND_SECRET')}
def run(now): return subprocess.run([sys.executable, 'certs.py'], env={**env, 'FAKE_NOW': now.date().isoformat()}, capture_output=True, text=True)
day = datetime.timedelta(days=1)
cert, dom = min(cert_expiry(h)[0] for h in HOSTS), domain_expiry()
calm = run(min(cert - (CERT_DAYS + 2) * day, dom - (DOMAIN_DAYS + 2) * day))   # before every alert window
near = run(cert - 5 * day)                                                   # soonest certificate inside 14 days
late = run(dom - 10 * day)                                                   # domain inside 30 days
assert calm.returncode == 0, calm.stdout
assert near.returncode == 1 and 'certificate' in near.stdout, near.stdout
if dom - cert > (DOMAIN_DAYS + 5) * day:   # usual case: the domain outlives the certificates by far
    assert 'renew at GoDaddy' not in near.stdout, near.stdout
assert late.returncode == 1 and 'renew at GoDaddy' in late.stdout, late.stdout
print('certs.py self-check OK')
