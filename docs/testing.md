# Testing

Tests check authenticated seeded data, unauthenticated rejection, a real write/read/
delete round-trip on an isolated historical date, and the example addon's API access.
Tests leave the demo history intact. Results are written to `reports/junit.xml`;
GitHub Actions runs the same command and uploads reports. Any failing command exits
nonzero. `tests/` and seed scripts are mounted read-only into disposable containers.

Application images are locked by digest in Compose after validation. Infrastructure
images use explicit version tags. To upgrade, update the image references as a pair
where appropriate, reset the disposable dataset, and run the full integration suite.
Generated secrets, API tokens, runtime journals and addon checkouts are ignored by Git.

## Run the suite

```sh
python harness.py test
```

Five baseline tests cover fixture visibility, strength history/progression, example-addon source access, private-data authentication and an isolated write/read/delete round-trip. Tests discover additional `test_*.py` files under the mounted directory. The report contains one testcase per discovered test plus failure/error details.

`test` starts/seeds the sandbox and leaves it available for inspection. It uses no production provider credentials. The UI is available for manual checks; browser automation is not part of this baseline suite. Historical [validation](https://github.com/willtheorangeguy/wger-addon-harness/blob/HEAD/VALIDATION.md) records its original environment and results.
