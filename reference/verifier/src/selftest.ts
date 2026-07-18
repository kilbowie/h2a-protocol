import { createSign, generateKeyPairSync } from "node:crypto";
import { gzipSync } from "node:zlib";
import { canonical } from "./crypto.js";
import { verifyBundle, type Anchors, type Bundle } from "./verify.js";

// Proves the verifier end-to-end with freshly generated keys and REAL signatures — no implementer
// code involved. The signing here mirrors the H2A conventions (the interop contract), so a green
// selftest means the verifier agrees with any conformant signer.

function kp() {
  const { privateKey, publicKey } = generateKeyPairSync("ec", { namedCurve: "P-256" });
  return {
    priv: privateKey.export({ type: "pkcs8", format: "pem" }).toString(),
    pub: publicKey.export({ type: "spki", format: "pem" }).toString(),
  };
}
function signDetached(priv: string, obj: Record<string, unknown>): string {
  const { signatures, ...rest } = obj as { signatures?: unknown };
  void signatures;
  const s = createSign("SHA256"); s.update(canonical(rest)); s.end();
  return s.sign(priv).toString("base64url");
}
function signObject(priv: string, obj: Record<string, unknown>): string {
  const { signature, ...rest } = obj as { signature?: unknown };
  void signature;
  const s = createSign("SHA256"); s.update(canonical(rest)); s.end();
  return s.sign(priv).toString("base64url");
}
function encodeBitstring(revoked: Set<number>): string {
  const bytes = Buffer.alloc(1024 / 8);
  for (const i of revoked) if (i >= 0 && i < 1024) bytes[i >> 3] |= 1 << (i & 7);
  return gzipSync(bytes).toString("base64url");
}

let failures = 0;
function check(cond: boolean, msg: string) {
  if (!cond) { console.error("  x " + msg); failures++; } else console.log("  ok " + msg);
}

const issuer = kp(), subject = kp(), bridle = kp();
const ISS = "https://interim-fiduciary.kilbowieconsulting.com/h2a/issuer";
const SUBJECT_REF = "urn:h2a:subject:jane-actor-001";
const IDX = 42;
const now = new Date();
const iso = (d: Date) => d.toISOString();

function makeGrant() {
  const exp = new Date(now.getTime() + 90 * 864e5);
  const base: Record<string, unknown> = {
    h2a_version: "0.1", grant_id: "3f2a1c40-0d1e-4b2a-9c33-8a1b2c3d4e5f", iss: ISS,
    subject_ref: SUBJECT_REF, grantee_ref: "urn:h2a:grantee:truly-imagined",
    scope: { purposes: ["promotional-video"], territories: ["GB", "US"], exclusions: ["political"] },
    status: { uri: `${ISS}/status/list`, mirrors: [], index: IDX },
    revocation_horizon: "PT30M", alg: "ES256", signatures: [] as unknown[],
    iat: iso(now), nbf: iso(now), exp: iso(exp),
  };
  base.signatures = [
    { role: "consent", kid: `${SUBJECT_REF}#consent`, value: signDetached(subject.priv, base) },
    { role: "issuance", kid: `${ISS}#issuance`, value: signDetached(issuer.priv, base) },
  ];
  return base;
}
function makeStatusList(revoked: Set<number>) {
  const list: Record<string, unknown> = {
    h2a_version: "0.1", status_list_id: "list", iss: ISS, purpose: "revocation",
    encoding: "base64url-bitstring", list: encodeBitstring(revoked),
    valid_from: iso(now), valid_until: iso(new Date(now.getTime() + 3600e3)), alg: "ES256",
  };
  list.signature = signObject(issuer.priv, list);
  return list;
}
function makeRecord(decision: string, reason: string) {
  const rec: Record<string, unknown> = {
    h2a_version: "0.1", record_id: "rec-1", grant_id: "3f2a1c40-0d1e-4b2a-9c33-8a1b2c3d4e5f",
    decision, reason_code: reason, signature_state: "verified", measured_latency_ms: 0,
    non_conformant_transmission: null, created_at: iso(now), alg: "ES256", signature: "",
  };
  rec.signature = signObject(bridle.priv, rec);
  return rec;
}

