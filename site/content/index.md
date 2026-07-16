# H2A Protocol

**H2A is a neutral, open standard for the consent, attestation, and revocation of AI-generated
likeness and AI memory.** It answers one question, verifiably: *was this allowed?*

H2A **evidences; it does not enforce.** For every act of use it produces a signed, externally
anchored record of whether the transmission was conformant — and when it was not, it records that
explicitly, so the record is admissible evidence. The check is free and open; the guarantee around
it is what a commercial implementer sells.

## The four objects
- **Grant** — authority to use a subject within a bounded scope, revocable at point of use.
- **Attestation** — a signed receipt of one act of use.
- **Decision Record** — the signed conformant / non-conformant transmission decision.
- **Status List** — a static, signed revocation artefact.

## Start here
- [How verification works](verification.html) — the check, in order, fail-closed.
- [Core specification](spec-core.html) · [Conformance](conformance.html) · [Schemas](schemas.html)
- Reference verifier: `reference/` in the repository (`python -m h2a_ref.demo`).
