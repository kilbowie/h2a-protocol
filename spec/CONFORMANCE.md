# H2A Conformance — v0.2 (working draft)

Conformance is honest by construction: a level claims only what it can prove.

## Levels
- **L1 — Verifiable.** Objects validate against the schemas; signatures verify; the verification
  algorithm (SPEC-CORE §4) is implemented and fails closed. Provable by the reference suite.
- **L2 — Attested.** L1 plus point-of-use attestations and Decision Records produced for every act,
  with a resolvable, short-TTL status list.
- **L3 — Anchored.** L2 plus external anchoring (ADR-005): eIDAS-qualified TSA timestamps and an
  independent witness co-signature. L3 is the level an underwriter can rely on.

## Test suite
`scripts/validate-schemas.py` gates schema + example conformance (positive and negative) and runs in
CI before every deploy. `reference/` provides the executable verification algorithm and the
permit / out-of-scope / revoked scenarios.

## Claim discipline
Until signature verification and anchoring are live in a given deployment, that deployment is L1 at
most. Do not claim "cryptographically verified" or "anchored" beyond what the deployment proves.
