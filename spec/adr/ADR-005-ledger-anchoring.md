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