const anchors: Anchors = {
  issuers: { [ISS]: { public_key_pem: issuer.pub } },
  subjects: { [SUBJECT_REF]: { public_key_pem: subject.pub } },
  implementers: { bridle: { public_key_pem: bridle.pub } },
};
const use = { purpose: "promotional-video", territory: "GB", spend: 100 };

console.log("1. honest PERMIT bundle");
{
  const b: Bundle = { grant: makeGrant() as any, use, decision_record: makeRecord("PERMITTED_CONFORMANT", "in-scope"), status_list: makeStatusList(new Set()), implementer: "bridle" };
  const r = verifyBundle(b, anchors, now);
  check(r.ok, "verifies as honest");
  check(r.conformance_observed === "L2", "conformance observed = L2");
  check(r.rederived.decision === "PERMITTED_CONFORMANT", "independent re-derivation = PERMITTED_CONFORMANT");
  check(r.implementer_key === "bridle", "record attributed to pinned implementer key 'bridle'");
}

console.log("2. honest REVOKED bundle (revoked, and the record says so)");
{
  const b: Bundle = { grant: makeGrant() as any, use, decision_record: makeRecord("REFUSED_REVOKED", "asset-revoked"), status_list: makeStatusList(new Set([IDX])), implementer: "bridle" };
  const r = verifyBundle(b, anchors, now);
  check(r.ok, "verifies as honest (revocation correctly reflected)");
  check(r.rederived.decision === "REFUSED_REVOKED", "independent re-derivation = REFUSED_REVOKED");
}

console.log("3. LYING implementer (asset revoked, but record claims PERMITTED) — must be caught");
{
  const b: Bundle = { grant: makeGrant() as any, use, decision_record: makeRecord("PERMITTED_CONFORMANT", "in-scope"), status_list: makeStatusList(new Set([IDX])), implementer: "bridle" };
  const r = verifyBundle(b, anchors, now);
  check(!r.ok, "NOT verified — the lie is caught");
  check(r.checks.some((c) => c.id === "decision.consistency" && c.status === "fail"), "decision.consistency fails");
}

console.log("4. tampered grant (scope changed after signing)");
{
  const g = makeGrant() as any;
  g.scope.purposes = ["hostile-deepfake"];
  const b: Bundle = { grant: g, use: { ...use, purpose: "hostile-deepfake" }, decision_record: makeRecord("PERMITTED_CONFORMANT", "in-scope"), status_list: makeStatusList(new Set()), implementer: "bridle" };
  const r = verifyBundle(b, anchors, now);
  check(!r.ok, "NOT verified — grant signatures fail");
  check(r.checks.some((c) => c.id === "grant.consent_signature" && c.status === "fail"), "consent signature fails");
}

console.log("5. issuer not in the pinned anchor set");
{
  const empty: Anchors = { issuers: {}, subjects: anchors.subjects, implementers: anchors.implementers };
  const b: Bundle = { grant: makeGrant() as any, use, decision_record: makeRecord("PERMITTED_CONFORMANT", "in-scope"), status_list: makeStatusList(new Set()), implementer: "bridle" };
  const r = verifyBundle(b, empty, now);
  check(!r.ok, "NOT verified — unpinned issuer namespace is untrusted");
  check(r.checks.some((c) => c.id === "grant.issuance_signature" && c.status === "fail"), "issuance signature fails (no anchor)");
}

if (failures > 0) { console.error(`\nSELFTEST FAIL: ${failures} check(s) failed`); process.exit(1); }
console.log("\nSELFTEST PASS — the verifier agrees with honest evidence and catches a lying implementer.");
