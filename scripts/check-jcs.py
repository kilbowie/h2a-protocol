#!/usr/bin/env python3
"""ADR-014 conformance gate — run interop/vectors/ through every implementation in this repo.

This is what turns ADR-014 from prose into a check. It asserts three things:

  1. The Python canonicaliser (reference/h2a_ref/jcs.py) reproduces every vector byte-for-byte.
  2. The TypeScript canonicaliser (reference/*/src/jcs.ts) does too.
  3. Every copy of jcs.ts is byte-identical to the others.

(3) matters as much as the first two. The reference stack is zero-dependency by design, so the
canonicaliser is duplicated per component rather than shared through a package — and unchecked
duplication is precisely what produced the estate's four-way split. The vectors catch a copy that
is WRONG; the byte-identity check catches a copy that is merely DIFFERENT, before it has a chance
to become wrong in a way no vector happens to cover.

Usage:  python scripts/check-jcs.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VECTORS = ROOT / "interop" / "vectors" / "vectors.json"
CANONICAL_JCS_TS = ROOT / "reference" / "verifier" / "src" / "jcs.ts"

# These scripts move UTF-8 between processes and print non-ASCII. Both need saying out loud on
# Windows, where the default is the locale codepage: without the first, "José" is mangled on the way
# INTO the subprocess and a conformant implementation is reported as failing; without the second,
# printing "R‖S" raises UnicodeEncodeError and takes the whole gate down. Both bit this file.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    if not ok:
        if detail:
            for line in detail.splitlines():
                print(f"       {line}")
        failures.append(label)


def main() -> int:
    sys.path.insert(0, str(ROOT / "reference"))
    from h2a_ref.jcs import jcs, jcs_bytes, der_to_raw, raw_to_der  # noqa: E402

    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    vectors = data["canonicalization_vectors"]

    # --- 1. Python -------------------------------------------------------
    print(f"\nPython — reference/h2a_ref/jcs.py ({len(vectors)} vectors)")
    for v in vectors:
        got = jcs(json.loads(v["input_json"]))
        check(v["id"], got == v["canonical"], f"got : {got}\nwant: {v['canonical']}")

    # --- 2. TypeScript ---------------------------------------------------
    # Driven out-of-process so this gate needs no Node toolchain to report the Python half, and so
    # a TypeScript syntax error surfaces as a failure rather than an import crash.
    print(f"\nTypeScript — {CANONICAL_JCS_TS.relative_to(ROOT)}")
    ts = subprocess.run(
        ts_runner() + [str(ROOT / "scripts" / "check-jcs.ts")],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    for line in (ts.stdout or "").splitlines():
        print(f"  {line}")
    if ts.returncode != 0:
        check("typescript vectors", False, (ts.stderr or "").strip()[:2000])

    # --- 3. copies are byte-identical ------------------------------------
    print("\njcs.ts copies are byte-identical")
    reference_bytes = CANONICAL_JCS_TS.read_bytes()
    copies = sorted((ROOT / "reference").glob("*/src/jcs.ts"))
    check("at least one copy exists", len(copies) >= 1)
    for c in copies:
        rel = c.relative_to(ROOT)
        check(str(rel), c.read_bytes() == reference_bytes,
              "differs from reference/verifier/src/jcs.ts — regenerate it with:\n"
              f"  cp {CANONICAL_JCS_TS.relative_to(ROOT)} {rel}")

    # --- 4. signature encoding round-trips -------------------------------
    print("\nsignature encoding (ADR-014 §2)")
    s = data["signature_vectors"]
    raw = b64u(s["signature_raw_r_s_base64url"])
    der = b64u(s["signature_same_signature_as_der_base64url"])
    check("preimage canonicalises to the vector",
          jcs_bytes(json.loads(s["preimage_input_json"])).decode() == s["preimage_canonical"])
    check("raw signature is 64 bytes", len(raw) == 64, f"got {len(raw)}")
    check("der_to_raw(der) == raw", der_to_raw(der) == raw)
    check("raw_to_der(raw) == der", raw_to_der(raw) == der)
    check("the committed raw signature verifies", verifies(s["public_key_pem"], s["preimage_canonical"], raw))

    print()
    if failures:
        print(f"FAILED — {len(failures)} check(s): {', '.join(failures[:6])}"
              + (" ..." if len(failures) > 6 else ""))
        return 1
    print("ADR-014 conformance: all implementations agree with the normative vectors.")
    return 0


def b64u(s: str) -> bytes:
    import base64
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def verifies(public_pem: str, message: str, raw_sig: bytes) -> bool:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    sys.path.insert(0, str(ROOT / "reference"))
    from h2a_ref.jcs import raw_to_der
    pub = load_pem_public_key(public_pem.encode())
    try:
        pub.verify(raw_to_der(raw_sig), message.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False


def ts_runner() -> list[str]:
    """How to run a .ts file here.

    tsx, not `node --experimental-strip-types`. The reference components import each other with the
    ESM `.js` extension convention (`import { jcs } from "./jcs.js"`), which type-stripping does not
    resolve back to `.ts`. tsx does, and it is already the sanctioned runner — every `npm run` script
    in reference/verifier uses it.

    Invoked as `node <tsx>/dist/cli.mjs` rather than through node_modules/.bin/tsx, because that
    entry is a shell script on Windows and subprocess raises WinError 193 on it. Going straight to
    the JS entry point sidesteps every platform's wrapper conventions.
    """
    from shutil import which
    node = which("node") or "node"
    cli = ROOT / "reference" / "verifier" / "node_modules" / "tsx" / "dist" / "cli.mjs"
    if cli.exists():
        return [node, str(cli)]
    # No local install (a bare checkout). npx resolves it, and needs its own wrapper on Windows.
    import os
    return [which("npx") or ("npx.cmd" if os.name == "nt" else "npx"), "--yes", "tsx"]


if __name__ == "__main__":
    raise SystemExit(main())
