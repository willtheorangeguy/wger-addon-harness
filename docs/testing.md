# Testing

All three addon harnesses use the same controller, API client, JUnit reporter,
host unit suite, integration contract, and CI matrix. Platform adapters retain
each application's authentication, fixtures, and API behavior.

## Run the suites

```sh
python harness.py test-unit
python harness.py test
python harness.py test-override
```

`test-unit` runs 42 standard-library tests without Docker, `.env`, or host pip
packages. They cover controller paths and overrides, secret generation and
preservation, reset safeguards, failure diagnostics, HTTP authentication and
cookies, JSON/multipart requests, pagination, and JUnit failure/error/skip reporting.
The directory-symlink check skips on hosts that cannot create symlinks.

`test` starts the real application stack, seeds twice and compares fixture IDs,
dates and semantic values, then runs the containerized integration suite. It
captures fixture state, restarts application services, waits for health, and
compares persisted data again. Finally it builds the supplied standalone addon,
replaces the running default addon, checks its real authenticated API results,
and restores your original addon configuration. Each audit fails the command
when values differ. Compose logs are collected even if startup or tests fail.

`test-override` runs startup, reseed, and replacement-addon checks without the
full integration suite or restart audit. Neither command changes your local
`compose.override.yaml`. The supplied replacement is verified even when
`CHECK_EXAMPLE_ADDON=false` skips assertions about a custom addon's interface.

Local runs retain the sandbox for inspection. CI uses a fresh checkout and stops
the stack after collecting reports. Round-trip tests delete the records they
create and preserve the seeded history. These tests use synthetic data and local
credentials. Frontend HTML and real HTTP login are tested; browser automation
and production identity providers are outside this suite.

## Shared coverage

The 13 common integration tests check application health, frontend HTML, valid
login with private-data access, invalid login, missing/invalid API credentials,
authenticated fixture access, reseed equality, frozen dates, unique record IDs,
addon snapshots, credential redaction, and missing-resource responses.

| Harness | Host unit tests | Common integration tests | Platform integration tests | Total integration tests |
| --- | --- | --- | --- | --- |
| Dreeve | 42 | 13 | 13 | 26 |
| wger | 42 | 13 | 10 | 23 |
| SparkyFitness | 42 | 13 | 10 | 23 |

Reseed, restart, and addon replacement are additional workflow gates. Their
results are separate JSON reports rather than extra unittest cases.

## Platform coverage

The ten wger-specific tests cover fourteen weight measurements and their
progression, six strength-training dates with 54 logged sets, exercise progression,
42 nutrition entries with three meals each day, pagination without lost/duplicate
IDs, create/read/update/delete round trips, and rejected malformed weight data.
Real login uses the app's headless authentication endpoint and verifies that its
issued JWT can read private data. API-token authentication is checked separately.
The controller generates a local RSA JWT keypair required by the pinned wger image.

## Reports

| File under `reports/` | Contents |
| --- | --- |
| `unit.xml` | Host unit results, durations, failures, errors and skips |
| `junit.xml` | Containerized integration results in the same format |
| `api-snapshot.json` | Synthetic data read from the application's API |
| `seed-before.json`, `seed-idempotence.json` | Fixture state and comparison after the second seed |
| `restart-before.json`, `restart-idempotence.json` | Fixture state and comparison across application restart |
| `override.json` | Data returned by the verified replacement addon |
| `compose.log` | Compose diagnostics, collected on success and failure |

Reports exclude runtime credentials. Keep generated `.env`, `runtime/`, reports
and local addon checkouts out of Git. CI uploads reports even when checks fail.

## Extend the suite

Add host tests under `tests/unit/test_*.py` and HTTP integration tests under
`tests/integration/test_*.py`. The shared runner discovers them and adds JUnit
results automatically. Scripts and integration tests are mounted read-only into
the test container. Preserve fixture dates and remove temporary API records in
`finally` blocks so reruns remain useful.

For a custom addon interface, set `CHECK_EXAMPLE_ADDON=false` in `.env` and add
your own integration assertions. Application, authentication, persistence and
supplied replacement-addon checks still run. Extend the Compose override with
mock upstream services when your addon needs an external API.

## CI matrix

Every push and pull request runs host tests on Ubuntu and Windows with Python
3.10 and 3.12, plus the full Docker workflow on Ubuntu/Python 3.12. Unit artifacts
have a distinct name for each OS/Python combination. Integration reports are
uploaded as `integration-reports`. The Docker job has a 30-minute timeout and
always attempts sandbox shutdown.
