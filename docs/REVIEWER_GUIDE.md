# Reviewer guide

## Reading path

Start with the root README for scope and current status, then inspect the artifacts below. M1 application source now exists, but M1 remains in progress until the Docker/frontend-lock/CI gates in `09_M1_FOUNDATION.md` are verified. M2 runtime and later product behavior remain blueprint work.

| Competency area | Artifact | What to inspect | Missing implementation evidence |
| --- | --- | --- | --- |
| Product decomposition | 02_PRODUCT_SPECIFICATION.md | Personas, rules, beta acceptance and exclusions | User feedback and actual beta outcomes |
| Modular architecture | 03_TECHNICAL_ARCHITECTURE.md | Core/pack boundaries, runtime and trade-offs | Dependency boundaries enforced in code |
| API/data modeling | 06_BACKEND_DATABASE_AUTH.md | Ownership, uniqueness and transactions | M1 migration + identity tests exist; M2+ domain transaction tests remain |
| Low-code contracts | ../packages/contracts/ | JSON envelope, manifest, example graph | Full semantic validation and handlers |
| Reliability | 04_APPLICATION_FLOW.md | Restart, duplicates, ambiguous delivery and conflicts | Recovery and concurrency tests |
| UI design | 05_UI_UX_GUIDE.md | Canvas structure, mapping and state feedback | M1 shell exists; canvas, screenshots and accessibility checks remain |
| Delivery discipline | 07_IMPLEMENTATION_PLAN.md | Vertical slices and measurable gates | M1 source/tests exist; external CI history and release evidence remain |

## Existing validation

Run `python3 scripts/validate_blueprint.py` from the repository root. It checks the sample graph structurally and detects unresolved documentation placeholders. Read its code to understand its limits: it is not a production workflow validator and does not perform permission checks.

## Future demonstration path

When M2 is implemented, the first demo should create a workflow through the editor, publish it, run a manual input, wait for approval, restart the worker, and resume exactly one approved mock action. It should also demonstrate rejection and cross-workspace denial. HR integrations come after this core path.

## Honest evidence

Do not add screenshots of nonexistent features, passing test badges before a run exists, fabricated benchmark numbers, or completion ticks based solely on written plans. Commit history should describe actual changes. Document assistance and authorship accurately when discussing the project; artifacts alone do not establish who independently performed each task.
