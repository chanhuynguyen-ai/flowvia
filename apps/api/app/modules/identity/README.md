# identity

Tenant/workspace, user, membership, session và role context.

## M1 implemented
- `User`, `Tenant`, `Membership`, `AuthSession` models.
- Personal/team workspaces.
- Argon2 passwords, opaque session token hash, CSRF validation.
- Login, `/auth/me`, workspace switch and logout.
- Active membership is rechecked on every authenticated request.
- Current tenant is derived from the session; inaccessible workspace switch returns 404.

This is the M1 web-session foundation, not full member administration/OIDC/credential grants. See `docs/06_BACKEND_DATABASE_AUTH.md` and `docs/09_M1_FOUNDATION.md`.
