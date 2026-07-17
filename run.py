# -*- coding: utf-8 -*-
"""Genome Dashboard — CLI. Parse a raw DNA file, analyze, render an offline HTML report.

  python run.py --input <raw.txt> [--out dashboard.html] [--lang ru,es] [--images]

English by default & fully offline. --lang / --images activate only if the matching
API key is configured (see scripts/config.py); otherwise they degrade gracefully.
This is educational, not medical advice. Your DNA file never leaves this machine.
"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
import run_analysis, render_html, safety, config

def main():
    ap = argparse.ArgumentParser(description="Generate an offline genome dashboard from a raw DNA file.")
    ap.add_argument("--input", required=True, help="raw DNA file (23andMe or AncestryDNA)")
    ap.add_argument("--out", default="dashboard.html")
    ap.add_argument("--lang", default="", help="comma-separated extra languages (needs LLM key)")
    ap.add_argument("--images", action="store_true", help="generate hero art (needs image key)")
    ap.add_argument("--portrait", type=int, default=0, metavar="N", help="generate N speculative DNA portrait variants (needs image key)")
    ap.add_argument("--env", default=None, help="path to a .env with optional API keys")
    # UX (all on by default): sticky jump-nav, collapsible cards, compact/detailed toggle
    ap.add_argument("--no-nav", action="store_true", help="disable the sticky jump-navigation bar")
    ap.add_argument("--no-collapse", action="store_true", help="keep trait cards fully expanded (no click-to-open)")
    ap.add_argument("--no-compact", action="store_true", help="hide the compact/detailed density toggle")
    a = ap.parse_args()
    opts = {"nav": not a.no_nav, "disclosure": not a.no_collapse, "compact": not a.no_compact}
    cfg = config.Config(env_file=a.env)
    disc = safety.load()

    print(f"[1/4] parsing + analyzing {a.input} …")
    analysis = run_analysis.analyze(a.input)

    images = {}
    if a.images:
        if cfg.has_images():
            import gen_images; images = gen_images.generate(cfg)
            print(f"[2/4] images: {len(images)} generated")
        else:
            print("[2/4] images skipped — no IMAGE_API_KEY")
    if a.portrait and cfg.has_images():
        import gen_images
        pr = gen_images.generate_portraits(cfg, analysis["appearance"]["prompt"], a.portrait)
        images.update(pr); print(f"[2b] portraits: {len(pr)} generated")
    elif a.portrait:
        print("[2b] portraits skipped — no IMAGE_API_KEY")
    else:
        print("[2/4] images off")

    print("[3/4] rendering HTML …")
    htmls = render_html.render(analysis, a.out, disc, images=images, opts=opts)

    langs = [l.strip() for l in a.lang.split(",") if l.strip()]
    if langs:
        if cfg.has_translation():
            import translate; htmls = translate.fill(htmls, langs, cfg)
            print(f"[4/4] translated: {', '.join(langs)}")
        else:
            print("[4/4] translation skipped — no LLM_API_KEY (English only)")
    else:
        print("[4/4] English only")

    open(a.out, "w", encoding="utf-8").write(htmls)
    print(f"✓ wrote {a.out}  ({len(htmls)//1024} KB)  — open in any browser, offline.")

if __name__ == "__main__":
    main()
