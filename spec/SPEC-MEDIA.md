# H2A-Media Profile — v0.1 (working draft)

Asset-bound profile for AI-generated likeness (audio, video, image, 3D). Applies only when a Grant
lists `h2a-media`. Schema: `h2a-media.profile.schema.json`.

## Requirements
- An H2A-Media object **MUST** reference its `grant_id` and the `likeness_ref` (subject URN).
- The `asset.content_hash` **MUST** be a SHA-256 over the committed asset bytes.
- Where a [C2PA](https://c2pa.org/specifications/) manifest exists, `asset.c2pa_manifest_ref`
  **SHOULD** point to it. C2PA composition for multi-part supply chains lives here, not in Core.
- For a composite asset, `composition[]` **MUST** list the parent assets and their governing grants.
  The composite's effective revocability is the **maximum horizon over all parts**.

## Notes
Modality-specific limits (e.g. no singing voice, no minor likeness) are expressed in `constraints`
and evaluated as scope exclusions at point of use.
