import { canonical, verifyObject, verifyDetached, isRevoked } from "./crypto.js";

// h2a-verify — the standalone, independent verifier.
//
// It is given an evidence BUNDLE (a grant, the use, the implementer's signed decision record, and the
// issuer's signed status list) plus a pinned set of trust ANCHORS, and it re-derives the decision from
// first principles — it never trusts the implementer's own record. Trust anchors are resolved by
// ISSUER NAMESPACE (the `iss` URL), from a set the operator pins; the implementer being checked never
// supplies them. See ADR-010. Today those anchors are founder-operated; the only thing the future
// changes is WHERE the namespace resolves and WHO governs the anchor set — not this code.

export interface Anchors {
  // Keyed by issuer namespace (grant.iss / status_list.iss). Unknown namespace = untrusted.
  issuers: Record<string, { public_key_pem: string; custodian?: string; endpoint?: string }>;
  // Keyed by subject_ref (enroll-with-pubkey, ADR-003).
  subjects: Record<string, { public_key_pem: string }>;
  // Keyed by implementer name; the party being CHECKED. Its key is pinned so it cannot swap keys.
  implementers: Record<string, { public_key_pem: string; endpoint?: string }>;
}

interface Grant {
  grant_id: string;
  iss: string;
  subject_ref: string;
  scope: { purposes: string[]; territories?: string[]; exclusions?: string[] };
  lease?: { cap: number; nbf: string; exp: string };
  status: { uri: string; mirrors?: string[]; index: number };
  signatures: { role: string; kid: string; value: string }[];
  nbf: string;
  exp: string;
}

export interface Bundle {
  grant: Grant;
  use: { purpose: string; territory: string; spend?: number };
  decision_record: Record<string, unknown>;
  status_list: Record<string, unknown>;
  attestation?: Record<string, unknown>;
  implementer?: string; // name into anchors.implementers; if absent, every implementer key is tried
}

export type CheckStatus = "pass" | "fail" | "not_evaluated";
export interface Check {
  id: string;
  level: "L1" | "L2" | "L3";
  status: CheckStatus;
  detail: string;
}
export interface Report {
  ok: boolean; // no evaluated check failed — the record is an HONEST reflection of the evidence
  conformance_observed: "none" | "L1" | "L2";
  rederived: { decision: string; reason: string };
  record: { decision: string; reason: string };
  implementer_key: string | null; // which pinned implementer key verified the record, if any
  checks: Check[];
}

function within(nowMs: number, nbf: string, exp: string): boolean {
  return nowMs >= Date.parse(nbf) && nowMs <= Date.parse(exp);
}

// Independent re-implementation of the SPEC-CORE §4 decision — the whole point of the verifier is that
// this does NOT call the implementer. `sigOk` and `revoked` are the facts the checks above established;
// `revoked` is already fail-closed (true when the status list could not be trusted).
function rederive(
  grant: Grant,
  use: Bundle["use"],
  sigOk: boolean,
  windowOk: boolean,
  revoked: boolean,
  statusUsable: boolean,
): { decision: string; reason: string } {
  if (!sigOk) return { decision: "REFUSED_OUT_OF_SCOPE", reason: "grant-signature-invalid" };
  if (!windowOk) return { decision: "REFUSED_OUT_OF_SCOPE", reason: "grant-outside-validity-window" };
  if (!statusUsable) return { decision: "REFUSED_REVOKED", reason: "status-fail-closed" };
  if (revoked) return { decision: "REFUSED_REVOKED", reason: "asset-revoked" };

  const s = grant.scope;
  if ((s.exclusions ?? []).includes(use.purpose))
    return { decision: "REFUSED_OUT_OF_SCOPE", reason: `excluded:${use.purpose}` };
  if (!s.purposes.includes(use.purpose))
    return { decision: "REFUSED_OUT_OF_SCOPE", reason: `purpose-not-granted:${use.purpose}` };
  const terr = s.territories;
  if (terr && !terr.includes("GLOBAL") && !terr.includes(use.territory))
    return { decision: "REFUSED_OUT_OF_SCOPE", reason: `territory-not-granted:${use.territory}` };

  if (grant.lease) {
    if (!within(Date.now(), grant.lease.nbf, grant.lease.exp))
      return { decision: "REFUSED_LEASE_EXHAUSTED", reason: "lease-outside-window" };
    if ((use.spend ?? 0) > grant.lease.cap)
      return { decision: "REFUSED_LEASE_EXHAUSTED", reason: "lease-cap-exceeded" };
  }
  return { decision: "PERMITTED_CONFORMANT", reason: "in-scope" };
}

