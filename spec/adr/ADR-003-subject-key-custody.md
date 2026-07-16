# ADR-003 — Subject key custody

**Status:** Accepted (2026-07-16).

## Context
Performers will not, in general, run key management. Custody has to be real without pretending
the subject is operating HSMs.

## Decision
**Custodial-with-fiduciary** custody is the default for performers: the custodian holds the
subject's signing key under fiduciary oversight. Self-custody remains available for sophisticated
subjects. Custody model is recorded, not assumed.

## Consequences
- Usable by real performers on day one.
- The custodian's signature attests to an authorisation (see ADR-007); it never manufactures one.
