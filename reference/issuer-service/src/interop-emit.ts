// Interop harness: drive the real HTTP service and dump its signed artefacts to disk,
// so the Python reference verifier (scripts/check-interop.py) can prove it verifies a
// list this TypeScript issuer signed. Cross-language signature agreement is the whole
// point of ADR-009 — the authority is one key, checkable from any implementation.
import { buildIssuerService } from "./service.js";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const outDir = process.env.INTEROP_OUT ?? process.argv[2] ?? ".";
mkdirSync(outDir, { recursive: true });

const svc = buildIssuerService({ token: "dev-secret" });

svc.server.listen(0, async () => {
  const addr = svc.server.address();
  const port = typeof addr === "object" && addr ? addr.port : 0;
  const base = `http://127.0.0.1:${port}`;
  try {
    const pubkey = await (await fetch(`${base}/pubkey`)).json();
    const live = await (await fetch(`${base}/status/${svc.listId}`)).json();

    // The endpoint is not the authority — the token/key is. An unauthorized revoke
    // MUST be refused; if it weren't, the split ADR-009 describes would be fiction.
    const unauth = await fetch(`${base}/revoke`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ index: 7 }),
    });
    if (unauth.status !== 401) {
      throw new Error(`unauthorized revoke returned ${unauth.status}, expected 401`);
    }

    const revResp = await fetch(`${base}/revoke`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: "Bearer dev-secret" },
      body: JSON.stringify({ index: 42 }),
    });
    const rev = (await revResp.json()) as { status: unknown };

    writeFileSync(join(outDir, "pubkey.json"), JSON.stringify(pubkey, null, 2));
    writeFileSync(join(outDir, "status-live.json"), JSON.stringify(live, null, 2));
    writeFileSync(join(outDir, "status-revoked.json"), JSON.stringify(rev.status, null, 2));
    console.log(`interop artefacts written to ${outDir}`);
  } catch (err) {
    console.error(err);
    process.exitCode = 1;
  } finally {
    svc.server.close();
  }
});
