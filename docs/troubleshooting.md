# Troubleshooting

## Harness failed with Docker or Compose errors

Confirm Docker is running in Linux-container mode and Compose is at least v2.24.4. Inspect the merged configuration and service logs:

```sh
python harness.py config
python harness.py status
python harness.py logs
```

The first startup can take several minutes for image downloads and migrations. Check the failing service's health/logs before resetting data.

## Port already allocated or browser origin rejected

Choose unused `APP_PORT` and `ADDON_PORT` values and change `PUBLIC_URL` with the frontend port. Give parallel copies unique `COMPOSE_PROJECT_NAME` values. Inside containers use `http://web:8000` for source calls, not host localhost.

## Login or API authentication fails

Use the demo username and the password configured in `.env`. API addons read `token` and send `Authorization: Token` from `/runtime/credentials.json`. An existing `.env` is never regenerated automatically; confirm it contains actual generated secret values rather than untouched placeholders.

## Demo history looks empty

Choose the end date recorded in runtime credentials. The fixture remains anchored across normal reruns. Run `seed` with the existing application available, then `test` to check the expected counts. Session-based consumers need explicit session fixtures beyond the demo logs.

## Replacement addon fails the default tests

The supplied assertion expects the sample JSON snapshot contract and internal port 8080. Update that test for your interface, override the inherited command/working directory, and add a readiness check suitable for the replacement service.

## reset requires confirmation

`reset` without `--yes` exits with an argument error. Only use `python harness.py reset --yes` after verifying the intended sandbox project. It deletes that project's volumes; use `down` when you need to retain data.
