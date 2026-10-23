# Sample data

## Workout data

Log in as `demo`, open Workouts and select **Harness Full Body**. It contains three
exercises, three sets of ten reps per exercise, a recovery day, and **six workout dates (54 logged sets)**. Logged weights increase by 2.5 kg per session
so addons can test workout history, training volume, and progression.

Workout dates are 12, 10, 8, 5, 3 and 0 days before the fixture's end date, which
is recorded in `runtime/credentials.json`. The latest workout is on that end date.

A demo user, 14 daily body-weight readings, a full-body routine with three exercises and a recovery day, and six workouts totaling 54 logged sets. A nutrition plan includes three sample ingredients, breakfast/lunch/dinner meals and 42 diary entries. The upstream bundled exercise catalog is available without a remote sync. The bootstrap admin uses the demo password.

The history ends on the first seed date and remains anchored on normal reruns.
For a fixed date, set `SEED_END_DATE=2026-10-20` before the first `up`.
Use reset to move an existing fixture to another date or start a clean scenario.
The wger seeder runs in a database transaction with stable keys.

## Timestamped session objects

The default seeder creates `WorkoutLog` rows for six dates but does not create `WorkoutSession` objects or link logs to a session. Session-based connectors therefore need their own dedicated fixtures. The connector integration runners create those accounts/workouts separately; the demo's 54 logs alone are not a completed-session export fixture.

## Inspect the fixture

```sh
python harness.py seed
python harness.py test
```

Use the fixture end date from the ignored credentials file to choose diary/history dates. Normal reseeding stays anchored; moving to a different date requires a deliberate clean scenario. Test round-trips use `2001-01-01` to avoid changing the visible demo history.
