# ADR-007 — Consent-capture ceremony

**Status:** Accepted (2026-07-16).

## Context
Under custodial custody (ADR-003) the risk is a custodian fabricating consent. The ceremony must
make that impossible to do silently.

## Decision
The subject **always** authorises through an **authenticated, challenge-bound interaction**,
recorded as a **`CONSENT_CAPTURE`** event. The custodian's signature **attests to that
authorisation** — it never manufactures it. No `CONSENT_CAPTURE`, no valid consent signature.

## Consequences
- Consent is traceable to a live subject interaction, not a custodian's say-so.
- Gives [GDPR Art. 7(1)](https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_7) "demonstrate consent on
  every act" a concrete artefact.
