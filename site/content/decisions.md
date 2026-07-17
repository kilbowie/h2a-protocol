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

**Most recent.** [ADR-009](adr-009.html) moves revocation authority to the issuer and defines it as
custody of the status-list signing key: whoever signs the list can publish one with the bit cleared, so
possession of the key *is* the authority regardless of the org chart. An implementer is fetch-and-verify
only — it holds the issuer's public key, checks the signature, and fails closed on an unreachable,
unsigned, wrongly-signed, or stale list. It has no revoke endpoint and serves no list of its own.
