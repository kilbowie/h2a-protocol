// Verify the `catches` metadata in vectors.json is true.
//
// Each vector claims which of the estate's non-conformant canonicalisers it detects. A claim like
// that is worth nothing unless it is executed: a vector that is SUPPOSED to catch a bug and quietly
// does not is worse than no vector, because it reports green over a real divergence.
//
// So this script re-implements the two known-bad canonicalisers verbatim and asserts, per vector,
// that each one fails exactly the vectors it is listed against — no more, no fewer. An over-claim
// (listed but passes) and an under-claim (not listed but fails) are both errors.
//
//   node interop/verify-catches.mjs
//
// `py-json-dumps` is verified by the companion verify_catches.py, which cannot be run from here
// without assuming a Python on PATH.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const { canonicalization_vectors: vectors } = JSON.parse(
  readFileSync(join(HERE, "vectors", "vectors.json"), "utf8"),
);

// Verbatim from reference/{verifier/src/crypto.ts,issuer-service/src/sign.ts,
// subject-signer/src/index.ts,witness-service/src/sign.ts} and Bridle packages/core/src/{sign,audit}.ts
// — the same eight lines copied six times. Reproduced here so the vectors are checked against what
// the estate actually runs, and so this file keeps failing until every copy is ported (S1.P3/S1.B2).
const tsLocaleCompare = (obj) =>
  JSON.stringify(obj, (_k, v) =>
    v && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b)))
      : v,
  );

const IMPL = "ts-localecompare";
let errors = 0;

console.log(`checking ${vectors.length} vectors against ${IMPL}\n`);
for (const v of vectors) {
  const claimed = v.catches.includes(IMPL);
  const actual = tsLocaleCompare(JSON.parse(v.input_json)) !== v.canonical;
  const ok = claimed === actual;
  if (!ok) errors++;
  const verdict = actual ? "DIVERGES" : "matches ";
  console.log(`  ${ok ? "ok  " : "FAIL"} ${v.id.padEnd(26)} ${verdict}  claimed=${claimed}`);
  if (!ok) {
    console.log(`       ${claimed ? "OVER-CLAIM: listed in catches but agrees with JCS"
                                  : "UNDER-CLAIM: diverges from JCS but is not listed"}`);
    console.log(`       hand-rolled : ${tsLocaleCompare(JSON.parse(v.input_json))}`);
    console.log(`       JCS         : ${v.canonical}`);
  }
}

const caught = vectors.filter((v) => v.catches.includes(IMPL)).length;
console.log(`\n${caught}/${vectors.length} vectors detect ${IMPL}; ${errors} metadata error(s).`);
process.exit(errors ? 1 : 0);
