# Schemas

The six H2A schemas are **JSON Schema Draft 2020-12**. Every `$id` resolves under
`https://h2a-protocol.org/schemas/v0/`, so a validator can fetch them directly. Each object below
lists its fields — type, whether it is required, and what it means — followed by a real example
taken straight from the repository.

Every example shown is **checked in CI** by [`scripts/validate-schemas.py`](https://github.com/kilbowie/h2a-protocol/blob/main/scripts/validate-schemas.py):
the validated ones must pass their schema, and the two counter-examples
(`decision-record.INVALID`, `memory.derived.INVALID`) must be rejected. The tables and examples on
this page are generated from the schema files at build time, so they cannot drift from the schemas
they describe.

<!--SCHEMA-REFERENCE-->
