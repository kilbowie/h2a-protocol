import { createVerify } from "node:crypto";
import { gunzipSync } from "node:zlib";

// The verifier re-implements the H2A crypto conventions from scratch — it depends on NO implementer
// package (that independence is the whole point: it must be able to expose a misbehaving one), and
// it stays zero-dependency for the same reason. The conventions are the cross-implementation interop
// contract, and they are now written down: **ADR-014** makes RFC 8785 JCS the normative canonical
// form and `alg:"ES256"` the JOSE raw R‖S encoding, with `interop/vectors/vectors.json` as normative
// test data.
//
// ⚠️ THIS FILE DOES NOT YET CONFORM TO ADR-014. Ported in S1.P3; until then, stated plainly:
//
//   - `canonical()` below sorts with `localeCompare`, which is locale-collated. RFC 8785 §3.2.3
//     requires UTF-16 code units compared as unsigned integers, "independent of locale settings".
//     It also rebuilds a JavaScript object, which silently re-orders integer-like keys to the front
//     and discards the sort. It fails interop vectors 04, 05 and 09.
//   - `createVerify(...).verify()` accepts DER, and rejects the fixed-width R‖S encoding that
//     `alg:"ES256"` actually denotes (RFC 7518 §3.4). A conforming signer is rejected today.
//
// The comment this replaced claimed the output was "byte-identical to the issuer service, the
// subject signer, and an independent implementer — by specification, not by shared code". That was
// false when written: there was no specification to be identical by, and measurement on 5 August
// 2026 found four canonicalisers and two signature encodings across the estate. ADR-014 supplies the
// specification; S1.X1 supplies the CI job that makes the claim checkable instead of asserted.

export function canonical(obj: unknown): string {
  return JSON.stringify(obj, (_k, v) =>
    v && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b)))
      : v,
  );
}

// Verify an object carrying a singular `signature` field (status lists, decision records, attestations).
export function verifyObject(publicKeyPem: string, obj: Record<string, unknown>): boolean {
  const { signature, ...rest } = obj as { signature?: string };
  if (!signature) return false;
  try {
    const v = createVerify("SHA256");
    v.update(canonical(rest));
    v.end();
    return v.verify(publicKeyPem, Buffer.from(signature, "base64url"));
  } catch {
    return false;
  }
}

// Verify one DETACHED grant signature over canonical(grant minus the `signatures` array) (ADR-004).
export function verifyDetached(publicKeyPem: string, obj: Record<string, unknown>, value: string): boolean {
  if (!value) return false;
  const { signatures, ...rest } = obj as { signatures?: unknown };
  void signatures;
  try {
    const v = createVerify("SHA256");
    v.update(canonical(rest));
    v.end();
    return v.verify(publicKeyPem, Buffer.from(value, "base64url"));
  } catch {
    return false;
  }
}

// Read one bit of a base64url gzip bitstring status list (bit set = revoked).
export function isRevoked(listB64u: string, index: number): boolean {
  const raw = gunzipSync(Buffer.from(listB64u, "base64url"));
  const byte = index >> 3;
  if (byte >= raw.length) return false;
  return (raw[byte] & (1 << (index & 7))) !== 0;
}
