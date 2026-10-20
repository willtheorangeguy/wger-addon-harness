# wger addon testing harness

Independent Docker Compose sandbox with a real application, PostgreSQL, sample data,
an API-reading example addon, and containerized integration tests. Requires Docker
Desktop (Linux containers), Compose v2.24.4+ and Python 3.10+ on the host; no pip install.

## Quick start

```powershell
cd wger-addon-harness
python harness.py up
python harness.py test
```

Application: http://localhost:8101

Example addon JSON: http://localhost:9101

Login: **demo** / **HarnessDemo123!**

The first command creates a local `.env` with generated service secrets, waits for
application readiness, seeds data, then starts the example addon. First startup may
take several minutes while images download and databases migrate. Both harnesses
can run at once; each owns its Compose network and volumes. Ports bind to loopback.
This is a development fixture with known demo credentials.

Pinned application: **wger 2.8.0-dev.1**, upstream image built 2026-10-19.
This is the current upstream development image, locked to its tested digest;
see `upstream.json` for the exact source revision. JWT/mobile sync is not configured.

## Standard commands

| Command | Result |
| --- | --- |
| `python harness.py up` | Start, wait, seed, and start example addon |
| `python harness.py seed` | Reapply sample data without normal duplicate creation |
| `python harness.py test` | Start/seed, run API integration tests and addon tests |
| `python harness.py status` | Show all services |
| `python harness.py logs` | Follow application logs |
| `python harness.py down` | Stop; retain data |
| `python harness.py reset --yes` | Delete this sandbox's volumes and generated state |
| `python harness.py config` | Validate Compose configuration |

After reset run `up` again. `.env` survives reset. To change ports, edit both
`APP_PORT` and `PUBLIC_URL` in `.env`. Keep the Compose project name unique when
copying this repo. Reset operates on that project, so never reuse a production name.

## Sample scenario

A demo user, 14 daily body-weight readings, a full-body routine with three exercises and a recovery day, and six workouts totaling 54 logged sets. A nutrition plan includes three sample ingredients, breakfast/lunch/dinner meals and 42 diary entries. The upstream bundled exercise catalog is available without a remote sync. The bootstrap admin uses the demo password.

The history ends on the first seed date and remains anchored on normal reruns.
For a fixed date, set `SEED_END_DATE=2026-10-20` before the first `up`.
Use reset to move an existing fixture to another date or start a clean scenario.
The wger seeder runs in a database transaction with stable keys.

## Developing addons

1. Clone your addon under `addons/my-addon`, or point a build context at another repo.
2. Copy `compose.addon.example.yaml` to `compose.override.yaml` and customize it.
3. Run `python harness.py up` to launch with the override.
4. Add `tests/test_your_addon.py`; run `python harness.py test`.

The default addon is a working Python service in `scripts/addon.py`. It calls the
real authenticated API and exposes a small JSON summary, demonstrating networking
and credentials. Its container receives `APP_URL`, `PUBLIC_URL`, `TARGET` and a
read-only `/runtime/credentials.json` mount. Use the token with `Authorization: Token <token>`.
Within the Compose network the API URL is `http://web:8000/api/v2/`.
The sample addon listens on port 8080 inside its container.

For more addon services, add services to the override and attach them to the default
network. Set dependencies and a readiness check appropriate to the addon. For an
in-process addon or upstream patch, override the application image/build and mount
the necessary code; these applications do not share a universal addon loader.
The example integration test expects the sample JSON contract; replace that test
when your addon has its own interface. Extend `scripts/seed.py` for extra scenarios.

## Tests and reproducibility

Tests check authenticated seeded data, unauthenticated rejection, a real write/read/
delete round-trip on an isolated historical date, and the example addon's API access.
Tests leave the demo history intact. Results are written to `reports/junit.xml`;
GitHub Actions runs the same command and uploads reports. Any failing command exits
nonzero. `tests/` and seed scripts are mounted read-only into disposable containers.

Application images are locked by digest in Compose after validation. Infrastructure
images use explicit version tags. To upgrade, update the image references as a pair
where appropriate, reset the disposable dataset, and run the full integration suite.
Generated secrets, API tokens, runtime journals and addon checkouts are ignored by Git.

## Upstream references

- [wger source](https://github.com/wger-project/wger) and [Docker deployment](https://github.com/wger-project/docker)
- [Compose startup dependencies](https://docs.docker.com/compose/how-tos/startup-order/)

PowerSync/mobile offline synchronization, external provider accounts, SMTP and paid
AI integrations are outside this baseline fixture. Browser UI is available for
manual addon checks; automated checks exercise the APIs and example addon.
