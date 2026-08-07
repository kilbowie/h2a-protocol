# Decisions

Architecture Decision Records are the durable record of *why* H2A is shaped the way it is. Each one is
locked: superseding a decision means a new ADR, not an edit to an old one. The specification states the
rule; the ADR states the reasoning and what it cost.

| # | Decision | Status |
|---|---|---|
| [ADR-001](adr-001.html) | Identity namespace root | Accepted — production namespace is open gate **G1** |
| [ADR-002](adr-002.html) | Enrollment identity-assurance tiers | Accepted |
| [ADR-003](adr-003.html) | Subject key custody | Accepted |
| [ADR-004](adr-004.html) | Grant authorization | Accepted |
| [ADR-005](adr-005.html) | Ledger external anchoring | Accepted |
| [ADR-006](adr-006.html) | H2A evidences; it does not enforce | Accepted — supersedes the earlier gate / kill-switch framing |
| [ADR-007](adr-007.html) | Consent-capture ceremony | Accepted |
| [ADR-008](adr-008.html) | Signing curve | Accepted |
| [ADR-009](adr-009.html) | Revocation authority sits with the issuer, not the implementer | Accepted — refines ADR-005 and ADR-006 |
| [ADR-010](adr-010.html) | Trust-anchor governance: pinned by namespace, foundation-bound | Accepted |
| [ADR-011](adr-011.html) | Commercial model: governed act billed, assurance-priced | Accepted |
| [ADR-012](adr-012.html) | Exposure fields are an optional profile, never Core | Accepted |
| ADR-013 | *Reserved — executor tiers T0–T3* | Not yet written |
| [ADR-014](adr-014.html) | Canonical form and signature encoding | Accepted |

**Most recent.** [ADR-014](adr-014.html) makes **RFC 8785 JCS** the normative canonical form and
fixes `alg: "ES256"` as the JOSE raw R‖S encoding, never DER. It exists because measurement found
four canonicalisers and two signature encodings across implementations that all believed they
agreed — and the two non-conforming ones were wrong in disjoint ways, so each matched the other on
ordinary payloads and diverged only on real ones: a name carrying a diacritic, a lease cap written
`500.0` rather than `500`. The ADR ships **normative test data**
([`interop/vectors/`](https://github.com/kilbowie/h2a-protocol/tree/main/interop)) anchored to
RFC 8785's own published sample. An implementation is conformant if and only if it reproduces every
vector byte-for-byte; prose describes the canonical form, the vectors decide it.

ADR-013 is deliberately absent, not missing — it is reserved for the executor-tier decision.
