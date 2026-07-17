#!/usr/bin/env python3
"""H2A static site generator.

Content model (resist adding more): write markdown, add one row to PAGES, rebuild.
Also copies schemas/ into the site so every schema $id resolves once hosted at h2a-protocol.org.
"""
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "_out"
CONTENT = ROOT / "site" / "content"
SPEC = ROOT / "spec"
ADR = SPEC / "adr"


def adr_slug(path: Path) -> str:
    """ADR-009-revocation-authority.md -> adr-009.html — the name the specs cite."""
    return f"adr-{path.stem.split('-')[1]}.html"


# (source markdown, output path, nav title)  — nav title "" means not in top nav
PAGES = [
    (CONTENT / "index.md", "index.html", "Home"),
    (CONTENT / "verification.md", "verification.html", "How it verifies"),
    (SPEC / "SPEC-CORE.md", "spec-core.html", "Spec"),
    (SPEC / "SPEC-MEDIA.md", "spec-media.html", ""),
    (SPEC / "SPEC-MEMORY.md", "spec-memory.html", ""),
    (SPEC / "CONFORMANCE.md", "conformance.html", "Conformance"),
    (SPEC / "THREAT-MODEL.md", "threat-model.html", ""),
    (CONTENT / "schemas.md", "schemas.html", "Schemas"),
    (CONTENT / "decisions.md", "decisions.html", "Decisions"),
    (CONTENT / "governance.md", "governance.html", "Governance"),
]

# ADRs publish by convention, not by hand — a new ADR-0NN appears on the site by existing.
PAGES += [(p, adr_slug(p), "") for p in sorted(ADR.glob("ADR-*.md"))]

BANNER = ('<div class="banner">Working draft — the v0.x wire format may change. '
          'H2A is not yet a ratified standard.</div>')

TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · H2A</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<style>
:root {{ --ink:#171717; --paper:#fafafa; --rule:#e5e5e5; --mut:#666; }}
@font-face {{ font-family:Geist; src:url(https://cdn.jsdelivr.net/npm/geist@1/dist/fonts/geist-sans/Geist-Regular.woff2) format('woff2'); font-weight:400; font-display:swap; }}
@font-face {{ font-family:Geist; src:url(https://cdn.jsdelivr.net/npm/geist@1/dist/fonts/geist-sans/Geist-SemiBold.woff2) format('woff2'); font-weight:600; font-display:swap; }}
* {{ box-sizing:border-box; }}
body {{ font-family:Geist,ui-sans-serif,system-ui,sans-serif; color:var(--ink); background:var(--paper);
  max-width:44rem; margin:0 auto; padding:2rem 1.25rem 5rem; line-height:1.6; font-size:17px; }}
.banner {{ background:var(--ink); color:var(--paper); font-size:13px; padding:.55rem .8rem; border-radius:6px; margin-bottom:2rem; }}
nav {{ display:flex; gap:1.1rem; flex-wrap:wrap; font-size:14px; border-bottom:1px solid var(--rule); padding-bottom:1rem; margin-bottom:2rem; }}
nav a {{ color:var(--mut); text-decoration:none; }} nav a:hover {{ color:var(--ink); }}
h1 {{ font-weight:600; font-size:2rem; letter-spacing:-.02em; line-height:1.15; }}
h2 {{ font-weight:600; margin-top:2.4rem; letter-spacing:-.01em; }}
h3 {{ font-weight:600; font-size:1.05rem; margin-top:1.8rem; }}
a {{ color:var(--ink); }}
code {{ background:#f0f0f0; padding:.1em .35em; border-radius:4px; font-size:.9em; }}
pre {{ background:#f0f0f0; padding:1rem; border-radius:8px; overflow:auto; }}
pre code {{ background:none; padding:0; }}
table {{ border-collapse:collapse; width:100%; font-size:15px; margin:1rem 0; }}
th,td {{ border:1px solid var(--rule); padding:.5rem .7rem; text-align:left; vertical-align:top; }}
th {{ background:#f0f0f0; font-weight:600; }}
blockquote {{ border-left:3px solid var(--ink); margin:1.4rem 0; padding:.2rem 0 .2rem 1rem; color:var(--mut); }}
footer {{ margin-top:4rem; padding-top:1.5rem; border-top:1px solid var(--rule); font-size:13px; color:var(--mut); }}
</style></head><body>
{banner}
<nav>{nav}</nav>
<main>{body}</main>
<footer>H2A Protocol · working draft · <a href="https://h2a-protocol.org">h2a-protocol.org</a>.
Spec text CC BY 4.0; schemas &amp; code Apache-2.0.</footer>
</body></html>"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    nav = " ".join(
        f'<a href="{out}">{title}</a>' for _, out, title in PAGES if title
    )
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])

    for src, out, title in PAGES:
        md.reset()
        body = md.convert(Path(src).read_text())
        html = TEMPLATE.format(title=title or "H2A", banner=BANNER, nav=nav, body=body)
        (OUT / out).write_text(html)

    # publish schemas so every $id resolves under the hosted domain
    shutil.copytree(ROOT / "schemas", OUT / "schemas")
    (OUT / "CNAME").write_text("h2a-protocol.org\n")

    print(f"built {len(PAGES)} pages + schemas -> {OUT}")


if __name__ == "__main__":
    build()
