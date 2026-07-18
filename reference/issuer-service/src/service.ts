import { createServer, type Server } from "node:http";
import { generateKeyPairSync, randomUUID } from "node:crypto";
import { gzipSync } from "node:zlib";
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
export function buildIssuerService(opts?: {
  token?: string;
  iss?: string;
}): IssuerService {
  const token = opts?.token ?? process.env.FIDUCIARY_TOKEN ?? "dev-secret";
  const iss = opts?.iss ?? "https://issuer.example.org/h2a/issuer";
  const listId = randomUUID();
  const issuerKid = `${iss}#issuance`; // interim: one key signs both the status list and grant issuance
  const revoked = new Set<number>();

  const { privateKey, publicKey } = generateKeyPairSync("ec", { namedCurve: "P-256" });
  const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" }).toString();
  const publicKeyPem = publicKey.export({ type: "spki", format: "pem" }).toString();

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

// Standalone start.
const isMain = import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  const svc = buildIssuerService();
  const port = Number(process.env.PORT ?? 8790);
  svc.server.listen(port, () => {
    console.log(`issuer/status service on :${port}`);
    console.log(`  status list id: ${svc.listId}`);
    console.log(`  pubkey at:      GET /pubkey`);
    console.log(`  list at:        GET /status/${svc.listId}`);
  });
}
