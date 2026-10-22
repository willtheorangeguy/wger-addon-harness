<!-- Logo -->
<h1 align="center">wger addon testing harness</h1>
<!-- Tagline -->
<h4 align="center">Run a seeded wger Docker sandbox with a real API, example addon and containerized integration tests.</h4>
<!-- Badges -->
<div align="center">
<img alt="Issues" src="https://img.shields.io/github/issues/willtheorangeguy/wger-addon-harness">
<img alt="Pull requests" src="https://img.shields.io/github/issues-pr/willtheorangeguy/wger-addon-harness">
<img alt="License" src="https://img.shields.io/github/license/willtheorangeguy/wger-addon-harness">
<img alt="docs-lint workflow" src="https://github.com/willtheorangeguy/wger-addon-harness/actions/workflows/docs-lint.yml/badge.svg">
<img alt="docs workflow" src="https://github.com/willtheorangeguy/wger-addon-harness/actions/workflows/docs.yml/badge.svg">
<img alt="integration workflow" src="https://github.com/willtheorangeguy/wger-addon-harness/actions/workflows/integration.yml/badge.svg">
</div>
<!-- Nav -->
<p align="center"><a href="#key-features">Key Features</a> • <a href="#installation">Installation</a> • <a href="#usage">Usage</a> • <a href="#documentation">Documentation</a> • <a href="#support">Support</a> • <a href="#license">License</a></p>

## Key Features

- Run pinned wger `2.8.0-dev.1` with PostgreSQL and health checks.
- Seed six strength-training dates, 54 logged sets and nutrition/measurement history.
- Read the authenticated real API through a working Python addon.
- Replace addon services with an automatically included Compose override.
- Run containerized integration checks and save JUnit reports.

## Installation

Requires Docker Desktop/Linux containers, Compose v2.24.4+ and host Python 3.10+. No pip installation is needed.

```sh
git clone https://github.com/willtheorangeguy/wger-addon-harness.git
cd wger-addon-harness
python harness.py up
```

First startup creates local secrets and seeds the demo account. See [getting started](docs/getting-started.md).

## Usage

```sh
python harness.py test
python harness.py status
python harness.py down
```

Application: `http://localhost:8101`. Example addon: `http://localhost:9101`.
Demo username: **`demo`**; password: **`HarnessDemo123!`** unless changed in `.env`.
`down` retains data; `reset --yes` deletes this sandbox's volumes and generated files. Keep the project name unique.

## Documentation

Read the [documentation site](https://williamvdg.me/wger-addon-harness/) or browse [`docs/`](docs/index.md):
[Getting started](docs/getting-started.md) · [Installation](docs/installation.md) · [Usage](docs/usage.md) · [Configuration](docs/configuration.md) · [Troubleshooting](docs/troubleshooting.md).

## Attribution

Runs the upstream [wger](https://github.com/wger-project/wger) application. Exact source/image references are recorded in [upstream.json](upstream.json).

## Support

Open an [issue](https://github.com/willtheorangeguy/wger-addon-harness/issues/new/choose).

## Contributing

Contributions welcome. See the org-wide [Contributing Guide](https://github.com/willtheorangeguy/.github/blob/main/CONTRIBUTING.md) and [Code of Conduct](https://github.com/willtheorangeguy/.github/blob/main/CODE_OF_CONDUCT.md).

## License

MIT — see [`LICENSE.md`](LICENSE.md). Upstream application images retain their own licenses.
