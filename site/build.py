#!/usr/bin/env python3
"""H2A static site generator.

Content model (resist adding more): write markdown, add one row to PAGES, rebuild.
The schemas page is the exception — its body is generated from the schema JSON by
schema_doc.render_reference (one source of truth, never hand-maintained).
Also copies schemas/ into the site so every schema $id resolves once hosted at h2a-protocol.org.
"""
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

import schema_doc

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "_out"
CONTENT = ROOT / "site" / "content"
SPEC = ROOT / "spec"
ADR = SPEC / "adr"
SCHEMA_DIR = ROOT / "schemas" / "v0"
EXAMPLE_DIR = SCHEMA_DIR / "examples"

SCHEMA_MARKER = "<!--SCHEMA-REFERENCE-->"


def adr_slug(path: Path) -> str:
    """ADR-009-revocation-authority.md -> adr-009.html — the name the specs cite."""
    return f"adr-{path.stem.split('-')[1]}.html"


def last_updated(paths) -> str | None:
    """Newest source-commit time across `paths`, as 'YYYY-MM-DD HH:MM UTC'.

    Tracks when a page's *content* last changed (its source files' last git commit), not when the
    site was rebuilt. Needs full history — CI checkout uses fetch-depth: 0. Returns None if git is
    unavailable or nothing is committed yet, so the footer simply omits the line.
    """
    stamps = []
    for p in paths:
        try:
            out = subprocess.run(
                ["git", "log", "-1", "--format=%cI", "--", str(p)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout.strip()
            if out:
                stamps.append(out)
        except Exception:
            pass
    if not stamps:
        return None
    dt = datetime.fromisoformat(max(stamps)).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _sources_for(src: Path, out: str) -> list:
    """Which source files a page's 'last updated' should watch. The schemas page is generated from
    the schema JSON + examples, so it must reflect a schema change, not just its intro edit."""
    if out == "schemas.html":
        return [src, *sorted(SCHEMA_DIR.glob("*.json")), *sorted(EXAMPLE_DIR.glob("*.json"))]
    return [src]


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
    (ROOT / "CHANGELOG.md", "changelog.html", "Changelog"),
]

# ADRs publish by convention, not by hand — a new ADR-0NN appears on the site by existing.
PAGES += [(p, adr_slug(p), "") for p in sorted(ADR.glob("ADR-*.md"))]

BANNER = ('<div class="banner">Working draft — the v0.x wire format may change. '
          'H2A is not yet a ratified standard.</div>')

# Pygments JSON/code highlighting — build-time, no client JS. Light by default,
# monokai swapped in under the OS dark preference (same .highlight class).
_FORMATTER = HtmlFormatter(cssclass="highlight")


def highlight_json(text: str) -> str:
    from pygments import highlight
    from pygments.lexers import JsonLexer
    return highlight(text, JsonLexer(), _FORMATTER)


def _pygments_css() -> str:
    """Light by default; monokai either when the theme is manually 'dark' or when the OS is dark
    and the theme was not manually set to 'light'. Mirrors the CSS-variable tiers below."""
    light = HtmlFormatter(style="default", cssclass="highlight").get_style_defs(".highlight")
    mono = HtmlFormatter(style="monokai", cssclass="highlight")
    dark_manual = mono.get_style_defs(':root[data-theme="dark"] .highlight')
    dark_os = mono.get_style_defs(':root:not([data-theme="light"]) .highlight')
    return (light + "\n" + dark_manual
            + "\n@media (prefers-color-scheme:dark){\n" + dark_os + "\n}")


# All CSS lives here as a plain string (real braces) and is substituted into TEMPLATE as a
# value — so Pygments' brace-heavy rules never collide with str.format's placeholders.
BASE_CSS = """
:root { --ink:#171717; --paper:#fafafa; --rule:#e5e5e5; --mut:#666; --chip:#f0f0f0;
  --ok:#128a3a; --bad:#c0392b; --code:#f4f4f4; }
/* dark theme values, applied via two selectors below so a manual pick beats the OS setting */
:root[data-theme="dark"] { --ink:#e8e8e8; --paper:#141414; --rule:#2b2b2b; --mut:#9a9a9a;
  --chip:#242424; --ok:#4cc96b; --bad:#e06c5a; --code:#1b1b1b; }
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) { --ink:#e8e8e8; --paper:#141414; --rule:#2b2b2b; --mut:#9a9a9a;
    --chip:#242424; --ok:#4cc96b; --bad:#e06c5a; --code:#1b1b1b; }
}
@font-face { font-family:Geist; src:url(https://cdn.jsdelivr.net/npm/geist@1/dist/fonts/geist-sans/Geist-Regular.woff2) format('woff2'); font-weight:400; font-display:swap; }
@font-face { font-family:Geist; src:url(https://cdn.jsdelivr.net/npm/geist@1/dist/fonts/geist-sans/Geist-SemiBold.woff2) format('woff2'); font-weight:600; font-display:swap; }
* { box-sizing:border-box; }
body { font-family:Geist,ui-sans-serif,system-ui,sans-serif; color:var(--ink); background:var(--paper);
  max-width:44rem; margin:0 auto; padding:2rem 1.25rem 5rem; line-height:1.6; font-size:17px; }
.banner { background:var(--ink); color:var(--paper); font-size:13px; padding:.55rem .8rem; border-radius:6px; margin-bottom:2rem; }
nav.top { display:flex; gap:1.1rem; flex-wrap:wrap; align-items:center; font-size:14px; border-bottom:1px solid var(--rule); padding-bottom:1rem; margin-bottom:2rem; }
nav.top a { color:var(--mut); text-decoration:none; } nav.top a:hover { color:var(--ink); }
.themebtn { margin-left:auto; display:inline-flex; align-items:center; justify-content:center;
  width:2rem; height:2rem; padding:0; border:1px solid var(--rule); border-radius:6px;
  background:none; color:var(--mut); cursor:pointer; }
.themebtn:hover { color:var(--ink); }
.themebtn svg { width:1.05rem; height:1.05rem; display:block; }
h1 { font-weight:600; font-size:2rem; letter-spacing:-.02em; line-height:1.15; }
h2 { font-weight:600; margin-top:2.4rem; letter-spacing:-.01em; }
h3 { font-weight:600; font-size:1.05rem; margin-top:1.8rem; }
a { color:var(--ink); }
code { background:var(--chip); padding:.1em .35em; border-radius:4px; font-size:.9em; }
pre { background:var(--code); padding:1rem; border-radius:8px; overflow:auto; }
pre code { background:none; padding:0; }
table { border-collapse:collapse; width:100%; font-size:15px; margin:1rem 0; }
th,td { border:1px solid var(--rule); padding:.5rem .7rem; text-align:left; vertical-align:top; }
th { background:var(--chip); font-weight:600; }
tbody tr:nth-child(even) { background:rgba(128,128,128,.06); }
blockquote { border-left:3px solid var(--ink); margin:1.4rem 0; padding:.2rem 0 .2rem 1rem; color:var(--mut); }
footer { margin-top:4rem; padding-top:1.5rem; border-top:1px solid var(--rule); font-size:13px; color:var(--mut); }
.updated { margin-bottom:.4rem; }

/* heading anchors (toc permalink) */
.headerlink { color:var(--rule); text-decoration:none; margin-left:.4rem; opacity:0; font-weight:400; }
h1:hover .headerlink, h2:hover .headerlink, h3:hover .headerlink { opacity:1; }

/* in-page table of contents ([TOC] and the schemas "on this page") */
.toc, .onthispage { font-size:14px; background:rgba(128,128,128,.06); border-radius:8px;
  padding:.7rem 1rem; margin:1.5rem 0; }
.toc ul { margin:.2rem 0; padding-left:1.1rem; }
.toc > ul { padding-left:0; list-style:none; }
.onthispage { display:flex; flex-wrap:wrap; gap:.9rem; align-items:baseline; margin:1.5rem 0 2.5rem; }
.onthispage span { color:var(--mut); font-weight:600; }
.onthispage a { text-decoration:none; color:var(--ink); }

/* wide breakout: prose stays 44rem; tables + examples center on the viewport */
.wide { position:relative; left:50%; transform:translateX(-50%); width:min(60rem,94vw);
  overflow-x:auto; margin:1rem 0; }
.wide table { width:100%; }

/* schema sections */
.schema { margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--rule); }
.schema h2 code { font-size:1rem; font-weight:400; background:var(--chip); }
.schema .lead { color:var(--mut); margin-top:.3rem; }
.raw { font-size:13px; color:var(--mut); text-decoration:none; font-weight:400; white-space:nowrap; }
.raw:hover { color:var(--ink); }
.subcap { font-size:13px; color:var(--mut); margin:1.3rem 0 .3rem; }
.req { color:var(--ok); font-weight:700; } .req-col { text-align:center; width:3.2rem; }
.mut { color:var(--mut); }
.ok { color:var(--ok); font-weight:600; } .bad { color:var(--bad); font-weight:600; }
.cond { border-left:3px solid var(--ink); padding:.5rem 0 .5rem 1rem; margin:1.1rem 0; font-size:15px; }
.cond ul { margin:.3rem 0 0; padding-left:1.1rem; }

/* collapsible examples */
details { margin:1rem 0; border:1px solid var(--rule); border-radius:8px; padding:.2rem .9rem; }
summary { cursor:pointer; padding:.6rem 0; font-size:14px; }
details[open] summary { border-bottom:1px solid var(--rule); margin-bottom:.6rem; }

/* syntax highlighting wrapper */
.highlight { border-radius:8px; overflow:auto; margin:0; }
.highlight pre { margin:0; background:transparent; }

/* copy-to-clipboard */
.codewrap { position:relative; }
.copy { position:absolute; top:.5rem; right:.5rem; font:inherit; font-size:12px; padding:.2rem .55rem;
  border:1px solid var(--rule); border-radius:5px; background:var(--paper); color:var(--mut);
  cursor:pointer; opacity:0; transition:opacity .15s; }
.codewrap:hover .copy, .copy:focus { opacity:1; }
.copy:hover { color:var(--ink); }
"""

# Runs in <head> before first paint: apply a saved theme so there's no flash of the wrong one.
HEAD_INIT = ("<script>(function(){try{var t=localStorage.getItem('h2a-theme');"
             "if(t==='dark'||t==='light')document.documentElement.setAttribute('data-theme',t);}"
             "catch(e){}})();</script>")

# Client JS (progressive enhancement — the page is fully readable with JS off): a copy button on
# each code block, and the theme toggle injected into the nav.
_SUN = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2'
        'M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>')
