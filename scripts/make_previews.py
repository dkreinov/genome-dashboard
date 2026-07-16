# -*- coding: utf-8 -*-
"""Render the synthetic example through each UX variant so they can be compared.
Throwaway artifacts (examples/preview_*.html are gitignored)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run_analysis, render_html, safety

HERE = os.path.dirname(__file__)
SAMPLE = os.path.join(HERE, "..", "examples", "mock_person.txt")
OUT = os.path.join(HERE, "..", "examples")

VARIANTS = {
    "preview_A_nav.html":        {"nav": True},
    "preview_B_disclosure.html": {"disclosure": True},
    "preview_C_combined.html":   {"nav": True, "disclosure": True},
    "preview_D_toggle.html":     {"nav": True, "compact": True},
}

def main():
    analysis = run_analysis.analyze(SAMPLE)
    disc = safety.load()
    for fname, opts in VARIANTS.items():
        html = render_html.render(analysis, None, disc, images={}, opts=opts)
        open(os.path.join(OUT, fname), "w", encoding="utf-8").write(html)
        print(f"wrote {fname}  ({len(html)//1024} KB)  opts={opts}")

if __name__ == "__main__":
    main()
