# Schemas

All schemas are JSON Schema Draft 2020-12. `$id`s resolve under `https://h2a-protocol.org/schemas/v0/`.

## Core
- [`h2a-core.grant`](schemas/v0/h2a-core.grant.schema.json)
- [`h2a-core.attestation`](schemas/v0/h2a-core.attestation.schema.json)
- [`h2a-core.decision-record`](schemas/v0/h2a-core.decision-record.schema.json)
- [`h2a-core.status-list`](schemas/v0/h2a-core.status-list.schema.json)

## Profiles
- [`h2a-media.profile`](schemas/v0/h2a-media.profile.schema.json)
- [`h2a-memory.profile`](schemas/v0/h2a-memory.profile.schema.json)

Every schema ships positive and negative examples under `schemas/v0/examples/`. The negative tests
(`memory.derived.INVALID`, `decision-record.INVALID`) are enforced in CI by
`scripts/validate-schemas.py`.
