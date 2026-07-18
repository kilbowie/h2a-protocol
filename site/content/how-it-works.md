# How H2A works

A visual walkthrough of the protocol, in the order the pieces come into play. Each diagram is a
picture of a rule stated normatively elsewhere — follow the links to the authoritative text. Colour is
consistent throughout: **green** is a pass / permitted path, **red** is a fail / refused one, and
**blue** marks informational or neutral machinery.

<!--DIAGRAM:legend-->

## The four objects

Everything in H2A hangs off one object, the **Grant**. Three records bind back to it, and it points
forward to the artefact that can revoke it.

<!--DIAGRAM:object-map-->

Full definitions live in the [core specification](spec-core.html#1-objects) and the generated
[schema reference](schemas.html).

## What a grant carries

A grant is only valid if two independent parties have signed it — the subject (or their custodian)
consents, and the issuer issues. Neither signature implies the other.

<!--DIAGRAM:two-signatures-->

See [authorization](spec-core.html#3-authorization-adr-004) (ADR-004).

## Delegation only narrows

A grant can be delegated, but never widened. A child is always a subset of its parent, so the whole
chain stays at least as revocable as its slowest link.

<!--DIAGRAM:delegation-chain-->

## How a use is verified

At the point of use, a conformant verifier runs the same five gates everywhere, in order, failing
closed at the first failure. This is the heart of the protocol.

<!--DIAGRAM:verification-flow-->

The normative sequence is [How it verifies](verification.html) and
[SPEC-CORE §4](spec-core.html#4-verification-algorithm-normative); the executable form is the
[reference verifier](https://github.com/kilbowie/h2a-protocol/blob/main/reference/h2a_ref/verify.py).

## Who can revoke

Gate 3 above fetches a **signed** status list. The signature matters because it encodes *who is
allowed to revoke*: revocation authority is custody of the signing key. The issuer holds it; an
implementer only fetches and verifies, and fails closed.

<!--DIAGRAM:trust-domains-->

This is [ADR-009](adr-009.html), refining ADR-005 and ADR-006.

## Evidence, not enforcement

H2A does not stop a third-party executor. When a transmission happens outside conformance, that fact
is *recorded* — explicitly, and then anchored — so it stands as admissible evidence rather than being
silently lost.

<!--DIAGRAM:anchoring-pipeline-->

See [evidence, not enforcement](spec-core.html#6-evidence-not-enforcement-adr-006) (ADR-006) and
[anchoring](spec-core.html#7-anchoring-adr-005) (ADR-005).

## What a deployment can claim

Conformance is honest by construction: each level claims only what it can prove. A deployment sits at
the highest rung it fully implements — and no higher.

<!--DIAGRAM:conformance-ladder-->

Full detail on the [Conformance](conformance.html) page.
