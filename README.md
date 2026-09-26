# payments-demo

A small FastAPI payments service used as the target app for [Control Coverage](https://github.com/oplatechie/control-coverage), a TrueForge agent that turns bank security controls into tests and checks each release against them.

**This is demo code with intentional gaps. Do not use it in production.**

## What it does

- `POST /payments`, `GET /payments/{id}`, `GET /payments`: merchant payments (bearer token). Card numbers are exchanged for a token by a stand-in vault; only the token and last 4 digits are stored.
- `POST /admin/login`, `POST /admin/login/verify`: admin login with password, then a one-time code as the second factor.
- `GET /admin/merchants`: admin-only.
- Every read of payment or merchant data writes an `audit_log` row.

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q                      # unit tests + control tests
.venv/bin/uvicorn app.main:app --reload  # http://localhost:8000/docs
```

## Layout

```
app/            service code
tests/          unit tests written by the team
controls/       created by Control Coverage: control tests and per-app config
conftest.py     fixtures shared by tests/ and controls/tests/
testkit.py      helpers (card-number detection, login-code extraction)
```

## AI assistance

Built with help from Claude Code (Anthropic).
