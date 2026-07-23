import { createServer, type Server } from "node:http";
import { generateKeyPairSync, createPrivateKey, createPublicKey, randomUUID } from "node:crypto";
import { pathToFileURL } from "node:url";
import { gzipSync } from "node:zlib";
import { readFileSync, writeFileSync } from "node:fs";
import { signObject, signDetached } from "./sign.js";

const SIZE_BITS = 1024;
const TTL_MS = 60 * 60 * 1000;

function encodeBitstring(revoked: Set<number>): string {
  const bytes = Buffer.alloc(SIZE_BITS / 8);
  for (const i of revoked) if (i >= 0 && i < SIZE_BITS) bytes[i >> 3] |= 1 << (i & 7);
  return gzipSync(bytes).toString("base64url");
}

export interface IssuerService {
  server: Server;
  publicKeyPem: string;
  listId: string;
  iss: string;
}

// The revocation authority. Holds the private signing key; nobody else can produce a valid list.
//
// Key/list custody (durable vs ephemeral). By default (nothing set) the signing key and listId are
// generated PER PROCESS — a restart changes the trust anchor Bridle pinned at boot, and every prior
// `status.uri` 404s. That is fine for a driven local demo but NOT for a hosted deployment. For a stable
// deployment, set (mirroring the witness's WITNESS_SIGNING_KEY):
//   ISSUER_SIGNING_KEY  — a durable EC P-256 PKCS8 PEM (the whole authority; keep it a real secret)
//   ISSUER_LIST_ID      — a stable status-list id, so published `status.uri`s survive restarts
//   ISSUER_ISS          — the issuer namespace (default kept for local/interop; override in prod)
//   ISSUER_REVOKED_PATH — optional JSON file (on a persistent volume) so live revokes survive a restart
// Real fiduciary custody (a KMS the Bridle deployment cannot reach) is the follow-on — see RUNBOOK §1.
export function buildIssuerService(opts?: {
  token?: string;
  iss?: string;
  signingKeyPem?: string;
  listId?: string;
  revokedPath?: string;
}): IssuerService {
  const token = opts?.token ?? process.env.FIDUCIARY_TOKEN ?? "dev-secret";
  // .trim() the identity values: a stray trailing space pasted into ISSUER_ISS / ISSUER_LIST_ID env
  // otherwise lands in `iss`/`kid` and every grant's status.uri — and `iss` is a schema `format: uri`,
  // so a trailing space makes Bridle reject every grant with grant-schema-invalid.
  const iss = (opts?.iss ?? process.env.ISSUER_ISS ?? "https://issuer.example.org/h2a/issuer").trim();
  const listId = (opts?.listId ?? process.env.ISSUER_LIST_ID ?? randomUUID()).trim();
  const issuerKid = `${iss}#issuance`; // interim: one key signs both the status list and grant issuance
  const revokedPath = opts?.revokedPath ?? process.env.ISSUER_REVOKED_PATH;

  // Load a durable signing key if provided (env may carry \n-escaped PEM), else generate an ephemeral one.
  let privateKeyPem: string;
  const durableKey = opts?.signingKeyPem ?? process.env.ISSUER_SIGNING_KEY;
  if (durableKey) {
    // Normalise + validate: accept a real-newline or \n-escaped PKCS8 PEM, re-export canonically.
    const pem = durableKey.includes("\\n") ? durableKey.replace(/\\n/g, "\n") : durableKey;
    privateKeyPem = createPrivateKey(pem).export({ type: "pkcs8", format: "pem" }).toString();
  } else {
    const { privateKey } = generateKeyPairSync("ec", { namedCurve: "P-256" });
    privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" }).toString();
    console.warn(
      "ISSUER_SIGNING_KEY not set — generated an EPHEMERAL key; a restart changes the trust anchor and " +
        "invalidates every previously published status list. Set it for a hosted deployment (see RUNBOOK §1).",
    );
  }
  const publicKeyPem = createPublicKey(privateKeyPem).export({ type: "spki", format: "pem" }).toString();

  // Revoked set: optionally durable via a JSON file on a volume, so a live revoke survives a restart.
  const revoked = new Set<number>();
  if (revokedPath) {
    try {
      for (const i of JSON.parse(readFileSync(revokedPath, "utf8")) as number[]) revoked.add(i);
    } catch { /* absent/unreadable on first boot — start empty */ }
  }
  const persistRevoked = () => {
    if (!revokedPath) return;
    try { writeFileSync(revokedPath, JSON.stringify([...revoked])); }
    catch (e) { console.error(`could not persist revoked set to ${revokedPath}:`, (e as Error).message); }
  };

  function signedList() {
    const now = Date.now();
    const list: Record<string, unknown> = {
      h2a_version: "0.1",
      status_list_id: listId,
      iss,
      purpose: "revocation",
      encoding: "base64url-bitstring",
      list: encodeBitstring(revoked),
      valid_from: new Date(now).toISOString(),
      valid_until: new Date(now + TTL_MS).toISOString(),
      alg: "ES256",
    };
    list.signature = signObject(privateKeyPem, list); // REAL ES256 — the authority lives in this key
    return list;
  }

  const send = (res: any, code: number, body: unknown) => {
    res.writeHead(code, { "content-type": "application/json" });
    res.end(JSON.stringify(body));
  };

  const server = createServer((req, res) => {
    const url = new URL(req.url ?? "/", "http://localhost");
    if (req.method === "GET" && url.pathname === "/pubkey")
      return send(res, 200, { publicKeyPem, iss, listId, kid: issuerKid });
    if (req.method === "GET" && url.pathname === `/status/${listId}`)
      return send(res, 200, signedList());
    if (req.method === "GET" && url.pathname.startsWith("/status/"))
      return send(res, 404, { error: "unknown-status-list" });
    // Sign the ISSUANCE half of a grant (ADR-004). The issuer attests it issued this grant;
    // the fiduciary token gates it, just like revocation. Consent is signed separately by the subject.
    if (req.method === "POST" && url.pathname === "/sign-grant") {
      const auth = req.headers.authorization ?? "";
      if (auth !== `Bearer ${token}`)
        return send(res, 401, { error: "issuance-requires-issuer-authority" });
      let raw = "";
      req.on("data", (c) => (raw += c));
      req.on("end", () => {
        try {
          const grant = JSON.parse(raw || "{}") as Record<string, unknown>;
          const value = signDetached(privateKeyPem, grant);
          return send(res, 200, { role: "issuance", kid: issuerKid, value });
        } catch {
          return send(res, 400, { error: "bad-body" });
        }
      });
      return;
    }
    if (req.method === "POST" && url.pathname === "/revoke") {
      const auth = req.headers.authorization ?? "";
      if (auth !== `Bearer ${token}`)
        return send(res, 401, { error: "revocation-requires-fiduciary-authority" });
      let raw = "";
      req.on("data", (c) => (raw += c));
      req.on("end", () => {
        try {
          const { index } = JSON.parse(raw || "{}") as { index: number };
          if (typeof index !== "number") return send(res, 400, { error: "index-required" });
          revoked.add(index);
          persistRevoked();
          return send(res, 200, { revoked: true, status: signedList() });
        } catch {
          return send(res, 400, { error: "bad-body" });
        }
      });
      return;
    }
    return send(res, 404, { error: "not-found" });
  });

  return { server, publicKeyPem, listId, iss };
}

// Standalone start. pathToFileURL so argv[1] matches import.meta.url on Windows too (drive letter,
// backslashes) as well as macOS/Linux — a raw `file://${argv[1]}` never matches on Windows.
const isMain = !!process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const svc = buildIssuerService();
  const port = Number(process.env.PORT ?? 8790);
  svc.server.listen(port, () => {
    const durable = !!process.env.ISSUER_SIGNING_KEY;
    console.log(`issuer/status service on :${port}`);
    console.log(`  key custody:    ${durable ? "DURABLE (ISSUER_SIGNING_KEY)" : "EPHEMERAL (per-process)"}`);
    console.log(`  status list id: ${svc.listId}${process.env.ISSUER_LIST_ID ? " (pinned)" : " (generated)"}`);
    console.log(`  iss:            ${svc.iss}`);
    console.log(`  pubkey at:      GET /pubkey`);
    console.log(`  list at:        GET /status/${svc.listId}`);
  });
}
