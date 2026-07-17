import { createSign, createVerify } from "node:crypto";

// Deterministic stable stringify (deep-sorted keys) so signatures are reproducible.
export function canonical(obj: unknown): string {
  return JSON.stringify(obj, (_k, v) =>
    v && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b)))
      : v,
  );
}

// Sign everything in `obj` except its `signature` field. ES256 (ECDSA P-256), DER-encoded, base64url.
export function signObject(privateKeyPem: string, obj: Record<string, unknown>): string {
  const { signature, ...rest } = obj;
  void signature;
  const s = createSign("SHA256");
  s.update(canonical(rest));
  s.end();
  return s.sign(privateKeyPem).toString("base64url");
}

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
