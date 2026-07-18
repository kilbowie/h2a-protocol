# ADR-005 — Ledger external anchoring

**Status:** Accepted (2026-07-16).

## Context
A record signed only by the party it exonerates is worth little. Backdating and hidden-work
attacks cannot be caught from a self-consistent record alone.

## Decision
Anchor the record chain externally with **[RFC 3161](https://www.rfc-editor.org/rfc/rfc3161)
([eIDAS](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0910)-qualified)
timestamping** plus an **independent witness co-signature** on the chain head. **No blockchain** — it
reads badly to regulated counterparties and adds nothing here. The **v0 witness is an independent
witness service**, migrating to a fiduciary-operated witness later. The log stays **off the runtime
critical path**.

## Consequences
- Provides an external timestamp the recording party cannot forge.
- **Action:** select an eIDAS-qualified TSA.

## Implementation status (2026-07-18 — landed in code)
The anchoring shape is implemented end-to-end and checked by the standalone verifier:
- **Anchor object.** An implementer anchors its audit-chain **head** — `{ seq, head_hash, timestamp,
  witness }` — where `timestamp` (RFC-3161-shaped) and `witness` each carry a singular `signature` over
  `canonical(object − signature)`, the same convention as every other H2A object, so the verifier checks
  them with no implementer code.
- **Independent witness.** A reference **witness-service** (`reference/witness-service/`) co-signs the
  head from its own trust domain (`POST /cosign`), separate from the issuer and the implementer.
- **Verifier.** `anchoring.eidas_timestamp` and `anchoring.witness_cosignature` are now real checks;
  an anchored, honest bundle reaches **L3**, a forged timestamp is caught and drops to L2, and an
  unpinned TSA/witness is untrusted (`reference/verifier/src/selftest.ts` cases 6–8).
- **Interim vs qualified.** The reference TSA is **NOT eIDAS-qualified** (`qualified:false`); it proves
  the seam offline. A real qualified RFC-3161 TSA drops in behind the same seam and is pinned
  `qualified:true`. The v0 witness is founder-operated; a **fiduciary-operated** witness takes custody
  later — an ownership change, not an on-wire one. Binding a *specific record* to the anchored head via
  an inclusion proof (rather than head-level) is a documented follow-on.
- **Off the critical path.** Anchoring runs from a scheduled job over the current head, never inside a
  check (Bridle: `POST /v0/anchor` / `npm run anchor:run`).
