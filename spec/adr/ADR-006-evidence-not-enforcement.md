# ADR-006 — H2A evidences; it does not enforce

**Status:** Accepted (2026-07-16). Supersedes earlier "gate / halt / kill-switch" framing.

## Context
Earlier drafts described H2A as an in-flight *halt* on generation. That primitive cannot hold
when generation is outsourced to a third-party executor — you cannot halt someone else's process —
and framing the product as a veto invites exactly the fights that kill adoption.

## Decision
H2A **evidences** conformant vs non-conformant transmission; it does not enforce. The
**decision record is a first-class schema object** recording, per act, whether a transmission was
conformant — and, when it was not, recording the non-conformant transmission **explicitly** so it
becomes admissible evidence. Operators generate; H2A produces the signed account of what happened.

## Consequences
- An operator can outsource generation to a third-party generation provider (via an implementer's
  adapter) and still be conformant.
- H2A provides cryptographic evidence for dispute resolution, not a kill-switch.
- Retire "gate", "halt", "enforce" from spec language.
