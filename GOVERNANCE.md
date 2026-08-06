# Governance

**Versioning (gate G4).** v0.x is a working draft; the wire format may change. **v1.0 freezes** the
Grant, Attestation, Decision Record, and Status List formats. Post-v1.0 breaking changes require a
major-version bump.

**Licensing (gate G2 — CLOSED, 5 August 2026).** Spec text (`spec/**`, including all ADRs) is
**CC BY 4.0** — see [`spec/LICENSE`](spec/LICENSE). Schemas, reference code, scripts and site are
**Apache-2.0** — see [`LICENSE`](LICENSE). Both are the canonical texts, unmodified; the CC BY 4.0
legalcode was retrieved from creativecommons.org on the closing date. Do not hand-paste legal text
if either file is ever regenerated — retrieve the canonical original. Full statement and
attribution wording: [`NOTICE.md`](NOTICE.md).

**Decisions.** Recorded as ADRs under `spec/adr/` (ADR-001 … ADR-014), published at
[h2a-protocol.org/decisions.html](https://h2a-protocol.org/decisions.html). ADR-013 is reserved for
executor tiers and is not yet written; the gap is deliberate, not a missing file.

**Normative test data.** ADR-014 makes `interop/vectors/vectors.json` normative: an implementation is
conformant if and only if it reproduces every vector byte-for-byte. Prose describes the canonical
form; the vectors decide it.

**Authorship.** H2A was authored by **Kilbowie** and is offered as a neutral, proposed open standard;
it privileges no implementation and names no operator, implementer, or vendor in its trust model.
Stewardship is intended to pass to a neutral Foundation.

**Neutrality.** Public from day one; the stewarding Foundation is never in the runtime critical path.
