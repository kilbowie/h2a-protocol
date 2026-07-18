# ADR-001 — Identity namespace root

**Status:** Accepted (2026-07-16). Production namespace selection is gate **G1**.

## Context
`iss` and `subject_ref` identify who a grant is *from* and *about*. Whoever owns that
namespace root owns the identities. If the operator or the implementer owns it, the
standard is not neutral and portability breaks the moment a subject changes operator.

## Decision
- Identities are **self-certifying, key-bound URNs** (`urn:h2a:subject:…`, `urn:h2a:grantee:…`).
- The namespace **root is owned by the rights-holder or a fiduciary** (a union or collective
  management organisation (CMO)). It **MUST NOT** resolve under the operator's domain and
  **SHOULD NOT** resolve under the implementer's domain.
- **The implementer operates the resolution endpoints** under the fiduciary's domain via DNS
  delegation — it runs the plumbing, it is never the identity root.
- **Nothing in this chain sits in the runtime hot path.** Resolution is cache-friendly and static.
- An interim issuer domain, outside both operating companies, is used until a fiduciary adopts the root.

## Consequences
- Portability falls out for free: the same grant verifies at any conformant operator.
- Adopting a fiduciary later is a delegation change, not a redesign.
- **G1 action:** pick the interim production namespace before issuing any real grant.
