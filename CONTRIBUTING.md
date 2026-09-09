# Contributing to Flowvia

## Before changing code

Read `PROJECT_CONTEXT.md` and the relevant document in `docs/`. Work within one vertical slice. Keep core workflow execution independent from the HR pack. Do not overwrite existing work with the original blueprint.

## Development workflow

1. Create a focused branch, for example `feat/workflow-runtime` or `docs/module-contracts`.
2. Implement the requested behavior and update related contracts and documents.
3. Run `python3 scripts/validate_blueprint.py` for blueprint changes.
4. Once application tooling exists, run the relevant lint, type, unit, integration and build checks documented with that implementation.
5. Open a pull request explaining the problem, change, verification and remaining limitations.

Suggested commit style: `feat(workflows): persist published versions`, `fix(approvals): reject duplicate decisions`, `docs(api): clarify mapping validation`. Avoid unrelated formatting changes in functional patches.

## Review expectations

- Include migrations for persisted changes and meaningful tests for authorization, state transitions and transaction rules.
- Add concrete screenshots for actual UI changes, with synthetic data.
- Keep credentials, raw candidate information and private conversation data out of commits and logs.
- Distinguish mock/dry-run behavior from live integrations.
- Update roadmap status only when behavior has been implemented and verified.

## Licensing

The repository does not yet specify a license. The owner should choose one before advertising open-source reuse or soliciting external code contributions under assumed terms.
