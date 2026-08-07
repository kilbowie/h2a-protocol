// TypeScript half of the ADR-014 conformance gate. Driven by scripts/check-jcs.py; run directly
// with:  node --experimental-strip-types scripts/check-jcs.ts
//
// Checks the canonicaliser against every vector, then the signature-encoding contract: the
// committed raw R‖S signature must verify under the JOSE encoding, and the identical signature in
// DER must NOT — because if both verified there would be nothing for ADR-014 §2 to decide.
import { readFileSync } from "node:fs";
import { verify as cryptoVerify } from "node:crypto";
import { jcs, jcsBytes, derToRaw, rawToDer } from "../reference/verifier/src/jcs.ts";

const data = JSON.parse(readFileSync("interop/vectors/vectors.json", "utf8"));
let failed = 0;

const check = (label: string, ok: boolean, detail = ""): void => {
  console.log(`${ok ? "ok  " : "FAIL"} ${label}`);
  if (!ok) {
    failed++;
    for (const line of detail.split("\n").filter(Boolean)) console.log(`     ${line}`);
  }
};

for (const v of data.canonicalization_vectors) {
  const got = jcs(JSON.parse(v.input_json));
  check(v.id, got === v.canonical, `got : ${got}\nwant: ${v.canonical}`);
}

const s = data.signature_vectors;
const raw = Buffer.from(s.signature_raw_r_s_base64url, "base64url");
const der = Buffer.from(s.signature_same_signature_as_der_base64url, "base64url");
const preimage = jcsBytes(JSON.parse(s.preimage_input_json));

check("preimage canonicalises to the vector", preimage.toString("utf8") === s.preimage_canonical);
check("derToRaw(der) === raw", derToRaw(der).equals(raw));
check("rawToDer(raw) === der", rawToDer(raw).equals(der));
check(
  "raw R‖S verifies under ieee-p1363",
  cryptoVerify("sha256", preimage, { key: s.public_key_pem, dsaEncoding: "ieee-p1363" }, raw),
);
check(
  "the same signature in DER does NOT verify under ieee-p1363",
  !cryptoVerify("sha256", preimage, { key: s.public_key_pem, dsaEncoding: "ieee-p1363" }, der),
);

process.exit(failed ? 1 : 0);
