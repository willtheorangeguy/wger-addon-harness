# Addon development

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

## Override example

Copy the tracked example and edit it for an existing addon checkout:

```sh
cp compose.addon.example.yaml compose.override.yaml
python harness.py config
python harness.py up
```

```yaml title="compose.override.yaml"
# Copy to compose.override.yaml. This replaces the working example addon.
services:
  example-addon:
    image: my-fitness-addon:local
    build:
      context: ./addons/my-addon
    command: !reset null
    working_dir: !reset null
    # Set an appropriate readiness check for your addon.
    healthcheck:
      disable: true
    # Inherited: APP_URL, TARGET, PUBLIC_URL, /runtime mount, port 8080.
    # Your addon must listen on 0.0.0.0:8080, or override ports too.

```

The build context must exist before startup. `!reset` removes the sample command and working directory inherited from the base file. The example disables the inherited healthcheck; add a check appropriate to your addon. Listen on `0.0.0.0:8080` or change the inherited port mapping. The controller includes only `compose.override.yaml` automatically.

## Credentials and tests

Read the mounted credentials file and use the source's actual authentication scheme. Do not commit it or copy demo credentials into production. The default test suite expects the sample JSON contract. Replace that assertion when changing the addon interface, and add your tests under `tests/test_*.py` so the containerized unittest discovery includes them.
