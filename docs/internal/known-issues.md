# Known Issues — wger-addon-harness

Concrete defects and gaps found while writing this repository's documentation.
**Nothing here was changed** — each one needs a code, configuration, or
licensing decision rather than a documentation one.

Ordered by severity. See [`docs/roadmap.md`](../roadmap.md) for the narrative version,
which also covers deliberate non-goals.

**2 open:** 2 medium.

## 1. Runtime directory is writable by every local user — RESOLVED

**Resolution:** Generated directories use mode 2770 and the host group, Compose helpers join that group, and credential files use mode 660 with a restrictive seed umask.

**Severity:** Medium
**Where:** `harness.py:init()`; `scripts/seed.py`

**What:** Initialization applies chmod(0o777) to runtime and reports. The seed writes the demo password and API credential in runtime without explicitly restricting file permissions.

**Why it matters:** Other local users can replace runtime state or credentials through the world-writable directory; default umasks can also allow reading the API credential.

**Suggested fix:** Choose an explicit container UID/GID or shared group, restrict the runtime directory and credential file, and test Docker read/write access on supported hosts.

## 2. Default history lacks timestamped workout session objects

**Severity:** Medium
**Where:** `scripts/seed.py:46–62`; `tests/integration/test_platform.py:test_strength_workout_history`

**What:** The seeder creates WorkoutLog records for six dates but never creates WorkoutSession records or sets the logs’ session relation. The baseline assertion groups log dates rather than checking session objects.

**Why it matters:** Addons consuming timestamped workout sessions cannot use the default history as a completed-session fixture, despite the older README and validation record describing six sessions.

**Suggested fix:** Add six explicit completed sessions, link their logs, and assert the session endpoint and relationships. Keep dedicated connector fixtures separate to preserve test isolation.
