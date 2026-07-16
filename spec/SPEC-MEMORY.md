# H2A-Memory Profile — v0.1 (working draft)

Profile for AI memory records about a subject. Applies only when a Grant lists `h2a-memory`.
Schema: `h2a-memory.profile.schema.json`.

## The provenance rule (normative negative test)
A record with `memory_type: "derived"` **MUST** carry non-empty `provenance.sources`. A derived
record without provenance **MUST** be rejected. This is the standard's canonical negative test and
is enforced by `scripts/validate-schemas.py` against `examples/memory.derived.INVALID.json`.

## Requirements
- Every record **MUST** reference its `grant_id` and `subject_ref`.
- `record.content_hash` **MUST** be a SHA-256 over the record content.
- `retention.deletion_on_revoke` defaults to `true`; when true, revocation of the Grant obliges
  deletion of the record within the Grant's `revocation_horizon`.
