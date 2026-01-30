# CHANGELOG


## v0.0.0-rc.1 (2026-01-30)

### Chores

- Add pre-commit hooks configuration
  ([`caa8011`](https://github.com/jharibo/flowdoc/commit/caa8011a5a5a3daf848d687c643c8b2fc4f1a44c))

- Configure ruff formatting and linting hooks - Add standard pre-commit hooks for file quality -
  Helps catch issues before commit

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

- Set version to 0.0.0 for initial release
  ([`37a341d`](https://github.com/jharibo/flowdoc/commit/37a341d4324ec2843fbb908e03b37651cc9e0ea7))

Allows semantic-release to bump to 0.1.0a1 on first release

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

- Update dependency lock file
  ([`5119f4c`](https://github.com/jharibo/flowdoc/commit/5119f4c2d147d5f32b2aec518aa469fa934e8798))

Update uv.lock with python-semantic-release dependency

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

- Update project metadata for alpha release
  ([`8b62cc6`](https://github.com/jharibo/flowdoc/commit/8b62cc63426bd737bc25750d566277b906ea187e))

- Update author email to GitHub noreply address - Add project URLs (repository, homepage, issues,
  docs) - Bump version to 0.1.0a1 for first alpha release - Add python-semantic-release dependency -
  Configure semantic-release for version management

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

### Continuous Integration

- Add GitHub Actions workflows for CI and release
  ([`3c524cc`](https://github.com/jharibo/flowdoc/commit/3c524cc154d79bc511dc95969c776ca453ab9e5d))

- Add ci.yml workflow for testing across Python 3.10-3.13 - Add lint job with ruff formatting and
  type checking - Add release.yml workflow with manual trigger - Configure automated PyPI publishing
  with trusted publisher - Add release.yml for auto-generated release notes

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

- Update actions versions
  ([`d36bc89`](https://github.com/jharibo/flowdoc/commit/d36bc8943cc63f510f9f3750c2b1c5e39600faa7))

### Documentation

- Add CHANGELOG, CONTRIBUTING, and README improvements
  ([`cc34ea3`](https://github.com/jharibo/flowdoc/commit/cc34ea370f49cce49e47968a855560a6936d9781))

- Create CHANGELOG.md template for semantic-release - Add comprehensive CONTRIBUTING.md with
  conventional commits guide - Add badges to README (CI, PyPI version, Python versions, license) -
  Add troubleshooting section to README - Add link to FastAPI example in README - Create
  examples/README.md as an index of all examples

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

### Refactoring

- Use pre-commit in CI for all linters
  ([`e4103b0`](https://github.com/jharibo/flowdoc/commit/e4103b0ebfefbbc545d35fee517299c90dc39473))

- Consolidate all linters (ruff, ty) to run through pre-commit - CI now has single command:
  pre-commit run --all-files - Add ty check to pre-commit hooks (non-blocking for pre-existing
  issues) - Add file quality checks (trailing whitespace, EOF, yaml, toml) - Fix YAML indentation in
  release.yml

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

### Testing

- Improve CLI and parser test coverage
  ([`b169757`](https://github.com/jharibo/flowdoc/commit/b169757ca0c61c5ddd9d7261ad1511250c076505))

- Add CLI error-path tests (syntax errors, empty directories) - Add parser edge-case tests
  (namespaced decorators, bare decorators) - cli.py coverage improved from 85% to 94% - parser.py
  coverage improved from 91% to 98% - Total coverage improved from 94% to 98%

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

- Make version test more generic
  ([`448cdca`](https://github.com/jharibo/flowdoc/commit/448cdcab71077a0fc4755a5efdde80126d79572c))

Check for any version format instead of hardcoded 0.1.0 string

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
