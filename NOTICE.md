# Licensing

**Gate G2: CLOSED — 5 August 2026.** This repository was previously unlicensed, which under
copyright law means *all rights reserved* — while `POSITIONING.md:24` described the spec as
*"Open — published, free to implement"* and §4 promised a patent non-assert. Those statements
were not supported by any licence grant. They now are.

H2A Protocol is authored by **Kilbowie**.

## The split

| Path | Licence | File |
|---|---|---|
| `spec/**` — SPEC-CORE, SPEC-MEDIA, SPEC-MEMORY, SPEC-COMMERCIAL, CONFORMANCE, THREAT-MODEL, and all ADRs | **CC BY 4.0** (`SPDX: CC-BY-4.0`) | [`spec/LICENSE`](spec/LICENSE) |
| Everything else — `schemas/`, `reference/`, `scripts/`, `site/` | **Apache-2.0** (`SPDX: Apache-2.0`) | [`LICENSE`](LICENSE) |

Both licence texts are the canonical, unmodified originals:

- `LICENSE` — Apache License 2.0, verbatim, including the unfilled appendix template.
  Attribution is carried here in NOTICE rather than by editing the licence text.
- `spec/LICENSE` — Creative Commons Attribution 4.0 International Public License, retrieved
  from `https://creativecommons.org/licenses/by/4.0/legalcode.txt` on 5 August 2026
  (18,657 bytes; all eight sections present; `ShareAlike` absent, confirming BY and not BY-SA).

Hand-pasting licence text is not acceptable for either file. If either is ever regenerated,
retrieve the canonical original again rather than editing in place.

## Why this split

The specification is meant to be quoted, translated and reproduced by implementers, unions and
regulators — CC BY 4.0 is the right instrument for prose, and asks only for attribution. The
schemas, reference implementations and tooling are software, and Apache-2.0 carries the express
patent grant a proposed standard needs if a third party is to implement it without asking
permission first.

The reference verifier is deliberately zero-dependency. That is a licensing property as much as
an engineering one: it can be vendored, audited and run offline by an auditor, union or insurer
without inheriting a transitive dependency tree, or any licence but this one.

## Attribution

When reproducing material from `spec/**`:

> H2A Protocol specification, © Kilbowie, licensed under CC BY 4.0 — https://h2a-protocol.org

## Status

H2A is a **working draft (v0.x)**. The wire format may change before v1.0, and this is not a
ratified standard. Licensing the draft does not ratify it — see `GOVERNANCE.md`.
