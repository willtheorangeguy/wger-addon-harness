# wger addon testing harness

Run a disposable wger sandbox for addon development with a real application, PostgreSQL, seeded history, a working API-reading addon and containerized integration tests. The host controller needs only Python's standard library and Docker Compose.

## Key features

- Start a health-checked wger `2.8.0-dev.1` application from pinned images.
- Seed repeatable demo workout, measurement and nutrition history.
- Replace the sample addon with a Compose override and real API credentials.
- Run isolated API/addon checks and capture JUnit reports.

## Quick start

```sh
git clone https://github.com/willtheorangeguy/wger-addon-harness.git
cd wger-addon-harness
python harness.py up
python harness.py test
```

Open `http://localhost:8101` for the app and `http://localhost:9101` for addon JSON. Follow [getting started](getting-started.md) for prerequisites, demo login and expected results.

## Where to next

<div class="grid cards" markdown>

- [Installation](installation.md): host requirements and verification.
- [Configuration](configuration.md): ports, origins, credentials and seed dates.
- [Sample data](sample-data.md): exact fixture counts and boundaries.
- [Addon development](addon-development.md): overrides and replacement contracts.
- [Commands](commands.md): lifecycle and destructive reset behavior.
- [Architecture](architecture.md): controller, app, API client and test flow.

</div>

## Support

Open an [issue](https://github.com/willtheorangeguy/wger-addon-harness/issues/new/choose).
