# ADR-014 — Canonical form and signature encoding

**Status:** Accepted. 6 August 2026.

## Context

Every H2A claim reduces to one operation: **two parties independently derive the same bytes from the
same JSON document, and one signature over those bytes verifies under both.** Grants, decision
records, attestations, status list credentials and audit chain hashes are all signatures or hashes
over a canonicalised document. If two implementations canonicalise differently, a signature written
by one is invalid under the other — and the evidence test in `IMPL-00 §1.3` ("a stranger verifies it
offline") fails by construction.

This ADR exists because the estate had **four canonicalisers and two signature encodings**, and no
document said which was correct. Measured 5–6 August 2026:

| Implementation | Key ordering | Non-ASCII | Numbers | Signature |
|---|---|---|---|---|
| hdicr `vc-signer.ts` (`ecdsa-jcs-2019`) | RFC 8785 JCS (`canonicalize` npm) | literal UTF-8 | ECMAScript | **raw R‖S** |
| h2a TS references ×4 | `String.prototype.localeCompare` | literal UTF-8 | ECMAScript | DER |
| h2a Python `h2a_ref/verify.py:28` | `sort_keys=True` (code point) | **`\uXXXX` escaped** | **Python repr** | DER |
| Bridle `core` `canonical()` + `stable()` | `localeCompare` | literal UTF-8 | ECMAScript | DER |

The two non-conforming implementations are wrong in **disjoint** ways — the TypeScript hand-roll sorts
incorrectly but serialises correctly, and the Python reference sorts correctly but serialises
incorrectly. Neither is a subset of the other, and both agree with JCS on the payloads people test
with (lowercase ASCII keys, integer values). They diverge on exactly the payloads that matter:

```
document                         hand-rolled TS                        RFC 8785 JCS
{"Zeta":1,"alpha":2,"Beta":3}    {"alpha":2,"Beta":3,"Zeta":1}         {"Beta":3,"Zeta":1,"alpha":2}
{"10":"ten","2":"two"}           {"2":"two","10":"ten"}                {"10":"ten","2":"two"}

document                         Python h2a_ref                          RFC 8785 JCS
{"subject_ref":"José Muñoz"}     {"subject_ref":"Jos\u00e9 Mu\u00f1oz"}  {"subject_ref":"José Muñoz"}
{"cap":500.0}                    {"cap":500.0}                           {"cap":500}
```

A performer whose name carries a diacritic, or a lease cap written `500.0` rather than `500`, is
enough to make a grant unverifiable across the estate. That is the whole failure mode, and it is
silent: every implementation reports a valid signature over its own bytes.

Signature encoding is a second, independent split. Measured with a P-256 key over one message:

```
h2a/Bridle verifier (Node default = DER)  accepts DER      : true
h2a/Bridle verifier (Node default = DER)  accepts raw R‖S  : false   <- a conforming ES256 signer is rejected
JOSE / hdicr verifier (ieee-p1363)        accepts raw R‖S  : true
JOSE / hdicr verifier (ieee-p1363)        accepts DER      : false   <- the estate's own signatures are rejected
```

`SPEC-CORE` and ADR-008 declare `alg: "ES256"`. ES256 is defined by [RFC 7518
§3.4](https://www.rfc-editor.org/rfc/rfc7518#section-3.4), which specifies the fixed-width R‖S
concatenation, not DER. The estate's own signatures did not satisfy the algorithm they named.

## Decision

**1. RFC 8785 JCS is the normative canonical form.** All H2A signing and hashing operates on the
UTF-8 bytes of the [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) canonical serialisation of the
document. Three consequences are called out because each is a live defect somewhere in the estate:

- **Object property names sort as arrays of UTF-16 code units compared as unsigned integers.** RFC
  8785 §3.2.3: *"The sorting is based on pure value comparisons, where code units are treated as
  unsigned integers, independent of locale settings."* `localeCompare` is locale-collated by
  definition and is therefore never conformant. A sort implemented by rebuilding a JavaScript object
  is also non-conformant: integer-like keys are re-ordered to the front on insertion, discarding the
  sort. The canonicaliser MUST emit from the sorted sequence directly.
- **Characters outside U+0000–U+001F are emitted as literal UTF-8**, escaping only `"` and `\`.
  Python's `json.dumps` defaults to `ensure_ascii=True`; it MUST be set `False`.
- **Numbers serialise by ECMAScript `Number::toString`** (RFC 8785 §3.2.2.3, ECMA-262 §7.1.12.1).
  `500.0` emits as `500`; `-0` emits as `0`; `1e30` emits as `1e+30`. Python's `repr` satisfies none
  of these.

**2. `alg: "ES256"` means the JOSE fixed-width encoding — raw R‖S, 64 bytes, never DER.** Each of
`r` and `s` is left-padded with zeros to exactly 32 bytes. Implementations MUST emit raw R‖S and
SHOULD reject DER on the verification path. Where the signing device returns DER — AWS KMS and
Node's `createSign` both do — conversion happens at the boundary, before the signature reaches any
H2A document. Reference converters are `derToRawSignature` / `rawToDerSignature`; a DER-tolerant
verification path is permitted only behind an explicit `legacy_der` flag, and only for signatures
written before this ADR.

**3. Detached signature preimage.** A grant's `signatures[]` entries sign the JCS bytes of the grant
**with the `signatures` member removed** — not emptied, removed. Objects carrying a singular
`signature` member sign the JCS bytes of the object with that member removed. Nothing else is
stripped; in particular `signature_state` MUST NOT appear inside a signed document (see B9).

**4. The vectors in `interop/vectors/` are normative.** `vectors.json` is part of this decision, not
an illustration of it. Where prose and vectors disagree, the vectors are wrong and both get fixed —
but an implementation that reproduces every vector byte-for-byte is conformant, and one that does not
is not, regardless of what its own tests say. Vector `01-rfc8785-appendix-b` is RFC 8785's own
published test data, so the file is anchored to the RFC rather than to any single library.

**5. One canonicaliser per language, at a published import path.** Not one per repository and not
one per service. The estate's four hand-rolled copies exist because canonicalisation looked small
enough to inline — ~8 lines each, and every copy was wrong in the same two ways.

## Consequences

- **hdicr is the only implementation that is already conformant** on both axes. It becomes the
  reference against which the others are ported (S1.H1 verifies it against these vectors rather than
  assuming it).
- **Every signature written before this ADR is DER.** Nothing in the estate has issued a production
  grant, so there is no migration to perform — this is the last moment at which that is true, which
  is why the ADR lands in Phase 1 rather than later.
- **The browser consent ceremony (ADR-007, S3.T1) needs JCS too.** WebCrypto signs bytes; the
  ceremony must canonicalise the grant client-side to produce them, and it cannot reach the Node
  implementations by filesystem path. This makes the canonicaliser a **published package**, not a
  shared file — a fourth consumer that no repository can alias its way to (plan correction R-C13).
- **Interop is testable rather than asserted.** Before this ADR, "byte-identical by specification,
  not by shared code" was written in `reference/verifier/src/crypto.ts` and was false at the time it
  was written. The three-way byte-identity job (S1.X1) converts that sentence into a CI signal.
- `canonicalize` (npm) reproduces RFC 8785's published test data byte-for-byte and is the sanctioned
  TypeScript dependency for services. **The verifier stays zero-dependency** and carries its own ~80
  line implementation — its independence is the point of ADR-006, and a shared library would make it
  unable to expose an implementer that shipped the same bug.

## References

- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) — JSON Canonicalization Scheme
- [RFC 7518 §3.4](https://www.rfc-editor.org/rfc/rfc7518#section-3.4) — ES256, fixed-width R‖S
- ADR-004 (grant authorization — detached signatures), ADR-008 (signing curve, `alg` header)
- `interop/vectors/vectors.json`, `interop/README.md`
