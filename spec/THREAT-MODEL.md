# H2A Threat Model — v0.2 (working draft)

[TOC]

## Self-serving record
A Decision Record signed only by the party it exonerates is weak. Two attacks cannot be caught from
the record alone:
- **Backdating** — claiming an older beacon than the recorder actually held.
- **Hidden work** — omitting acts from the record.

**Mitigation (ADR-005):** external anchoring — an eIDAS-qualified TSA timestamp plus an independent
witness co-signature on an append-only chain head — provides an external time the recorder cannot
forge, closing both attacks. Kept off the runtime critical path.

## Fabricated consent
A custodian could assert consent that never happened.
**Mitigation (ADR-007):** the subject authorises via an authenticated, challenge-bound
`CONSENT_CAPTURE` interaction; the custodian's signature attests to it and never manufactures it.

## Stale, forged, or withheld status
An operator could serve or rely on an expired status list, or an implementer could forge one with the
revoked bit cleared — a permit that never expires is a revocation that never lands.
**Mitigation:** short-TTL lists signed by the issuer; verifiers verify the signature against the
issuer's key and fail closed on an unreachable, unsigned, wrongly-signed, or expired list
(SPEC-CORE §4.3).

## Implementer as revocation authority
An implementer that signs the status list or exposes a revoke endpoint **is** the revocation
authority, whatever the topology diagram says: possession of the signing key is the authority, and
whoever holds it can publish a list with the bit cleared. This silently preserves the exact power the
issuer/implementer split exists to remove.
**Mitigation (ADR-009):** the status-list signing key stays in the issuer / fiduciary trust domain.
Implementers are fetch-and-verify only and hold only the public key — a claim falsifiable by reading
their code, not by trusting their org chart. Residual risk at v0: no fiduciary exists yet, so the
interim issuer is founder-operated in a separate trust domain; the split becomes provable only when a
fiduciary holds the key.

## Namespace capture
An operator or implementer owning the identity root could rewrite identities.
**Mitigation (ADR-001):** key-bound URNs under a rights-holder / fiduciary root; implementer
operates endpoints via delegation but is never the root.
