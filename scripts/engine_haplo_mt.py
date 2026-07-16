# -*- coding: utf-8 -*-
"""Generic mtDNA haplogroup caller (rCRS-difference, rules-based).

Reads MT calls, builds {position: base}, scores each haplogroup by how many of its
diagnostic mutations are present, and reports the best-supported (deepest) match with
a confidence score. Honest/approximate — subclades need a dedicated tool.
"""
import json, os, math
REF = os.path.join(os.path.dirname(__file__), "..", "reference")
# Subclades that should win over their macro-haplogroup when supported
_MORE_SPECIFIC = {"U5","U4","U2","U8","K"}  # (all under U); K over U; U5/U4/... over U

def run(calls):
    tree = json.load(open(os.path.join(REF,"mt_phylotree.json"), encoding="utf-8"))
    tree = {k:v for k,v in tree.items() if not k.startswith("_")}
    pos = {rec["pos"]: rec["genotype"][0] for rs,rec in calls.items()
           if rec["chrom"]=="MT" and rec["genotype"] not in ("--","") and rec["pos"]>0}
    if len(pos) < 10:
        return {"call": None, "note": "Too few mtDNA calls to place a haplogroup.", "n_tested": len(pos)}
    scored = []
    for hg, diag in tree.items():
        tested = [(p,b) for p,b in diag if p in pos]
        if not tested: continue
        matched = sum(1 for p,b in tested if pos[p]==b)
        frac = matched/len(diag)
        # qualify: majority of diagnostic sites present AND matched, min 2 hits
        if matched>=2 and matched>=math.ceil(0.6*len(diag)):
            scored.append({"hg":hg,"matched":matched,"n_diag":len(diag),"conf":round(frac,2)})
    if not scored:
        # H is rCRS-like: if 7028 is C (present) and nothing else qualified, call H
        if pos.get(7028)=="C":
            return {"call":"H","matched_mutations":["7028C (rCRS-like)"],"confidence":0.5,
                    "n_tested":len(pos),"note":"H family (rCRS-like); confirm subclade with a dedicated tool."}
        return {"call": None, "note": "No haplogroup reached the support threshold.", "n_tested": len(pos)}
    # rank: prefer more diagnostic hits, then specificity (subclade), then confidence
    def rank(s):
        return (s["matched"], 1 if s["hg"] in _MORE_SPECIFIC else 0, s["conf"], len(s["hg"]))
    scored.sort(key=rank, reverse=True)
    top = scored[0]
    diag = dict((tuple(x) for x in tree[top["hg"]]))
    matched_muts = [f"{p}{b}" for p,b in tree[top["hg"]] if pos.get(p)==b]
    return {"call": top["hg"], "matched_mutations": matched_muts,
            "confidence": top["conf"], "n_tested": len(pos),
            "candidates": scored[:4],
            "note": "Approximate rules-based call; confirm the exact subclade with a dedicated mtDNA tool."}
