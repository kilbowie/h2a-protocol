"""Verify the `py-json-dumps` entries in vectors.json `catches` are true.

Companion to verify-catches.mjs. Same contract: each vector claims which non-conformant
canonicaliser it detects, and a claim that is never executed is not evidence. Both an over-claim
(listed but agrees) and an under-claim (diverges but not listed) fail this script.

    python interop/verify_catches.py

Stdlib only, so it runs anywhere the reference package does.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL = "py-json-dumps"

with open(os.path.join(HERE, "vectors", "vectors.json"), encoding="utf-8") as fh:
    vectors = json.load(fh)["canonicalization_vectors"]


def py_json_dumps(obj):
    """Verbatim from reference/h2a_ref/verify.py:28 — the canonicaliser the Python reference ships."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


errors = 0
print(f"checking {len(vectors)} vectors against {IMPL}\n")
for v in vectors:
    claimed = IMPL in v["catches"]
    # Parse the AUTHORED TEXT. Reading a pre-parsed value would hand Python a number that
    # JavaScript had already normalised, and the vector would stop testing its own claim.
    actual = py_json_dumps(json.loads(v["input_json"])) != v["canonical"]
    ok = claimed == actual
    if not ok:
        errors += 1
    verdict = "DIVERGES" if actual else "matches "
    print(f"  {'ok  ' if ok else 'FAIL'} {v['id']:<26} {verdict}  claimed={claimed}")
    if not ok:
        print("       " + ("OVER-CLAIM: listed in catches but agrees with JCS" if claimed
                           else "UNDER-CLAIM: diverges from JCS but is not listed"))
        got = py_json_dumps(json.loads(v["input_json"]))
        print(f"       json.dumps : {got}")
        print(f"       JCS        : {v['canonical']}")

caught = sum(1 for v in vectors if IMPL in v["catches"])
print(f"\n{caught}/{len(vectors)} vectors detect {IMPL}; {errors} metadata error(s).")
sys.exit(1 if errors else 0)
