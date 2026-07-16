# -*- coding: utf-8 -*-
"""Neanderthal-allele carriage estimate (SNPedia 42-marker 'out-of-Africa' panel)."""
import json, os
REF = os.path.join(os.path.dirname(__file__), "..", "reference")
COMP = {"A":"T","T":"A","C":"G","G":"C"}

def run(calls):
    panel = json.load(open(os.path.join(REF,"neanderthal_panel.json"), encoding="utf-8"))
    tested=nean_markers=nean_alleles=hom=0
    for rs,(d) in panel.items():
        aa, ooa = d["AA"], d["OOA"]
        rec = calls.get(rs)
        if not rec: continue
        gt = rec["genotype"]
        if len(gt)!=2 or gt=="--" or "I" in gt or "D" in gt: continue
        a,b = gt[0],gt[1]
        if a not in (aa,ooa) or b not in (aa,ooa):
            a,b = COMP.get(a,a), COMP.get(b,b)
            if a not in (aa,ooa) or b not in (aa,ooa): continue
        tested+=1
        c=(a==ooa)+(b==ooa)
        if c>0: nean_markers+=1; nean_alleles+=c
        if c==2: hom+=1
    return {"tested":tested,"panel":len(panel),"nean_markers":nean_markers,
            "nean_alleles":nean_alleles,"hom":hom,
            "european_avg_range":[5,10],
            "note":"Small panel — illustrative carriage, not a genome-wide %. Non-Africans ~1.5-2.1%."}
