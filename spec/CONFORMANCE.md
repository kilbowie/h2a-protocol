# H2A Conformance — v0.3 (working draft)

Conformance is honest by construction: a level claims only what it can prove.

## Levels
- **L1 — Verifiable.** Objects validate against the schemas; signatures verify; the verification
  algorithm (SPEC-CORE §4) is implemented and fails closed. Provable by the reference suite.
- **L2 — Attested.** L1 plus point-of-use attestations and Decision Records produced for every act,
  with a resolvable, short-TTL, **signed** status list whose signature the verifier checks against the
  issuer's key. The verifier is fetch-and-verify only and is never the revocation authority (ADR-009);
  a reference issuer/status service lives in `reference/issuer-service/`.
- **L3 — Anchored.** L2 plus external anchoring (ADR-005):
  [eIDAS](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0910)-qualified TSA
  timestamps and an independent witness co-signature. L3 is the level an underwriter can rely on.

<!--DIAGRAM:conformance-ladder-->

## Profiles are not required for conformance
Conformance is defined entirely over Core objects. **A Core-conformant implementation is not required
to support any profile** (`h2a-media`, `h2a-memory`, or `h2a-commercial`). A verifier **MUST** ignore
profile fields it does not recognise (SPEC-CORE §1). In particular, a commercial implementer's
exposure/pricing fields (`h2a-commercial`, SPEC-COMMERCIAL) are outside the conformance surface by
construction (ADR-012).

## One ladder, viewed two ways
The commercial **assurance level** (SPEC-COMMERCIAL) is the *same* L1/L2/L3 ladder defined here, not a
second axis: **L1 = Verifiable = software attestation, L2 = Attested = witnessed attestation,
L3 = Anchored = enclave attestation** (ADR-011). The conformance level is the technical claim a
deployment can prove; the assurance level is that same claim priced. A grant MUST NOT declare an
assurance level above what the deployment proves — the claim-discipline rule below applies to both.

## Test suite
`scripts/validate-schemas.py` gates schema + example conformance (positive and negative) and runs in
CI before every deploy. `reference/` provides the executable verification algorithm and the
permit / out-of-scope / revoked scenarios.

## Claim discipline
Until signature verification and anchoring are live in a given deployment, that deployment is L1 at
most. Do not claim "cryptographically verified" or "anchored" beyond what the deployment proves.
