import { createServer, type Server } from "node:http";
import { generateKeyPairSync, createPublicKey } from "node:crypto";
import { signObject } from "./sign.js";

// Reference INDEPENDENT WITNESS service (ADR-005 · L3). A second party that co-signs an implementer's
// audit-chain head, so the record does not rest on the recording party's word alone. It holds its OWN
// key in its OWN trust domain — it is deliberately NOT the implementer and NOT the issuer. The v0 is an
// independent witness service; a fiduciary-operated witness takes custody later (no on-wire change).
//
// It witnesses only WHAT IT IS TOLD (a head hash + seq) at the time it is asked — it does not, and need
// not, understand the chain. Its value is that its signature + clock are outside the implementer's reach.

export interface WitnessCosignature {
  witness: string;
  hashed: string;
  seq: number;
  cosigned_at: string;
  alg: "ES256";
  signature: string;
}

export interface WitnessService {
  server: Server;
  publicKeyPem: string;
  witness: string;
}

export function buildWitnessService(opts?: { witness?: string; privateKeyPem?: string; now?: () => Date }): WitnessService {
  const witness = opts?.witness ?? process.env.WITNESS_ID ?? "urn:h2a:witness:reference";
  const clock = opts?.now ?? (() => new Date());

  let privateKeyPem = opts?.privateKeyPem ?? process.env.WITNESS_SIGNING_KEY;
  if (!privateKeyPem) {
    const { privateKey } = generateKeyPairSync("ec", { namedCurve: "P-256" });
    privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" }).toString();
  }
  const publicKeyPem = createPublicKey(privateKeyPem).export({ type: "spki", format: "pem" }).toString();

  const send = (res: any, code: number, body: unknown) => {
    res.writeHead(code, { "content-type": "application/json" });
    res.end(JSON.stringify(body));
  };

  const server = createServer((req, res) => {
    const url = new URL(req.url ?? "/", "http://localhost");
    if (req.method === "GET" && url.pathname === "/pubkey")
      return send(res, 200, { publicKeyPem, witness });

    // Co-sign a head hash + seq. No auth: witnessing is a public, append-only attestation — a witness
    // gains nothing by refusing and forges nothing by signing (it signs only what it is handed).
    if (req.method === "POST" && url.pathname === "/cosign") {
      let raw = "";
      req.on("data", (c) => (raw += c));
      req.on("end", () => {
        try {
          const { head_hash, seq } = JSON.parse(raw || "{}") as { head_hash?: string; seq?: number };
          if (typeof head_hash !== "string" || typeof seq !== "number")
            return send(res, 400, { error: "head_hash (string) and seq (number) required" });
          const cosig: WitnessCosignature = {
            witness, hashed: head_hash, seq, cosigned_at: clock().toISOString(), alg: "ES256", signature: "",
          };
          cosig.signature = signObject(privateKeyPem!, cosig as unknown as Record<string, unknown>);
          return send(res, 200, cosig);
        } catch {
          return send(res, 400, { error: "bad-body" });
        }
      });
      return;
    }
    return send(res, 404, { error: "not-found" });
  });

  return { server, publicKeyPem, witness };
}

// Standalone start.
const isMain = import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  const svc = buildWitnessService();
  const port = Number(process.env.PORT ?? 8791);
  svc.server.listen(port, () => {
    console.log(`witness service on :${port} (${svc.witness})`);
    console.log(`  pubkey at:  GET /pubkey`);
    console.log(`  cosign at:  POST /cosign { head_hash, seq }`);
  });
}
