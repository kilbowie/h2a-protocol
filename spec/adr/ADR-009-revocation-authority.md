# ADR-009 — Revocation authority sits with the issuer, not the implementer

**Status:** Accepted (2026-07-17). Refines ADR-005 and ADR-006.

## Context
An implementer (Bridle) that exposes a revoke endpoint and signs the status list *is* the revocation
authority, whatever the org chart says. Possession of the signing key is the authority: whoever signs
the list can publish one with the bit cleared. That quietly preserves exactly the power the
issuer/implementer split exists to remove, and a union GC will see straight through it.

## Decision
Revocation authority lives entirely with the **issuer / fiduciary**, expressed as **custody of the
status-list signing key**:
- The issuer holds the private key, maintains the revoked set, and **signs** the status list.
  Revocation is: set the bit, re-sign, publish. The signed list **is** the revocation record.
- An implementer is **fetch-and-verify only**. It holds the issuer's **public key** as a trust
  anchor, fetches the signed list at the point of use, **verifies the signature**, reads the bit, and
  **fails closed** on an unreachable, unsigned, wrongly-signed, or stale list. It has **no revoke
  endpoint and serves no status list**.
- Consequently the status-list **signature is real from v0** (ES256), even while grant signatures
  remain stubbed until Sprint 1 — because this signature is what makes the authority split provable.

## Consequences
- The implementer can make a falsifiable claim: "we have no revoke capability — here is the code —
  the only way a use is refused is that we read the fiduciary's signed list."
- Breaking change to any implementer that previously owned `/revoke` or `/status`. Worth it: it is the
  actual proof, not a topology diagram.
- v0 caveat: with no fiduciary yet, the interim issuer is operated by the founder — but in a
  **separate trust domain** (separate process, separate credentials, ideally separate KMS key policy)
  from the implementer. The provable split arrives when a fiduciary holds the key.
