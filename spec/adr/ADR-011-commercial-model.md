# ADR-011 — Commercial model: governed act billed, aggregate-limit premium base, assurance-priced

**Status:** Accepted (2026-07-19). Builds on ADR-002 (enrollment assurance tiers), ADR-006 (evidence,
not enforcement), and the CONFORMANCE.md L1/L2/L3 ladder. Source of record:
`bridle/docs/COMMERCIAL-MODEL-LOCKIN.md`.

## Context
Bridle is a software company that prices like an insurer but **is not** an insurer: it does not
indemnify and carries no risk on its own balance sheet — *software first, underwriting optional*. The
decision-record corpus is the only loss table for this risk class, which makes an MGA structure
genuinely available in three-to-five years — an option, not a plan, and nothing in the build
forecloses it. The model must be documented in the open standard (so it is neutral and inspectable)
without Core standardising anyone's revenue (ADR-012 handles the neutrality mechanism).

Two things had to be decided out loud: **what is billed**, and **on what base**.

## Decision

1. **The billable unit is the governed act** — an act of use / attestation. Verification is free,
   halts are never billed, and CMOs, unions and performers never pay. Metering a check would ration
   it, and revocation is live; a rationed check would be a stale check.

2. **The premium base is the annual aggregate limit, not the sum of per-act exposures.** Pricing per
   act on the *sum* of per-act declared exposures does not survive contact with a real operator:
   20,000 acts/month at $1,000 each is a $20M/month aggregate that no operator will sign, and the
   number is wrong because the risks are heavily correlated — the realistic maximum is one or two
   incidents, not 20,000 independent failures. The correction is standard insurance practice:
   - **per-act limit** sets the **per-claim cap** (max remedy on any single act);
   - **annual aggregate limit** sets the **premium base**;
   - **premium = aggregate limit × rate(assurance_level)**, allocated and billed per governed act,
     trued up quarterly against actual volume.
   Second-order benefit: under-declaration is self-policing — a low aggregate limit caps the
   customer's own remedy, so no audit is required.

3. **Rate by assurance level, and assurance level is the conformance ladder priced.** L1 software =
   Verifiable = 1.0%; L2 witnessed = Attested = 2.0%; L3 enclave = Anchored = 3.0%. There is **one**
   L1/L2/L3 ladder (CONFORMANCE.md), not two — the conformance level is the technical claim, the
   assurance level is that claim priced. A grant MUST NOT declare an assurance level above what the
   deployment proves.

4. **Multi-currency.** Exposure money objects carry their own ISO-4217 currency; a premium is computed
   in the currency of its aggregate limit; no silent cross-currency conversion.

5. **The remedy is a service credit, never indemnity.** Capped at fees paid in the preceding 12
   months, and additionally at the per-act limit. This ordering — revocation horizon (prevention) →
   decision record (evidence) → loss table (actuarial asset) — is also the legal argument: a
   prevention service that stops a loss occurring is materially different from a contract that pays
   after a loss occurs. `remedy_basis` is locked to `service_credit` in the schema; the language rules
   (SPEC-COMMERCIAL, and the copy guard in `bridle-site/`) enforce it in words.

## Consequences
- On-wire: the optional `exposure` object on a grant and `exposure_snapshot` + horizon fields on a
  decision record (both profile-gated, ADR-012), plus `h2a-loss-event.schema.json` — the file an
  underwriter will eventually ask to see, designed now while backfilling is possible.
- In the implementer (`bridle`): the shipped per-act tier table (Developer/Studio/Scale/Enterprise) is
  **superseded** as the headline model by `premium = aggregate × rate + platform fee + (governed acts
  × gate fee)`; the per-act metering machinery survives as the metered-gate-fee line.
- **Blocking, outside these repos (recorded, not resolved here):** a legal opinion on whether the halt
  commitment is a contract of insurance; horizon commitments remain placeholders pending 30 valid
  drill cycles under load; the L3 platform fee assumes an unmeasured enclave cost per tenant. Public
  quoted pricing is gated on these.
