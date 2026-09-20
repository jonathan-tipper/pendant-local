# Working on Pendant Local

Read `CONTRIBUTING.md`, `docs/ARCHITECTURE.md` and `docs/VALIDATION.md` before
changing behaviour. Read `docs/MAC_APP.md` for native lifecycle or packaging.

Use Python 3.11+ and the repository's existing FastAPI, SQLite and vanilla JS
structure. Both the Python dashboard and source-built Mac app use the same
backend and workspace format. There is no frontend build step.

Use work-type branches: `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`
or `infra/` followed by a lowercase kebab-case description. Do not prefix
branches with an agent, vendor or username.

Run focused tests and the full suite for a release. Check JavaScript with
`node --check src/pendant_api/ui/app.js` and release contents with
`python scripts/check_release.py`. Test services must use an isolated temporary
data directory and a separate port. Never print tokens, personal transcripts,
raw capture contents or keys. Never test against an owner's real workspace.

Preserve non-deleting dashboard sync, durable raw capture and journals, local
keys, authenticated `/v1` routes, loopback binding and text-only user rendering.
Do not download speech models as an installation side effect. Keep third-party
licences and protocol bindings. Hardware claims require physical hardware tests;
mocked transports or imported audio cannot establish them.

Publishing source does not authorise publishing user data or distributing a
native app. Follow `docs/RELEASING.md` and report the checks actually performed.
