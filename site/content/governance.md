# Governance

## Versioning promise (gate G4)
v0.x is a working draft; the wire format may change. **v1.0 will freeze** the Grant, Attestation,
Decision Record, and Status List formats. Breaking changes before v1.0 are announced in the
changelog; after v1.0 they require a major-version bump.

## Licensing
Specification text is **CC BY 4.0**. Schemas, reference code, scripts, and site are **Apache-2.0**.

## Decisions
Architectural decisions are recorded as ADRs under `spec/adr/` (ADR-001 … ADR-009) and published in
full under [Decisions](decisions.html). The load-bearing ones: identity namespace root (001), grant
authorization (004), external anchoring (005), evidence not enforcement (006), the signing curve
(008), and revocation authority (009).

## Authorship
H2A was authored by **Kilbowie** and is offered as a neutral, proposed open standard. Authorship does
not privilege any implementation: the protocol names no operator, implementer, or vendor in its trust
model, and stewardship is intended to pass to a neutral Foundation.

## Neutrality
The standard is public from day one. The Foundation that will steward it is never in the runtime
critical path; no required fetch during an act of use resolves under the Foundation's domain.
