# -*- coding: utf-8 -*-
"""Pharmacogenomics — genotype -> CPIC guidance (generic lookup)."""
import json, os
REF = os.path.join(os.path.dirname(__file__), "..", "reference")
def _norm(gt):
    gt=(gt or "").strip().upper()
    return gt if gt in("","--") else "".join(sorted(gt))
def run(calls):
    cat=json.load(open(os.path.join(REF,"pgx_catalog.json"),encoding="utf-8"))
    out=[]
    for e in cat:
        rec=calls.get(e["rsid"])
        if not rec: continue
        m=e["gt"].get(_norm(rec["genotype"]))
        if not m: continue
        out.append({"drug":e["drug"],"gene":e["gene"],"rsid":e["rsid"],"gt":rec["genotype"],
                    "phenotype":m[0],"category":m[1],"text":m[2],"source":e["source"]})
    return {"drugs":out}
