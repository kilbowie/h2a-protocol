# Changelog

Notable changes to the H2A protocol — spec, schemas, reference, and site. H2A is a **v0.x working
draft**, so entries are dated rather than version-tagged; per-document versions (e.g. SPEC-CORE v0.2)
are noted where they change. New changes go at the **top**, under the current date. Format loosely
follows [Keep a Changelog](https://keepachangelog.com).

## 2026-07-19

### Commercial profile (optional, non-Core)
- **New `h2a-commercial` profile.** [SPEC-COMMERCIAL](spec/SPEC-COMMERCIAL.md) defines an optional
  exposure/assurance profile for a commercial implementer that prices an assurance commitment. It is
  **never required for Core conformance** — a Core-conformant verifier ignores it. New schemas
  `h2a-commercial.profile.schema.json` (the exposure declaration — per-act limit, aggregate limit,
  assurance level, committed horizon, `remedy_basis` locked to `service_credit`) and
  `h2a-loss-event.schema.json` (the actuarial loss record). Money objects carry ISO-4217 currency, so
  the profile is inherently multi-currency.
- **Core forward-compatibility rule (SPEC-CORE §1 → still v0.2).** Profiles MAY define additional Grant
  and Decision Record fields; a verifier MUST ignore unrecognised fields and MUST NOT refuse a grant
  for carrying them. Enables the commercial fields to ride on the Core grant/decision-record without
  entering the conformance surface.
- **Grant + Decision Record additions.** Optional opaque `exposure` on the grant and `exposure_snapshot`
  on the decision record (profile-constrained). Core-owned evidence fields added to the decision record:
  `horizon_committed_ms`, `horizon_measured_ms`, `horizon_breach`, `chain_conformance`.
- **The assurance ladder is the conformance ladder, priced.** CONFORMANCE.md now states L1/L2/L3 are one
  ladder viewed two ways (Verifiable/Attested/Anchored = software/witnessed/enclave), and that profiles
  are never required for conformance. CONFORMANCE → v0.3 (clarified).
- **ADRs.** [ADR-011](spec/adr/ADR-011-commercial-model.md) — commercial model (governed act billed,
  annual aggregate limit as the premium base, assurance-priced, service-credit remedy).
  [ADR-012](spec/adr/ADR-012-exposure-fields-optional-profile.md) — exposure fields are an optional
  profile, never Core, with the neutrality rationale.

## 2026-07-18

### Neutrality & references
- **Neutral, proposed-standard framing.** All references to specific commercial actors were removed
  from the spec, ADRs, schemas, reference code, and site. A named example implementer, operator,
  generation vendors, specific unions/CMOs, and a specific witness domain are now stated only as
  neutral roles ("the implementer", "an operator", "a third-party generation provider", "a union or
  CMO", "an independent witness service"). Sales framing was rewritten as neutral standard language.
- **Authorship.** H2A is now attributed to **Kilbowie** as author, in the site footer, the home page,
  and Governance — offered as a neutral standard that privileges no implementation.
- **Cited sources.** Every external standard and legal instrument is now linked at its point of mention
  (RFC 2119, RFC 3161, eIDAS / Reg. (EU) 910/2014, GDPR Art. 7, C2PA, FIPS 140-3) and collected on a new
  **[References](references.html)** page in the nav.

### Site
- **Architecture & process-flow diagrams.** The protocol's key flows are now shown visually, not just
  in prose: the five-gate verification algorithm (fail-closed, with the reason code each gate emits),
  the four-object relationship map, the issuer-vs-implementer revocation key-custody split (ADR-009),
  the L1→L2→L3 conformance ladder, the two-signature grant, delegation attenuation, and the
  evidence/anchoring pipeline. Diagrams are generated at build time as themed inline HTML (`site/diagrams.py`,
  placed with `<!--DIAGRAM:name-->` markers) — no client JS, and they follow the light/dark theme.
- **New "How it works" page** assembling the diagrams into a single visual walkthrough, linked from the
  top nav.
- **Colour language extended:** a third semantic accent, BLUE `--info`, joins GREEN `--ok` (pass) and
  RED `--bad` (fail) for informational/neutral states; a shared legend documents the key. The top nav
  now marks the current page.

## 2026-07-17

### Site
- **Theme toggle.** A manual light/dark switch in the header, remembered across visits; the site still
  follows the operating-system setting until you choose. Syntax highlighting themes with it.
- **"Last updated" per page.** Each page footer shows when its content last changed, taken from the
  source file's last commit.
- **This changelog**, published at [/changelog](changelog.html).
- **Schemas page rebuilt** as a generated per-object reference: `Field / Type / Required / Description`
  tables with nested sub-tables, enum and pattern labels, the conditional rules stated in prose, and
  every CI-validated example inlined. Generated from the schema JSON at build time (a coverage guard
  fails the build if a field would be dropped), so it can never drift from the schemas.
- **Readability polish:** dark mode, Pygments JSON/code highlighting, copy-to-clipboard buttons,
  heading anchors, on-page tables of contents, and wider tables for the schema reference.

### Reference & CI
- **Cross-language interop gate.** The TypeScript issuer service signs a status list; the Python
  reference verifier verifies that signature, reads the revoked bit, and reaches the right decision —
  enforced in CI, no longer asserted only by inspection. The issuer service is also typechecked.
- **Reference verifier is fail-closed on the status-list signature.** `verify()` now requires the
  issuer's status public key; there is no path that permits a list it could not verify. A shared
  issuing helper builds schema-valid signed lists for both the demo and the CI gate.

### Spec
- **ADR-009 — revocation authority sits with the issuer.** Revocation authority is defined as custody
  of the status-list signing key: the issuer signs the list, and an implementer is fetch-and-verify
  only, with no revoke endpoint and no list of its own. SPEC-CORE §4.3 now requires verifying the
  status-list signature and failing closed on an unreachable, unsigned, wrongly-signed, or stale list;
  CONFORMANCE L2 requires signed-list verification; the threat model covers status forgery and
  implementer-as-authority. SPEC-CORE → v0.2, CONFORMANCE → v0.3, THREAT-MODEL → v0.2. Detail in
  [`CHANGES-revocation-authority.md`](https://github.com/kilbowie/h2a-protocol/blob/main/CHANGES-revocation-authority.md).
- The reference issuer/status service (`reference/issuer-service/`) was added as the fiduciary trust
  domain that holds the signing key.

### Initial
- First publication: the core, media, and memory specifications; conformance levels; threat model;
  ADR-001 … ADR-008; six JSON Schemas with positive and negative examples; the runnable reference
  verifier; and this static site, deployed to h2a-protocol.org via GitHub Actions.
