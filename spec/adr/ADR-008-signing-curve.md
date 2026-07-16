# ADR-008 — Signing curve

**Status:** Accepted.

## Context
Ed25519 is not supported at standard tier by AWS KMS or Azure Managed HSM, and regulated
counterparties care about FIPS validation.

## Decision
**ECDSA P-256 (ES256)** is the mandatory-to-implement baseline — FIPS 140-3 validated, supported
everywhere, credible with a general counsel. The spec is **curve-agnostic via the `alg` header**,
so post-quantum migration is a header change, not a redesign.

## Consequences
- Guaranteed interoperability floor.
- Bind the property (signature verifiability), never the vendor or the curve.
