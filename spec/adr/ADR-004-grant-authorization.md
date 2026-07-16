# ADR-004 — Grant authorization

**Status:** Accepted (2026-07-16).

## Context
A grant conflates two distinct acts if signed once: the subject *consenting* and the issuer
*issuing*. Collapsing them destroys the evidence that consent was independently given.

## Decision
- **Two signatures per grant**, kept separate: a **consent** signature (subject / custodian) and
  an **issuance** signature (issuer). Both are required; neither implies the other.
- **Attenuation-only delegation:** a child grant may only narrow scope, never widen it.
- **`grant_id` doubles as `jti`** for replay protection.
- **`grantee_ref` is authenticated** — a grant is issued *to* a named, verifiable operator.

## Consequences
- Consent and issuance are independently auditable.
- Delegation chains are safe by construction; the effective horizon is the max over links.
