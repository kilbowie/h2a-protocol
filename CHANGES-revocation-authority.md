# Change: revocation authority moves to the issuer (ADR-009)

**Date:** 2026-07-17 · **Scope:** h2a-protocol (spec + reference)

## Why
An implementer that signs the status list or exposes a revoke endpoint *is* the revocation authority,
because possession of the signing key is the authority. Keeping that with the implementer preserves
the exact power the issuer/implementer split exists to remove. Authority is key custody, not org chart.

## What changed
- **New ADR-009** — revocation authority sits with the issuer/fiduciary as custody of the status-list
  signing key; implementers are fetch-and-verify only.
- **SPEC-CORE §4.3** now requires verifying the status-list **signature** and failing closed on an
  unreachable / unsigned / wrongly-signed / stale list; **§5** states implementers MUST NOT revoke or
  sign a status list.
- **CONFORMANCE L2** updated to require signed-list verification.
- **New `reference/issuer-service/`** — a zero-dependency reference issuer/status service that holds
  the signing key, serves the signed list, and is the only component that can revoke.
- **Python reference** (`reference/h2a_ref`) now verifies the status-list signature (`status_pubkey`).

## Impact
Additive to the standard; implementers must add signed-list verification and drop any revoke/status
serving. See the sibling repos' change notes.
