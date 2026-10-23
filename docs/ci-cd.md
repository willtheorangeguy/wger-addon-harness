# CI/CD

`integration.yml` runs on pushes, pull requests and manual dispatch. Host unit
tests run on Ubuntu and Windows with Python 3.10 and 3.12:

```sh
python harness.py test-unit
```

A separate Ubuntu/Python 3.12 job starts the real Docker stack and verifies
repeat seeding, integration behavior, restart persistence and addon replacement:

```sh
python harness.py test
```

Each matrix job uploads `reports/unit.xml`. The Docker job uploads `reports/`
as `integration-reports` on success or failure and always attempts `down`.
Its timeout is 30 minutes. See [testing](testing.md) for coverage and report files.
Application images are pinned by digest. There is no harness image release workflow.

`docs-lint.yml` delegates Markdown, strict-build and link checks to the shared
MkDocs workflow on documentation PRs. `docs.yml` builds/deploys Pages on documentation
pushes and manual dispatch, independently of the Docker test services.
