# CI/CD

`integration.yml` runs on pushes, pull requests and manual dispatch. It checks out the repository, sets up host Python 3.12 and invokes the same controller used locally:

```sh
python harness.py test
```

On failure, it saves Compose logs to `reports/compose.log`. It uploads `reports/` as the `integration-reports` artifact regardless of success, then runs `python harness.py down` for cleanup. The job timeout is 25 minutes. Containers use pinned application image digests; there is no harness package/container release workflow.

`docs-lint.yml` delegates Markdown, strict-build and link checks to the shared MkDocs workflow on documentation PRs. `docs.yml` delegates build/deployment to Pages on main/master docs pushes and manual dispatch. Pages uses Actions as its build source, separate from application fixture services.
