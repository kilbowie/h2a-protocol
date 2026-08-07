// RFC 8785 JSON Canonicalization Scheme + JOSE ES256 signature encoding (ADR-014).
//
// ZERO DEPENDENCIES, and deliberately so: this file is copied byte-identically into each reference
// component rather than shared through a package. Two reasons, and they pull the same way.
//
//   1. The reference stack has no dependencies at all — a stranger runs it with nothing but Node.
//      That is what makes it an executable spec rather than a project. Adding `canonicalize` to
//      three services to avoid retyping thirty lines would trade that away cheaply.
//   2. ADR-006: the verifier must be able to expose an implementer that shipped a canonicalisation
//      bug. It cannot do that while sharing the implementation with one.
//
// Duplication is what caused the estate's four-way split, so it is only tolerable here because it
// is now CHECKED rather than trusted: scripts/check-jcs-copies.py asserts every copy is
// byte-identical, and scripts/check-interop.py runs all of them against interop/vectors/. Drift
// fails CI. When the reference packages are published (IMPL-02 §4.3) this collapses to one import.
//
// WHAT WAS ACTUALLY WRONG BEFORE. Very little, which is why it survived: JavaScript's own
// primitives are already RFC 8785-conformant. JSON.stringify emits ECMAScript Number::toString
// (500.0 -> 500, -0 -> 0, 1e21 -> 1e+21), lowercase \uXXXX for control characters with the five
// short forms, literal UTF-8 above U+001F, and escapes only " and \. The single defect was key
// ORDERING, and it was two defects in one line:
//
//   Object.fromEntries(Object.entries(v).sort(([a],[b]) => a.localeCompare(b)))
//                                             ^^^^^^^^^^^^^ locale-collated, never conformant
//   ^^^^^^^^^^^^^^^^^^ rebuilding an object re-orders integer-like keys to the front, discarding
//                      the sort entirely — so "10" landed after "2" even with a correct comparator
//
// Both are fixed by sorting an ARRAY of keys with the default comparator, which compares UTF-16
// code units as unsigned integers — exactly what RFC 8785 §3.2.3 requires.

/** RFC 8785 canonical JSON. Throws on values JSON cannot represent. */
export function jcs(value: unknown): string {
  const out = serialize(value);
  if (out === undefined) throw new Error("jcs: value is not representable as JSON");
  return out;
}

/** The UTF-8 bytes to sign or hash. Signatures are over bytes, not over strings. */
export function jcsBytes(value: unknown): Buffer {
  return Buffer.from(jcs(value), "utf8");
}

function serialize(v: unknown): string | undefined {
  if (v === null) return "null";
  switch (typeof v) {
    case "boolean":
      return v ? "true" : "false";
    case "number":
      // RFC 8785 §3.2.2.3 defers to ECMAScript Number::toString, which is what JSON.stringify uses.
      // NaN and Infinity have no JSON form; emitting "null" for them (JSON.stringify's behaviour)
      // would silently canonicalise two different values to the same bytes.
      if (!Number.isFinite(v)) throw new Error(`jcs: ${String(v)} has no JSON representation`);
      return JSON.stringify(v);
    case "string":
      // §3.2.2.2 — JSON.stringify already escapes only " and \, uses the five short forms, emits
      // lowercase \uXXXX below U+0020, and leaves everything above it as literal UTF-8.
      return JSON.stringify(v);
    case "object":
      break;
    default:
      return undefined; // undefined, function, symbol — dropped by JSON, so dropped here
  }

  if (Array.isArray(v)) {
    // A hole or an undefined element is `null` in JSON, matching JSON.stringify.
    return "[" + v.map((e) => serialize(e) ?? "null").join(",") + "]";
  }
  if (v instanceof Date || typeof (v as { toJSON?: unknown }).toJSON === "function") {
    return serialize((v as { toJSON: () => unknown }).toJSON());
  }

  const obj = v as Record<string, unknown>;
  // THE FIX. Sorting an array of keys uses the default comparator: UTF-16 code units compared as
  // unsigned integers, independent of locale. Emitting from that sequence — never by rebuilding an
  // object — is what keeps "10" before "2".
  const parts: string[] = [];
  for (const key of Object.keys(obj).sort()) {
    const encoded = serialize(obj[key]);
    if (encoded === undefined) continue; // undefined-valued properties are omitted, as in JSON
    parts.push(JSON.stringify(key) + ":" + encoded);
  }
  return "{" + parts.join(",") + "}";
}

// ---------------------------------------------------------------------------
// ES256 signature encoding — ADR-014 §2.
//
// `alg: "ES256"` is RFC 7518 §3.4: the fixed-width concatenation of r and s, each left-padded to
// 32 bytes. 64 bytes total, never DER. Node's createSign and AWS KMS both return DER, so the
// conversion belongs at that boundary — before the signature reaches any H2A document.
// ---------------------------------------------------------------------------

const P256_COORD_BYTES = 32;

/** DER SEQUENCE{INTEGER r, INTEGER s} -> raw 64-byte R‖S. */
export function derToRaw(der: Buffer): Buffer {
  let i = 0;
  if (der[i++] !== 0x30) throw new Error("derToRaw: expected SEQUENCE");
  let len = der[i++];
  if (len & 0x80) {
    const n = len & 0x7f;
    len = 0;
    for (let k = 0; k < n; k++) len = (len << 8) | der[i++];
  }
  const readInt = (): Buffer => {
    if (der[i++] !== 0x02) throw new Error("derToRaw: expected INTEGER");
    const l = der[i++];
    const b = der.subarray(i, i + l);
    i += l;
    return b;
  };
  return Buffer.concat([pad32(readInt()), pad32(readInt())]);
}

/** Raw 64-byte R‖S -> DER SEQUENCE{INTEGER r, INTEGER s}. */
export function rawToDer(raw: Buffer): Buffer {
  if (raw.length !== 2 * P256_COORD_BYTES) {
    throw new Error(`rawToDer: expected ${2 * P256_COORD_BYTES} bytes, got ${raw.length}`);
  }
  const toDerInt = (b: Buffer): Buffer => {
    let v = stripLeadingZeros(b);
    if (v[0] & 0x80) v = Buffer.concat([Buffer.from([0x00]), v]); // DER INTEGERs are signed
    return Buffer.concat([Buffer.from([0x02, v.length]), v]);
  };
  const r = toDerInt(raw.subarray(0, P256_COORD_BYTES));
  const s = toDerInt(raw.subarray(P256_COORD_BYTES));
  return Buffer.concat([Buffer.from([0x30, r.length + s.length]), r, s]); // P-256: length < 128
}

/** True if the buffer is plausibly DER rather than raw R‖S — used to give a precise error. */
export function looksLikeDer(sig: Buffer): boolean {
  return sig.length !== 2 * P256_COORD_BYTES && sig[0] === 0x30;
}

function stripLeadingZeros(b: Buffer): Buffer {
  let i = 0;
  while (i < b.length - 1 && b[i] === 0) i++;
  return b.subarray(i);
}

function pad32(b: Buffer): Buffer {
  const v = stripLeadingZeros(b);
  if (v.length > P256_COORD_BYTES) throw new Error("coordinate longer than 32 bytes");
  return Buffer.concat([Buffer.alloc(P256_COORD_BYTES - v.length), v]);
}
