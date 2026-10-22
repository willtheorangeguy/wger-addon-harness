# Development

Use host Python 3.10+ and Compose v2.24.4+. No pip packages are needed for the controller or baseline standard-library tests. Start by validating CLI and Compose behavior:

```sh
python harness.py --help
python harness.py config
python harness.py test
```

Edit `scripts/` and `tests/` in the checkout; they are mounted read-only inside tools, so updated files are used on the next run. Extend `scripts/seed.py` with a synthetic scenario and add API assertions in `tests/test_*.py`. Keep normal reseeding anchored and preserve existing demo history during round-trip tests.

Use the [addon guide](addon-development.md) for replacement services or upstream image overrides. This harness has no universal in-process addon loader. Keep API credentials, generated `.env`, runtime files, reports and addon checkouts untracked.

## Documentation

With the shared MkDocs checkout beside this repository:

```sh
../mkdocs/scripts/docs-serve.sh --build
../mkdocs/scripts/docs-serve.sh
```

The inherited theme, plugins and dependencies live in [willtheorangeguy/mkdocs](https://github.com/willtheorangeguy/mkdocs). Declare identity/navigation here without overriding shared plugin or extension lists.