_MOON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3'
         'a7 7 0 0 0 9.8 9.8z"/></svg>')
CLIENT_JS = """<script>
document.querySelectorAll('pre').forEach(function(pre){
  var wrap=document.createElement('div'); wrap.className='codewrap';
  pre.parentNode.insertBefore(wrap,pre); wrap.appendChild(pre);
  var btn=document.createElement('button'); btn.className='copy'; btn.type='button';
  btn.textContent='Copy'; btn.setAttribute('aria-label','Copy code to clipboard');
  btn.addEventListener('click',function(){
    navigator.clipboard.writeText(pre.innerText).then(function(){
      btn.textContent='Copied'; setTimeout(function(){btn.textContent='Copy';},1200);
    });
  });
  wrap.appendChild(btn);
});
(function(){
  var SUN='__SUN__', MOON='__MOON__';
  var root=document.documentElement, nav=document.querySelector('nav.top');
  if(!nav) return;
  var btn=document.createElement('button'); btn.className='themebtn'; btn.type='button';
  function effective(){ return root.getAttribute('data-theme') ||
    (window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'); }
  function paint(){ var dark=effective()==='dark';
    btn.innerHTML=dark?SUN:MOON;
    btn.setAttribute('aria-label', dark?'Switch to light theme':'Switch to dark theme');
    btn.setAttribute('title', dark?'Switch to light theme':'Switch to dark theme'); }
  paint();
  btn.addEventListener('click',function(){ var next=effective()==='dark'?'light':'dark';
    root.setAttribute('data-theme',next);
    try{localStorage.setItem('h2a-theme',next);}catch(e){} paint(); });
  nav.appendChild(btn);
})();
</script>""".replace("__SUN__", _SUN).replace("__MOON__", _MOON)

TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · H2A</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net">
{head_init}
<style>{style}</style></head><body>
{banner}
<nav class="top">{nav}</nav>
<main>{body}</main>
<footer>{updated}H2A Protocol · working draft · <a href="https://h2a-protocol.org">h2a-protocol.org</a>.
Spec text CC BY 4.0; schemas &amp; code Apache-2.0.</footer>
{script}
</body></html>"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    style = BASE_CSS + "\n" + _pygments_css()
    nav = " ".join(
        f'<a href="{out}">{title}</a>' for _, out, title in PAGES if title
    )
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "toc"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": False},
            "toc": {"permalink": True},
        },
    )

    reference = schema_doc.render_reference(SCHEMA_DIR, EXAMPLE_DIR, highlight_json)

    for src, out, title in PAGES:
        md.reset()
        body = md.convert(Path(src).read_text(encoding="utf-8"))
        if SCHEMA_MARKER in body:
            body = body.replace(SCHEMA_MARKER, reference)
        stamp = last_updated(_sources_for(src, out))
        updated = f'<div class="updated">Last updated {stamp}</div>' if stamp else ""
        html = TEMPLATE.format(title=title or "H2A", style=style, head_init=HEAD_INIT,
                               banner=BANNER, nav=nav, body=body, updated=updated,
                               script=CLIENT_JS)
        (OUT / out).write_text(html, encoding="utf-8")

    # publish schemas so every $id resolves under the hosted domain
    shutil.copytree(ROOT / "schemas", OUT / "schemas")
    (OUT / "CNAME").write_text("h2a-protocol.org\n", encoding="utf-8")

    print(f"built {len(PAGES)} pages + schemas -> {OUT}")


if __name__ == "__main__":
    build()
