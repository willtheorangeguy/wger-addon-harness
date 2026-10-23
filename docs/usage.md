# Usage

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

## Inspect results

```sh
python harness.py status
curl --fail http://localhost:9101/
```

The sample addon performs authenticated source reads on each GET. A successful request returns JSON; API failure produces HTTP 503 with an error object. `status` includes tool profiles, so an exited seed/test container is expected after its one-shot command completes.

## State ownership

`down` retains data. Keep runtime files together with application database volumes, especially the anchored seed dates. `reset --yes` removes volumes for the configured Compose project, including override services that belong to it. `.env` survives reset. Read [deployment](deployment.md) before using reset.
