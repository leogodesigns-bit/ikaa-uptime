#!/usr/bin/env python3
"""Daily (GitHub Actions): do the HTTPS certificates and the domain registration have time left?
URGENT alert when a certificate expires in under 14 days (or can't be read/verified), or the
domain (GoDaddy; read from the public RDAP registry) in under 30 days. Every alert repeats the
domain expiry date. FAKE_NOW=2026-12-10 pretends it is that day (to test the alert)."""
import datetime, json, os, socket, ssl, subprocess, sys, urllib.request

HOSTS = ['www.ikaajewellery.com', 'ikaajewellery.com', 'pay.ikaajewellery.com', 'bill.ikaajewellery.com']
DOMAIN, CERT_DAYS, DOMAIN_DAYS = 'ikaajewellery.com', 14, 30
UTC = datetime.timezone.utc

def cert_expiry(host):
    with socket.create_connection((host, 443), timeout=20) as sock:
        with ssl.create_default_context().wrap_socket(sock, server_hostname=host) as s:
            c = s.getpeercert()
    issuer = dict(x[0] for x in c['issuer'])
    return datetime.datetime.fromtimestamp(ssl.cert_time_to_seconds(c['notAfter']), UTC), issuer.get('organizationName', '?')

def domain_expiry():
    with urllib.request.urlopen(f'https://rdap.verisign.com/com/v1/domain/{DOMAIN}', timeout=20) as r:
        ev = {e['eventAction']: e['eventDate'] for e in json.load(r)['events']}
    return datetime.datetime.fromisoformat(ev['expiration'].replace('Z', '+00:00'))

def main():
    fake = os.environ.get('FAKE_NOW')
    now = datetime.datetime.fromisoformat(fake).replace(tzinfo=UTC) if fake else datetime.datetime.now(UTC)
    problems = []
    try:
        dexp = domain_expiry(); ddays = (dexp - now).days
        dline = f'Domain {DOMAIN} (GoDaddy) expires {dexp:%d %b %Y} ({ddays} days).'
        if ddays < DOMAIN_DAYS: problems.append(f'domain {DOMAIN} expires in {ddays} days — renew at GoDaddy')
    except Exception as e:  # noqa: BLE001
        dline = f'Domain expiry unknown (RDAP lookup failed: {type(e).__name__}).'
    print(dline)
    for h in HOSTS:
        try:
            exp, issuer = cert_expiry(h); days = (exp - now).days
            print(f'{h}: {issuer}, expires {exp:%d %b %Y} ({days} days)')
            if days < CERT_DAYS: problems.append(f'{h} certificate ({issuer}) expires {exp:%d %b %Y}, in {days} days')
        except Exception as e:  # noqa: BLE001
            print(f'{h}: FAILED {e}')
            problems.append(f'{h} certificate could not be checked: {type(e).__name__}: {str(e)[:120]}')
    if problems:
        what = ('TEST ' if fake else '') + 'URGENT: SSL/domain expiring for ikaajewellery.com'
        details = '; '.join(problems) + '. ' + dline + (f' (Test run pretending today is {fake}.)' if fake else '')
        print('ALERT:', what, '—', details)
        if os.environ.get('WA_TOKEN') or os.environ.get('SMTP_USER') or os.environ.get('SETU_SEND_SECRET'):
            subprocess.run([sys.executable, 'notify.py', what, details, '--urgent'])
        return 1
    return 0

sys.exit(main())
