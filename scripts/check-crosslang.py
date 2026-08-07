#!/usr/bin/env python3
"""Cross-language signature gate: Python signs, TypeScript verifies, and back again.

scripts/check-jcs.py proves each implementation agrees with the normative vectors. That is the
stronger check, but it is not this one. This asserts the property the vectors exist to guarantee:
a signature written by one language actually verifies in the other.

The distinction matters because the two can come apart. Every implementation in this repository had
a green selftest on 5 August 2026, and every one of them signed and verified with its OWN
canonicaliser — a closed loop agreeing with itself. Four of them disagreed with each other, and no
test in the estate was shaped to notice.

It also pins the negative: a DER signature must be REFUSED, not silently accepted. Without that,
"we emit raw R‖S" degrades into "we emit whatever, and everyone accepts everything", which is
where this started.

Usage:  python scripts/check-crosslang.py
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "reference"))

from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.hazmat.primitives.serialization import (  # noqa: E402
    Encoding, NoEncryption, PrivateFormat, PublicFormat, load_pem_public_key,
)

from h2a_ref.jcs import jcs, jcs_bytes, der_to_raw, raw_to_der  # noqa: E402

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
        for line in detail.splitlines():
            print(f"       {line}")
        failures.append(label)


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def main() -> int:
    # A document chosen to break every non-conformant implementation at once: a diacritic (Python's
    # ensure_ascii), a decimal cap (Python's float repr), mixed-case and integer-like keys (the
    # TypeScript localeCompare + object-rebuild pair).
    doc = {
        "grant_id": "urn:uuid:5f1d0c7e-9a3b-4c21-8e55-77b0a1d2f9c4",
        "subject_ref": "José Muñoz",
        "Use": ["advertising"],
        "lease": {"cap": 500.0, "currency": "GBP"},
        "10": "ten",
        "2": "two",
    }

    priv = ec.generate_private_key(ec.SECP256R1())
    priv_pem = priv.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()
    pub_pem = priv.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()

    payload = jcs_bytes(doc)
    py_sig_raw = der_to_raw(priv.sign(payload, ec.ECDSA(hashes.SHA256())))
    py_sig_der = priv.sign(payload, ec.ECDSA(hashes.SHA256()))

    print("\nPython signs -> TypeScript verifies")
    ts = subprocess.run(
        ts_runner() + [str(ROOT / "scripts" / "check-crosslang.ts")],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        input=json.dumps({
            "doc": doc,
            "canonical": jcs(doc),
            "publicKeyPem": pub_pem,
            "privateKeyPem": priv_pem,
            "signatureRaw": b64u(py_sig_raw),
            "signatureDer": b64u(py_sig_der),
        }),
    )
    for line in (ts.stdout or "").splitlines():
        print(f"  {line}")
        if line.strip().startswith("FAIL"):
            failures.append(line.strip())
    if ts.returncode != 0 and not failures:
        check("typescript side ran", False, (ts.stderr or "").strip()[:1500])

    # The TypeScript side echoes back what IT canonicalised and what IT signed.
    try:
        back = json.loads([l for l in (ts.stdout or "").splitlines() if l.startswith("{")][-1])
    except (IndexError, json.JSONDecodeError):
        check("typescript returned its own artefacts", False, (ts.stderr or "")[:800])
        return report()

    print("\nTypeScript signs -> Python verifies")
    check("both languages canonicalise to identical bytes", back["canonical"] == jcs(doc),
          f"ts : {back['canonical']}\npy : {jcs(doc)}")

    pub = load_pem_public_key(pub_pem.encode())
    ts_raw = base64.urlsafe_b64decode(back["signatureRaw"] + "=" * (-len(back["signatureRaw"]) % 4))
    check("the TypeScript raw R‖S signature is 64 bytes", len(ts_raw) == 64, f"got {len(ts_raw)}")

    try:
        pub.verify(raw_to_der(ts_raw), payload, ec.ECDSA(hashes.SHA256()))
        check("Python verifies the TypeScript signature", True)
    except Exception as exc:
        check("Python verifies the TypeScript signature", False, str(exc))

    # The negative. h2a_ref.verify.verify_sig must refuse DER outright.
    from h2a_ref.verify import verify_sig
    check("Python's verify_sig accepts raw R‖S", verify_sig(pub, payload, b64u(ts_raw)))
    check("Python's verify_sig REFUSES the same signature in DER",
          not verify_sig(pub, payload, b64u(raw_to_der(ts_raw))))
    check("Python's verify_sig refuses a tampered signature",
          not verify_sig(pub, jcs_bytes({**doc, "Use": ["political"]}), b64u(ts_raw)))

    return report()


def report() -> int:
    print()
    if failures:
        print(f"FAILED — {len(failures)} check(s)")
        return 1
    print("Cross-language: a signature written in either language verifies in the other.")
    return 0


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
