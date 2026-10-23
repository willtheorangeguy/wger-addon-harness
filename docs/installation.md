# Installation

## Requirements

Use Docker Desktop in Linux-container mode or Docker Engine, Compose v2.24.4+ and Python 3.10+ on the host. Compose's reset-tag syntax is used by the addon override example. No host pip installation is required: seeding and API tests run in containers.

The pinned application is wger `2.8.0-dev.1`. The image digests and exact source revision live in [upstream.json](https://github.com/willtheorangeguy/wger-addon-harness/blob/HEAD/upstream.json). Infrastructure images use explicit version tags.

<!-- markdownlint-disable MD046 -->

## Source checkout

=== "macOS / Linux"

    ```sh
    git clone https://github.com/willtheorangeguy/wger-addon-harness.git
    cd wger-addon-harness
    python3 harness.py up
    ```

=== "Windows"

    ```powershell
    git clone https://github.com/willtheorangeguy/wger-addon-harness.git
    Set-Location wger-addon-harness
    py harness.py up
    ```

The host only orchestrates Docker. There is no published harness Python package or standalone harness executable.

## Verify the installation

```sh
python harness.py config
python harness.py status
python harness.py test
```

`config` exits zero when Compose validates. `status` shows all profiles, including stopped tool containers. `test` exits zero on successful seeded API/addon checks and writes JUnit XML. Open the application at `http://localhost:8101` and the example addon at `http://localhost:9101`.

## Upgrading

Update application image references and `upstream.json` together. Review related frontend/server or worker references as a set. Reset only the disposable dataset, start again, and run the full integration suite. Existing validation records apply to their recorded image digests.

## Uninstalling

`python harness.py down` stops/removes this project's services and retains volumes, `.env` and runtime state. `reset --yes` is destructive: it removes project volumes and generated files. Confirm the project is the intended sandbox before resetting. See [deployment](deployment.md).