export function verifyBundle(bundle: Bundle, anchors: Anchors, now = new Date()): Report {
  const nowMs = now.getTime();
  const { grant, use, decision_record: rec, status_list: list } = bundle;
  const checks: Check[] = [];
  const add = (id: string, level: Check["level"], status: CheckStatus, detail: string) =>
    checks.push({ id, level, status, detail });

  // Resolve anchors BY NAMESPACE — the implementer never supplies these.
  const issuerAnchor = anchors.issuers[grant.iss];
  const subjectAnchor = anchors.subjects[grant.subject_ref];

  // --- L1: the grant's two detached signatures + validity window ---
  const consent = grant.signatures?.find((s) => s.role === "consent");
  const issuance = grant.signatures?.find((s) => s.role === "issuance");

  let consentOk = false;
  if (!subjectAnchor) add("grant.consent_signature", "L1", "fail", `no pinned anchor for subject ${grant.subject_ref}`);
  else if (!consent) add("grant.consent_signature", "L1", "fail", "consent signature absent");
  else {
    consentOk = verifyDetached(subjectAnchor.public_key_pem, grant as unknown as Record<string, unknown>, consent.value);
    add("grant.consent_signature", "L1", consentOk ? "pass" : "fail", consentOk ? "consent signature verifies against the subject's pinned key" : "consent signature does not verify");
  }

  let issuanceOk = false;
  if (!issuerAnchor) add("grant.issuance_signature", "L1", "fail", `no pinned anchor for issuer namespace ${grant.iss}`);
  else if (!issuance) add("grant.issuance_signature", "L1", "fail", "issuance signature absent");
  else {
    issuanceOk = verifyDetached(issuerAnchor.public_key_pem, grant as unknown as Record<string, unknown>, issuance.value);
    add("grant.issuance_signature", "L1", issuanceOk ? "pass" : "fail", issuanceOk ? "issuance signature verifies against the issuer's pinned key" : "issuance signature does not verify");
  }

  const windowOk = within(nowMs, grant.nbf, grant.exp);
  add("grant.validity_window", "L1", windowOk ? "pass" : "fail", windowOk ? "now is within [nbf, exp]" : "grant is outside its validity window");

  // --- L2: the issuer's signed status list (fetch-and-verify; fail closed) ---
  const statusSigOk = issuerAnchor ? verifyObject(issuerAnchor.public_key_pem, list) : false;
  add("status_list.signature", "L2", statusSigOk ? "pass" : "fail", statusSigOk ? "status list signature verifies against the issuer's pinned key" : "status list signature does not verify (or issuer unpinned)");

  const issuerMatch = list.iss === grant.iss;
  add("status_list.issuer_match", "L2", issuerMatch ? "pass" : "fail", issuerMatch ? "status list iss matches the grant's issuer" : `status list iss (${String(list.iss)}) != grant iss (${grant.iss})`);

  const fresh = nowMs <= Date.parse(String(list.valid_until));
  add("status_list.freshness", "L2", fresh ? "pass" : "fail", fresh ? "status list is within valid_until" : "status list is stale");

  const statusUsable = statusSigOk && issuerMatch && fresh;
  let revoked = true; // fail closed until proven clear
  if (statusUsable) {
    revoked = isRevoked(String(list.list), grant.status.index);
    add("status_list.revocation_bit", "L2", "pass", `revocation bit at index ${grant.status.index} = ${revoked ? "REVOKED" : "clear"}`);
  } else {
    add("status_list.revocation_bit", "L2", "fail", "status list unusable — revocation treated as fail-closed");
  }

  // --- L2: the implementer's own signed decision record (pinned key; it cannot swap keys) ---
  let implKeyName: string | null = null;
  let recSigOk = false;
  const candidates = bundle.implementer
    ? (anchors.implementers[bundle.implementer] ? [[bundle.implementer, anchors.implementers[bundle.implementer]] as const] : [])
    : Object.entries(anchors.implementers);
  for (const [name, a] of candidates) {
    if (verifyObject(a.public_key_pem, rec)) { recSigOk = true; implKeyName = name; break; }
  }
  add("decision_record.signature", "L2", recSigOk ? "pass" : "fail", recSigOk ? `decision record verifies against pinned implementer key "${implKeyName}"` : "decision record does not verify against any pinned implementer key");

  // --- L1 core: re-derive the decision independently and compare to the record's claim ---
  const rd = rederive(grant, use, consentOk && issuanceOk, windowOk, revoked, statusUsable);
  const recDecision = String(rec.decision ?? "");
  const recReason = String(rec.reason_code ?? "");
  const consistent = rd.decision === recDecision;
  add("decision.consistency", "L1", consistent ? "pass" : "fail",
    consistent ? `independent re-derivation agrees: ${rd.decision}` : `record claims ${recDecision} but independent re-derivation gives ${rd.decision}`);

  // --- L3: not evaluated (no external anchoring in the bundle) ---
  add("anchoring.eidas_timestamp", "L3", "not_evaluated", "no eIDAS-qualified timestamp in bundle (Sprint: L3)");
  add("anchoring.witness_cosignature", "L3", "not_evaluated", "no independent witness co-signature in bundle (Sprint: L3)");

  const failed = (level: Check["level"]) => checks.some((c) => c.level === level && c.status === "fail");
  const l1ok = !failed("L1");
  const l2ok = !failed("L2");
  const conformance_observed = l1ok && l2ok ? "L2" : l1ok ? "L1" : "none";

  return {
    ok: !checks.some((c) => c.status === "fail"),
    conformance_observed,
    rederived: rd,
    record: { decision: recDecision, reason: recReason },
    implementer_key: implKeyName,
    checks,
  };
}

// Human-readable one-line-per-check report.
export function formatReport(r: Report): string {
  const mark = (s: CheckStatus) => (s === "pass" ? "PASS" : s === "fail" ? "FAIL" : "n/e ");
  const lines = r.checks.map((c) => `  [${mark(c.status)}] ${c.level} ${c.id} — ${c.detail}`);
  const head = r.ok
    ? `VERIFIED — the decision record is an honest reflection of the evidence (${r.conformance_observed}).`
    : `NOT VERIFIED — the record and the evidence disagree, or a signature failed.`;
  const derived = `  re-derived: ${r.rederived.decision} (${r.rederived.reason}) · record claims: ${r.record.decision} (${r.record.reason})`;
  return [head, ...lines, derived].join("\n");
}
