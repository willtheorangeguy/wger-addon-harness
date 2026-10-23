# Getting started

## Prerequisites

Install Docker Desktop with Linux containers or Docker Engine, Docker Compose v2.24.4+ and host Python 3.10+. Host Python needs no pip packages. Check the versions:

```sh
python --version
docker compose version
```

## Install

```sh
git clone https://github.com/willtheorangeguy/wger-addon-harness.git
cd wger-addon-harness
```

## First run

```sh
python harness.py up
python harness.py test
```

Application: `http://localhost:8101`

Example addon JSON: `http://localhost:9101`

Demo username: **`demo`**

Demo password: **`HarnessDemo123!`**

These are the default credentials. If you change `DEMO_PASSWORD` in `.env`, use that value instead.

The first command creates a local `.env` with generated service secrets, waits for
application readiness, seeds data, then starts the example addon. First startup may
take several minutes while images download and databases migrate. Both harnesses
can run at once; each owns its Compose network and volumes. Ports bind to loopback.
This is a development fixture with known demo credentials.

Pinned application: **wger 2.8.0-dev.1**, upstream image built 2026-10-19.
This is the current upstream development image, locked to its tested digest;
see `upstream.json` for the exact source revision. JWT/mobile sync is not configured.

Check services and run the test command after startup:

```sh
python harness.py status
python harness.py test
```

Success means the application and example-addon services are healthy and the unittest runner exits zero. Test results are written to `reports/junit.xml`. The real application's first startup can take several minutes.

## What just happened

The controller generated `.env` only if it was absent, created runtime/report directories, started the health-checked application stack, seeded its demo account, and launched a read-only API addon. Application images are pinned to the revision recorded in `upstream.json`.

## Next steps

- Review [sample data](sample-data.md) for dates and expected counts.
- Customize [addon development](addon-development.md) without using production state.
- Read [configuration](configuration.md) before changing ports or project names.
- Use [deployment](deployment.md) to stop, retain or reset the disposable sandbox.
