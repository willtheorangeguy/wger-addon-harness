# Commands

The host controller requires Python 3.10+ and Docker Compose. Run commands from the checkout; the controller changes to its own directory. Every parsed command initializes `.env` if absent and creates runtime/report directories. `--help` exits before initialization.

## `up`

Start/health-wait application services, seed, then start the example addon.

```sh
python harness.py up
```

## `seed`

Run the one-shot seed service against the available application. It expects the existing stack.

```sh
python harness.py seed
```

## `test`

Start/wait, seed twice and verify stable fixtures, run integration tests, verify restart persistence, and build/check the supplied replacement addon. See [testing](testing.md).

```sh
python harness.py test
```

## `status`

Show Compose services across all profiles, including exited tool containers.

```sh
python harness.py status
```

## `logs`

Follow service logs with the last 100 lines.

```sh
python harness.py logs
```

## `down`

Stop/remove all-profile containers and retain volumes.

```sh
python harness.py down
```

## `config`

Initialize local files, then validate the merged Compose configuration.

```sh
python harness.py config
```

## `reset --yes`

Delete this project’s volumes and regular generated runtime/report files; retain .env.

```sh
python harness.py reset --yes
```

## Flags and exits

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--yes` | flag | off | Required for destructive `reset`; example `python harness.py reset --yes`. |
| `--help` | flag | off | Print command/flag choices without initializing the sandbox. |

Failed Compose commands or missing Docker exit 1. Invalid CLI arguments and `reset` without confirmation exit 2. Successful commands exit zero. A failed test container makes `test` fail; it does not automatically stop the application stack.

## `test-unit`

Run the host controller, HTTP-client and JUnit unit suites without Docker or credentials:

```sh
python harness.py test-unit
```

## `test-override`

Start/seed twice, verify fixture stability, build/check the supplied addon, and restore your original addon:

```sh
python harness.py test-override
```
