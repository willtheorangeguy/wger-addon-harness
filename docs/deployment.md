# Deployment

This harness is a disposable local development stack. Host application and addon ports bind to `127.0.0.1`; internal addon clients use Compose service names.

## Start and inspect

```sh
python harness.py up
python harness.py status
python harness.py logs
```

`up` waits for application health for up to 600 seconds, seeds, then starts the addon profile. `logs` follows the last 100 lines plus new logs until interrupted. The pinned wger image is `2.8.0-dev.1`; review [upstream.json](https://github.com/willtheorangeguy/wger-addon-harness/blob/HEAD/upstream.json) for the digest and source revision.

## Stop and retain data

```sh
python harness.py down
```

This removes containers for all profiles, retaining database/application volumes, generated runtime files, reports and `.env`. Preserve them together to retain a reproducible fixture.

## Reset the sandbox

!!! danger
    `reset --yes` deletes volumes belonging to `COMPOSE_PROJECT_NAME`, including services added by the local override. Verify that this is a unique sandbox project and preserve anything you need first.

```sh
python harness.py reset --yes
python harness.py up
```

Reset removes regular files in `runtime/` and `reports/` except `.gitkeep`; nested directories remain. `.env` and the override survive. To choose a new fixture date, edit `SEED_END_DATE` before the next seed.

## Parallel harnesses

The two supplied harnesses use different project names, volumes and host ports. To duplicate one, give the copy a unique project name plus unused app/addon ports. Change `PUBLIC_URL` with `APP_PORT`. Local `localhost` inside a container means that container, not the application.
