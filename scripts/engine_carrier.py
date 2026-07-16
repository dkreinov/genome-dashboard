# -*- coding: utf-8 -*-
"""Ancestry carrier screen — genotype -> carrier status (generic lookup).
Homozygous call at a rare founder variant = reference (non-carrier), since
homozygous-mutant is non-viable/vanishingly rare. Always clinically caveated by render/safety."""
import json, os
REF = os.path.join(os.path.dirname(__file__), "..", "reference")
def _norm(gt):
    gt=(gt or "").strip().upper()
    return gt if gt in("","--") else "".join(sorted(gt))
def run(calls):
    cat=json.load(open(os.path.join(REF,"carrier_catalog.json"),encoding="utf-8"))
    out=[]
    for e in cat:
        rec=calls.get(e["rsid"])
        if not rec: continue
        m=e["gt"].get(_norm(rec["genotype"]))
        if not m: continue
        out.append({"disease":e["disease"],"gene":e["gene"],"variant":e["variant"],"rsid":e["rsid"],
                    "gt":rec["genotype"],"result":m[0],"category":m[1],"text":m[2],
                    "type":e.get("type"),"source":e["source"]})
    return {"variants":out}
