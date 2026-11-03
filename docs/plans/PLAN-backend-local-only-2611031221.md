# Plan (bugfix): backend-local-only
Status: done 2026-11-03 (Daniel: "great idea", "pls do")

Departures: AGENTS.md Part B also carries a verify line (`present 'host="127.0.0.1"' in backend`), so the guard holds from both sides. The test first ran `main.py` with `uvicorn.run` replaced; CI failed it at import (its test requirements leave out uvicorn and the routers' packages), so it now reads the `uvicorn.run` call from the source, and AGENTS.md Part B records the trap.

## Why

Daniel asked whether he can view the dashboard from another machine on his network. Checking showed the backend listening on every interface (`host="0.0.0.0"` in `backend/main.py`), the Mac's firewall off and no route behind a login, so any device on the same network can already read students, transcripts and handouts straight from port 8001, while the page itself (Vite, localhost only) cannot be opened from elsewhere.

## Observed

- `lsof` shows Vite on `127.0.0.1:3000` and the backend on `*:8001`; the application firewall is disabled; no API route depends on a current user.
- The page calls relative `/api` URLs that Vite proxies to `localhost:8001` on the same Mac, so nothing legitimate needs the backend on the network.
- `backend/main.py` is the only place the backend's address is set; docker-compose and the start scripts do not set one.

## Assumed

- Nothing else (another app, a phone, a script on another machine) talks to port 8001 directly.

## Acceptance criteria

1. Started with `python main.py` (`start_backend.sh`, `start.sh`), the backend listens on `127.0.0.1:8001` only: a request to the Mac's network address on 8001 is refused, `localhost:8001` and the page at `localhost:3000` still work.
2. Viewing from another machine stays possible on demand: `cd frontend && npm run dev -- --host`, documented with the warning that, with no login, the page then exposes all data to the network through its proxy while it runs.
3. A revert to `0.0.0.0` turns a test red and fails the lint.

## Surface

- `backend/main.py`
- `backend/tests/test_main_binding.py`
- `AGENTS.md` (Part B, outside the managed block)
- `docs/ARCHITECTURE.md` (invariant)
- `NEXT-STEPS.md`
- this plan; the session log

## Design

- One line: `host="127.0.0.1"`. No setting: nothing needs another value, and a setting would make the open address one `.env` line away.
- Network viewing is not made the default: without a login, the proxy would re-expose everything whenever the dashboard runs. A login is a separate decision for Daniel.

## Test plan

- Unit, written first: `test_backend_listens_on_this_mac_only` asserts the host `main.py` passes to `uvicorn.run` is `127.0.0.1`. Red first against `0.0.0.0`.
- Claim: an invariant in the map with `verify: absent 'host="0.0.0.0"' in backend`.
- e2e: restart the backend; `lsof` shows `127.0.0.1:8001`; `curl` to the network address on 8001 is refused; `localhost:8001/health` and `localhost:3000/api/handouts/status` answer.

## Records

Architecture map delta: yes (one invariant). ADR: no (one-line hardening; the reasoning lives in the invariant and this plan).

Cross-repo impact: none.

## Open questions

- None open. Deferred to Daniel: a login, which is what would make network viewing safe to leave on.

## BACKLOG

- CORS lists `localhost:5173` and `FRONTEND_URL`; harmless, untouched.
