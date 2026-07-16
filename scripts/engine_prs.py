# -*- coding: utf-8 -*-
"""Polygenic risk scores from frozen weights. Palindrome-safe dosage, one row per
locus_group, z-scored to the 1000G European distribution -> theoretical percentile."""
import json, os, math
REF = os.path.join(os.path.dirname(__file__), "..", "reference")
COMP = {"A":"T","T":"A","C":"G","G":"C"}

def _dosage(gt, risk, fr):
    if not gt or len(gt)!=2 or gt=="--" or "I" in gt or "D" in gt: return None
    a,b = gt[0],gt[1]
    alleles = set(fr.keys()) if fr else set()
    if alleles and (a not in alleles or b not in alleles):
        a,b = COMP.get(a,a), COMP.get(b,b)
    return (a==risk)+(b==risk)

def run(calls):
    weights = json.load(open(os.path.join(REF,"prs_weights.json"), encoding="utf-8"))
    freqs = json.load(open(os.path.join(REF,"allele_freqs.json"), encoding="utf-8"))
    out=[]
    for trait, rows in weights.items():
        raw=mu=var=0; used=0; seen=set()
        src=rows[0]["source_url"] if rows else None
        for r in rows:
            if r["locus_group"] in seen: continue          # enforce one per locus
            fr = freqs.get(r["rsid"],{}).get("EUR")
            rec = calls.get(r["rsid"])
            p = None
            if fr:
                p = fr.get(r["risk_allele"]) or fr.get(COMP.get(r["risk_allele"],r["risk_allele"]))
            d = _dosage(rec["genotype"], r["risk_allele"], fr) if rec else None
            if p is None or d is None: continue
            seen.add(r["locus_group"]); used+=1
            b=r["beta"]; raw+=d*b; mu+=2*p*b; var+=b*b*2*p*(1-p)
        if used<4 or var<=0: continue
        z=(raw-mu)/math.sqrt(var)
        pct=round(0.5*(1+math.erf(z/math.sqrt(2)))*100)
        out.append({"trait":trait,"used":used,"pct":pct,"z":round(z,2),
                    "rr":round(math.exp(raw-mu),2),"source_url":src})
    return {"scores":out}
