# ADR-012 — Exposure fields are an optional profile, never Core

**Status:** Accepted (2026-07-19). Builds on ADR-011 (commercial model) and the SPEC-CORE §1
forward-compatibility rule. Source of record: `bridle/docs/COMMERCIAL-MODEL-LOCKIN.md` §3.1.

## Context
ADR-011 puts a price on an assurance commitment. The exposure and assurance fields that carry that
price (per-act limit, aggregate limit, assurance level, committed horizon, remedy basis) are the
implementer's **revenue model**. If SPEC-CORE mandated any of them as a conformance requirement, the
Foundation would be standardising one implementer's revenue — and the neutrality argument H2A rests on
(the implementer is not the standard; the standard is inspectable and vendor-neutral) dies at the
first hostile question. The work order states the constraint bluntly: *the exposure fields MUST NOT be
a Core conformance requirement.*

There is a genuine tension to resolve: the commercial fields must ride on the **same** on-wire grant
and decision record that Core defines (so a single verifier sees them), yet must not be Core.

## Decision
**Exposure/assurance fields are defined only in the `h2a-commercial` profile (SPEC-COMMERCIAL) and are
never required for Core conformance.** Concretely:

1. **A forward-compatibility rule in Core.** SPEC-CORE §1: profiles MAY define additional Grant and
   Decision Record fields; a verifier **MUST** ignore fields it does not recognise and **MUST NOT**
   refuse a grant solely because it carries profile fields outside Core.
2. **An opaque hook in the Core schemas, not the shape.** The grant schema gains one optional
   `exposure` property typed only as `{"type": "object"}`; the decision-record schema gains one
   optional `exposure_snapshot` the same way. Core does **not** constrain their internals — the
   `h2a-commercial.profile.schema.json` does, and only when the grant lists `h2a-commercial`. Core
   stays `additionalProperties: false` for every field it actually owns.
3. **CONFORMANCE.md states it explicitly.** A Core-conformant implementation is not required to
   support the commercial profile; the profile is outside the conformance surface by construction.
4. **Horizon and chain-conformance fields are the exception, and belong to Core.** `horizon_committed_ms`,
   `horizon_measured_ms`, `horizon_breach`, and `chain_conformance` are *evidence-quality* fields (the
   revocation horizon is already the Core conformance dial), so they are Core decision-record fields —
   not commercial. Only the exposure/assurance/pricing fields are profile-gated.
5. **Naming.** Profile fields follow the existing snake_case convention (not the camelCase of the
   source work order), so they read identically to Core fields on the wire.

## Consequences
- A hostile reviewer can confirm neutrality mechanically: remove `h2a-commercial` from an
  implementation and every conformance test still passes; no Core object *requires* an exposure field.
- The loss-event schema (`h2a-loss-event.schema.json`) is likewise associated with the commercial
  profile and is not a Core conformance requirement.
- The single-value `remedy_basis` enum (ADR-011) lives in the profile schema, documenting the
  prevention-not-indemnity constraint where the fields are defined, not in Core.
