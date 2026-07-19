# H2A-Commercial Profile — v0.1 (working draft)

Optional profile for a commercial implementer that prices an assurance commitment. Applies only when
a Grant lists `h2a-commercial`. Schema: `h2a-commercial.profile.schema.json`. **This profile is never
required for Core conformance (ADR-012)** — a Core-conformant verifier that does not implement it
**MUST** ignore the Grant's `exposure` field and the Decision Record's `exposure_snapshot` (SPEC-CORE
§1). It is defined here, in the open standard, so that the pricing model is documented and neutral —
not so that Core standardises any implementer's revenue.

## The prevention-not-indemnity rule (normative)

The commercial profile describes a **prevention service with a contractual service remedy**, never a
contract of insurance. This is carried in the schema: `remedy_basis` is a single-value enum locked to
`service_credit`. An implementation **MUST NOT** introduce a `remedy_basis` value implying indemnity,
cover, or a promise to make a party whole. Loss events (`h2a-loss-event.schema.json`) record
prevented or narrowly-prevented acts; `remedy_triggered` records whether a service credit followed,
never a payout. See ADR-011.

## Requirements

- The exposure declaration **MUST** validate against `h2a-commercial.profile.schema.json`. It carries
  `assurance_level`, `committed_horizon_ms`, and `remedy_basis` (required), and **MAY** carry
  `per_act_limit` and `aggregate_limit` (each an ISO-4217 money object; `aggregate_limit` also carries
  its period).
- **`assurance_level` is the unified ladder.** L1 / L2 / L3 are exactly the conformance levels of
  CONFORMANCE.md (Verifiable / Attested / Anchored), read commercially as software / witnessed /
  enclave attestation. A grant **MUST NOT** declare an `assurance_level` above the level the
  deployment actually proves (the CONFORMANCE.md claim-discipline rule applies unchanged).
- **The premium base is the annual aggregate limit, not the sum of per-act limits.**
  `premium = aggregate_limit.amount × rate(assurance_level)`. The `per_act_limit` sets the per-claim
  cap only and **MUST NOT** enter the premium base (ADR-011 §2 — per-act values are correlated, not
  independent).
- **Multi-currency.** Each money object carries its own `currency`. An implementation **MUST** compute
  a premium in the currency of its `aggregate_limit` and **MUST NOT** silently convert across
  currencies.
- **Snapshot on use.** When the profile applies, a Decision Record **SHOULD** populate
  `exposure_snapshot` (per-act limit, aggregate limit, `aggregate_consumed`, `assurance_level` at the
  time of the act) and **SHOULD** populate `horizon_committed_ms` from the assurance level's committed
  horizon. `horizon_measured_ms` / `horizon_breach` are populated where the deployment instruments
  halt latency; until then they **MAY** be absent (the honest-state rule — do not fabricate a measured
  horizon).

## Notes

The billable unit is the **governed act** (an act of use / attestation), unchanged by this profile —
verification is free and halts are never billed (ADR-011). The metered gate fee per governed act, the
platform fee, and the rate card live with the implementer; only the on-wire exposure/assurance fields
and the loss-event shape are standardised here. The accumulated loss table is the actuarial asset that
makes an underwriting structure optional later — an option, not a plan.
