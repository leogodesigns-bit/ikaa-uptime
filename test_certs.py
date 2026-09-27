#!/usr/bin/env python3
"""Self-check for certs.py against the live certificates, with fake dates and no alert secrets."""
import os, subprocess, sys
env = {k: v for k, v in os.environ.items() if k not in ('WA_TOKEN', 'SMTP_USER', 'SETU_SEND_SECRET')}
def run(now): return subprocess.run([sys.executable, 'certs.py'], env={**env, 'FAKE_NOW': now}, capture_output=True, text=True)
calm, near, dom = run('2026-09-01'), run('2027-06-01'), run('2027-09-10')   # if the domain is renewed past 2028, move these dates
assert calm.returncode == 0, calm.stdout            # far from every expiry: no alert
assert near.returncode == 1 and 'certificate' in near.stdout and 'renew at GoDaddy' not in near.stdout, near.stdout
assert dom.returncode == 1 and 'renew at GoDaddy' in dom.stdout, dom.stdout   # < 30 days to 2 Oct 2027
print('certs.py self-check OK')
