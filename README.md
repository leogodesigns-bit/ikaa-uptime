# ikaa-uptime

Checks every 5 minutes (GitHub Actions) that Ikaa's shop, a product page, checkout and
invoices answer. After 2 failed checks in a row it sends one WhatsApp; another when the
site is back. `state.json` holds what is down; nothing private lives in this repository.

Once a day (09:00 IST) `certs.py` checks the HTTPS certificates of www., the apex, pay. and bill.
and the domain registration (RDAP). URGENT alert when a certificate expires in under 14 days or
the domain in under 30. Test: run the `certs` workflow by hand with `fake_now` (e.g. 2026-11-05).
Pushes go through `.githooks/pre-push` (`git config core.hooksPath .githooks` once per clone).
