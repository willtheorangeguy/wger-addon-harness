# FAQ

???+ question "Do I need Python packages on the host?"

    No. The controller uses the standard library. Application setup, seeding and tests run in containers; the host needs Python 3.10+ and Docker Compose.

??? question "Why doesn't the fixture move to today's date on every run?"

    Its first end date is persisted in runtime state. Reruns retain it for repeatable data. Set `SEED_END_DATE` before the first seed, or deliberately reset the disposable scenario to choose another date.

??? question "Can I run both harnesses at the same time?"

    Yes. The supplied projects use distinct names and ports. A second copy of the same harness also needs unique project/app/addon port values and a matching `PUBLIC_URL`.

??? question "Does down remove my demo data?"

    No. It retains volumes and runtime state. `reset --yes` removes project volumes and regular generated files, while `.env` survives.

??? question "Why does a connector not export the default demo workout history?"

    The demo creates logs for six dates without timestamped WorkoutSession objects. Session-based connectors create dedicated eligible fixtures through their own integration runners.

??? question "Is the example addon a loader for every addon?"

    No. It is a separate Python HTTP service using the real API. Replace its service for an external addon; an upstream patch needs an application image/build override appropriate to that application.
