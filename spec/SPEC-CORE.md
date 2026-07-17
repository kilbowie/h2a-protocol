# H2A Core Specification — v0.2 (working draft)

> **Working draft.** The v0.x wire format may change. v1.0 will freeze the Grant, Attestation,
> Decision Record, and Status List formats (see GOVERNANCE.md, gate G4). Do not present H2A as a
> ratified standard while this banner stands.

H2A is a neutral, open standard for the **consent, attestation, and revocation** of AI-generated
likeness (H2A-Media) and AI memory (H2A-Memory). H2A **evidences; it does not enforce** (ADR-006):
it produces a signed account of whether each act of use was conformant, and records non-conformant
transmissions explicitly so they become admissible evidence.

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted as in RFC 2119.

## 1. Objects

| Object | Purpose | Schema |
|---|---|---|
| **Grant** | Authority for a grantee to use a subject within a bounded scope, revocable at point of use | `h2a-core.grant.schema.json` |
| **Attestation** | Signed receipt of one act of use, binding output to grant and to the point-of-use check | `h2a-core.attestation.schema.json` |
| **Decision Record** | Signed record of a conformant / non-conformant transmission decision | `h2a-core.decision-record.schema.json` |
| **Status List** | Static, signed revocation artefact | `h2a-core.status-list.schema.json` |

Profiles (`h2a-media`, `h2a-memory`) are asset-bound and apply only when a Grant lists them.

## 2. Identity (ADR-001)

Identities are self-certifying, key-bound URNs. A Grant's `iss` **MUST** resolve under a
rights-holder or fiduciary namespace. It **MUST NOT** resolve under the operator's domain and
**SHOULD NOT** resolve under the implementer's domain. Endpoints **MAY** be operated by an
implementer via DNS delegation, but the implementer is never the identity root. No identity
resolution is on the runtime critical path.

## 3. Authorization (ADR-004)

A Grant **MUST** carry exactly two detached signatures with distinct roles: `consent` (subject or
custodian) and `issuance` (issuer). A verifier **MUST** validate both. `grant_id` **MUST** be
unique and serves as the replay-protection `jti`. `grantee_ref` **MUST** be an authenticated
operator identity.

Delegation is **attenuation-only**: a child Grant **MUST NOT** widen scope, extend the validity
window, or raise the lease cap beyond its parent. The **effective chain horizon is the maximum over
all links** — a chain is only as revocable as its slowest link.

## 4. Verification algorithm (normative)

A conformant verifier **MUST** perform, in order, failing closed at the first failure:

1. **Signatures.** Verify `consent` and `issuance` over the canonical Grant (all fields except the
   signature values). Either missing or invalid → refuse.
2. **Validity window.** `nbf ≤ now ≤ exp`, else refuse.
3. **Status.** Fetch `status.uri` (or any `status.mirrors` entry). The verifier **MUST** verify the
   status list's signature against the issuer's public key and **MUST** fail closed if the list is
   unreachable, unsigned, wrongly signed, or expired (`now > valid_until`). If the Grant's
   `status.index` bit is set → `REFUSED_REVOKED`. The verifier is **fetch-and-verify only**: it is
   never the revocation authority and serves no status list of its own (ADR-009).
4. **Scope.** The requested purpose **MUST** be in `scope.purposes`, **MUST NOT** be in
   `scope.exclusions`; territory **MUST** be permitted (or `GLOBAL`).
5. **Lease.** If present, `now` within the lease window and cumulative spend ≤ `cap`.

On success the verifier emits `PERMITTED_CONFORMANT`; otherwise the matching `REFUSED_*`. The
reference implementation in `reference/` is the executable form of this section.

## 5. The point-of-use rule

A check **MUST** be performed at the point of use and **MUST NOT** be cached. A permit is valid
only for the act it was issued against. Revocation takes effect at the next check; the declared
`revocation_horizon` is the single conformance dial bounding the window from revocation to the
non-conformant-transmission cutoff.

**Revocation authority (ADR-009).** Revocation is exercised by the issuer / fiduciary, as custody of
the status-list signing key: to revoke is to set the bit, re-sign, and publish. An implementer only
fetches and verifies that signed list. An implementer **MUST NOT** expose a revoke capability or sign
a status list; if it could, it would be the revocation authority regardless of intent.

## 6. Evidence, not enforcement (ADR-006)

H2A does not stop a third-party executor. When a transmission occurs outside conformance, the
verifier records a `TRANSMITTED_NON_CONFORMANT` Decision Record with a populated
`non_conformant_transmission` object. This record is the standard's commercial output: the
signed, externally-anchored account a counterparty relies on.

## 7. Anchoring (ADR-005)

Decision Records **SHOULD** be anchored with an RFC 3161 (eIDAS-qualified) timestamp and an
independent witness co-signature on the chain head. Anchoring **MUST** stay off the runtime
critical path. No distributed-ledger / blockchain anchoring is used.

## 8. Cryptography (ADR-008)

ES256 (ECDSA P-256) is mandatory-to-implement. The `alg` header makes the format curve-agnostic;
a verifier **MAY** support additional algorithms but **MUST** support ES256.
