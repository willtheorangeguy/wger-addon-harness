# API

The harness exposes the real upstream application's API through its frontend and a separate read-only JSON addon. `harness.py` is a host CLI; it does not implement an application API.

## Example addon

| Field | Contract |
| --- | --- |
| Method/path | GET `/` (the implementation handles GET on any path). |
| Authentication | No incoming addon authentication; it reads source credentials from the read-only runtime mount. |
| Success | HTTP 200 with snapshot JSON. |
| Failure | HTTP 503 with `{"error":"message"}` when snapshot reads raise an exception. |
| Port | Internal 8080; host `127.0.0.1:9101` by default. |

```sh
curl --fail http://localhost:9101/
```

The response includes `platform`, `weight_entries`, `routines` and `latest_weight`. `latest_weight` is an upstream object or null, and counts reflect the returned API page.

Example field subset for a fixture ending on 2026-10-20 (the actual upstream object includes additional fields):

```json
{"platform":"wger","weight_entries":14,"routines":1,"latest_weight":{"weight":"81.09"}}
```

## Application API

The internal origin is `http://web:8000`. Use the `token` from the runtime credentials file in `Authorization: Token`. The snapshot reads `/api/v2/weightentry/?limit=100` and `/api/v2/routine/?limit=100`. Tests additionally inspect workout/nutrition logs and perform an isolated weight-entry create/read/delete.

The client sends `PUBLIC_URL` as its Origin header. Health readiness uses `/api/v2/version/` on web/frontend. Private source requests without credentials are expected to fail with HTTP 401 or 403 in the tests.

For a live contract, inspect the pinned upstream application. The fixture's [client](https://github.com/willtheorangeguy/wger-addon-harness/blob/HEAD/scripts/client.py) and [tests](https://github.com/willtheorangeguy/wger-addon-harness/blob/HEAD/tests/test_harness.py) show the exact consumed routes and assertions.
