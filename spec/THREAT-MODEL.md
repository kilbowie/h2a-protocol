# H2A Threat Model — v0.2 (working draft)

[TOC]

## What this model is defending against, and why it is not a design preference

The threats below are not hypotheticals chosen for engineering interest. Synthetic-media systems
process faces and voices, which are **biometric data**, and two statutory obligations attach to that
processing. Both are obligations to *demonstrate* something, and neither can be met by an
architecture that merely intends to behave well.

| Obligation | What it demands | Why documents do not satisfy it |
|---|---|---|
| **[GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj) Art 7(1)** · **[BIPA](https://www.ilga.gov/legislation/ilcs/ilcs3.asp?ActID=3004) §15(b)** | The controller **must be able to demonstrate** that the data subject consented — for the processing that occurred | A signed release shows consent existed on the day it was signed. It cannot show consent was still live at 14:03:11 when a particular render ran. The obligation attaches to the **act**, not to the relationship. |
| **GDPR Art 7(3)** | The data subject has the right to withdraw consent **at any time**, and it must be **as easy to withdraw as to give** | Withdrawal that takes effect at the next quarterly reconciliation is not withdrawal at any time. If a running job cannot be interrupted, and no artefact records when it stopped, the right is nominal. |

This is why the standard is shaped the way it is, and it explains two decisions that otherwise look
like over-engineering:

- **The point-of-use rule** (SPEC-CORE §5) and the ban on caching a permit exist because Art 7(1)
  attaches to each act of processing. A check performed once and reused is evidence about the first
  act only.
- **The revocation horizon** (the single conformance dial) exists because Art 7(3) is a claim about
  *elapsed time*. An unbounded horizon is a system that cannot say when withdrawal took effect,
  which is indistinguishable from one where it did not.

It also explains why H2A **evidences rather than enforces** (ADR-006). Neither statute requires that
a controller be technically incapable of unlawful processing; both require that it be able to
demonstrate what happened. A signed, externally-anchored account of every act — including the
non-conformant ones — discharges an evidential obligation. A system that claimed to make
non-conformant transmission impossible would be claiming something it could not prove, and the claim
would fail at exactly the moment it mattered.

> **Consequence for the consent ceremony.** Whether an *agency custodian's* signature constitutes
> valid consent under Art 7 for biometric data is a live question, not a settled one (D-F records
> the interim answer: custodian at P1, subject device key at P2). `consent_signature_kind` exists so
> that which of the two happened is recorded on every grant rather than inferred later.
>
> **Lineage.** This framing is brought forward from `ARCHIVE/remit/README.md` (the predecessor
> project), where it was the stated motivation but lived only in a README. It is normative context
> for the threats below, so it belongs in the specification rather than in a repository that has
> been archived. Neither statute is quoted in full; both are cited so a reader can check the claim
> rather than take it. **This is engineering rationale, not legal advice.**

## Self-serving record
A Decision Record signed only by the party it exonerates is weak. Two attacks cannot be caught from
the record alone:
- **Backdating** — claiming an older beacon than the recorder actually held.
- **Hidden work** — omitting acts from the record.

**Mitigation (ADR-005):** external anchoring — an
[eIDAS](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0910)-qualified TSA timestamp
plus an independent witness co-signature on an append-only chain head — provides an external time the
recorder cannot forge, closing both attacks. Kept off the runtime critical path.

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
