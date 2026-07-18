import { createSign } from "node:crypto";

// Canonicalisation must be byte-identical to every other H2A signer (issuer service, subject signer,
// Bridle, the verifier): deep-sorted-key JSON, SHA256, ECDSA P-256 (ES256), DER, base64url. That the
// witness shares no code with them — only this convention — is the point: independence.
export function canonical(obj: unknown): string {
  return JSON.stringify(obj, (_k, v) =>
    v && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b)))
      : v,
  );
}

// Sign an object over its canonical form minus its singular `signature` field.
export function signObject(privateKeyPem: string, obj: Record<string, unknown>): string {
  const { signature, ...rest } = obj as { signature?: unknown };
  void signature;
  const s = createSign("SHA256");
  s.update(canonical(rest));
  s.end();
  return s.sign(privateKeyPem).toString("base64url");
}
