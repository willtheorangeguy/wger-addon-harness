# Local validation — 2026-10-20

Validated on Docker Desktop 4.72.0, Linux containers, Compose 5.1.3 and Windows.

- Started from new PostgreSQL/static/media volumes with `python harness.py up`.
- Repeated seeding retained exactly 14 weights, 54 workout sets, six workout
  sessions and 42 nutrition diary entries.
- `python harness.py test`: all five integration tests passed; results in
  the ignored `reports/junit.xml` file.
- Confirmed the HTTP frontend and its CSS assets return 200.
- Submitted the real login form using demo credentials; reached `/en/dashboard`
  with an authenticated session cookie.
- Validated the example Compose addon override using `docker compose config`.
- Ran concurrently with the SparkyFitness harness; that harness's reset left
  this application running with its dataset intact.
- Workout-specific API checks confirm six training dates, three exercises,
  54 ten-rep sets, and a 12.5 kg increase per exercise across the history.

The image is upstream's pinned 2.8.0-dev.1 build. It emits an upstream warning
about pending model changes in exercises/gallery. The harness uses the migrations
shipped in that image; it does not generate migrations. Mobile JWT/PowerSync,
external integrations, and visual browser automation are not covered.
