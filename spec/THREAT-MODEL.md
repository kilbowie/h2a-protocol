# H2A Threat Model — v0.1 (working draft)

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

## Stale / withheld status
An operator could serve or rely on an expired status list.
**Mitigation:** short-TTL signed lists; verifiers fail closed on expiry (SPEC-CORE §4.3).

## Namespace capture
An operator or implementer owning the identity root could rewrite identities.
**Mitigation (ADR-001):** key-bound URNs under a rights-holder / fiduciary root; implementer
operates endpoints via delegation but is never the root.
