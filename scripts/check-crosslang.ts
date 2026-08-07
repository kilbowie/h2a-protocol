// TypeScript half of the cross-language signature gate. Driven by scripts/check-crosslang.py,
// which sends a document plus a Python-produced signature on stdin and reads this side's
// canonicalisation and signature back on stdout as the last JSON line.
import { readFileSync } from "node:fs";
import { sign as cryptoSign } from "node:crypto";
import { jcs, jcsBytes } from "../reference/verifier/src/jcs.ts";
import { verifyObject } from "../reference/verifier/src/crypto.ts";

interface Input {
  doc: Record<string, unknown>;
  canonical: string;
  publicKeyPem: string;
  privateKeyPem: string;
  signatureRaw: string;
  signatureDer: string;
}

const input: Input = JSON.parse(readFileSync(0, "utf8"));
let failed = 0;

const check = (label: string, ok: boolean, detail = ""): void => {
  console.log(`${ok ? "ok  " : "FAIL"} ${label}`);
  if (!ok) {
    failed++;
    for (const line of detail.split("\n").filter(Boolean)) console.log(`     ${line}`);
  }
};

const canonical = jcs(input.doc);
check("both languages canonicalise to identical bytes", canonical === input.canonical,
  `ts : ${canonical}\npy : ${input.canonical}`);

// verifyObject strips a `signature` member and verifies over the rest — so hand it the document
// with the Python signature attached, exactly as it would arrive on the wire.
check("TypeScript verifies the Python signature",
  verifyObject(input.publicKeyPem, { ...input.doc, signature: input.signatureRaw }));

check("TypeScript REFUSES the same signature in DER",
  !verifyObject(input.publicKeyPem, { ...input.doc, signature: input.signatureDer }));

check("TypeScript refuses a tampered document",
  !verifyObject(input.publicKeyPem, { ...input.doc, Use: ["political"], signature: input.signatureRaw }));

const signatureRaw = cryptoSign("sha256", jcsBytes(input.doc), {
  key: input.privateKeyPem,
  dsaEncoding: "ieee-p1363",
}).toString("base64url");

// Last stdout line: what THIS side canonicalised and signed, for the Python half to check.
console.log(JSON.stringify({ canonical, signatureRaw }));
process.exit(failed ? 1 : 0);
