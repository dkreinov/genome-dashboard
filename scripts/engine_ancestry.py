# -*- coding: utf-8 -*-
"""Continental ancestry (naive-Bayes over AIMs vs 1000G freqs) + runs of homozygosity.
Uses bundled reference/allele_freqs.json (no live fetch). Prose is data-driven."""
import json, os, math, collections
REF = os.path.join(os.path.dirname(__file__), "..", "reference")
POPS = ["EUR","EAS","AFR","SAS","AMR"]
COMP = {"A":"T","T":"A","C":"G","G":"C"}
POPLBL = {"EUR":"European","EAS":"East Asian","AFR":"African","SAS":"South Asian","AMR":"Amerindian/Admixed"}
# ancestry-informative markers (subset present in the frozen freq table)
AIMS = ["rs1426654","rs16891982","rs2814778","rs3827760","rs1229984","rs17822931","rs671",
        "rs12913832","rs1042602","rs260690","rs174570","rs7554936","rs2946788","rs7657799",
        "rs2504853","rs2416791","rs1800407","rs1129038","rs459920","rs3785181","rs4471745",
        "rs11652805","rs12203592","rs4988235"]

def run(calls):
    freqs = json.load(open(os.path.join(REF,"allele_freqs.json"), encoding="utf-8"))
    logL = {p:0.0 for p in POPS}; used=0
    for rs in AIMS:
        rec = calls.get(rs); fr = freqs.get(rs)
        if not rec or not fr or not all(p in fr for p in POPS): continue
        gt = rec["genotype"]
        if len(gt)!=2 or gt=="--" or "I" in gt or "D" in gt: continue
        a,b = gt[0],gt[1]
        alleles = set().union(*[set(fr[p]) for p in POPS])
        if a not in alleles or b not in alleles:
            a,b = COMP.get(a,a), COMP.get(b,b)
            if a not in alleles or b not in alleles: continue
        used += 1
        for p in POPS:
            fa,fb = fr[p].get(a,1e-4), fr[p].get(b,1e-4)
            g = fa*fa if a==b else 2*fa*fb
            logL[p] += math.log(max(g,1e-6))
    post = None
    if used:
        m = max(logL.values()); e = {p:math.exp(logL[p]-m) for p in POPS}; s=sum(e.values())
        post = {p: round(e[p]/s,4) for p in POPS}
    # ROH scan
    bychr = collections.defaultdict(list)
    for rs,rec in calls.items():
        ch,gt = rec["chrom"], rec["genotype"]
        if ch in ("X","Y","MT") or len(gt)!=2 or gt=="--" or "I" in gt or "D" in gt: continue
        if rec["pos"]>0: bychr[ch].append((rec["pos"], gt[0]==gt[1]))
    roh=[]
    for ch,arr in bychr.items():
        arr.sort(); i=0; n=len(arr)
        while i<n:
            if arr[i][1]:
                j=i
                while j+1<n and arr[j+1][1]: j+=1
                span=(arr[j][0]-arr[i][0])/1e6
                if span>=1.5 and (j-i+1)>=100: roh.append((ch,round(span,1)))
                i=j+1
            else: i+=1
    roh.sort(key=lambda x:-x[1])
    total = round(sum(r[1] for r in roh)); big = sum(1 for r in roh if r[1]>=5)
    # data-driven prose
    prose = None
    if post:
        top = max(post, key=post.get)
        prose = (f"Closest 1000-Genomes reference population: {POPLBL[top]} "
                 f"({round(100*post[top])}%). "
                 f"{'Elevated' if total>=40 else 'Typical'} runs of homozygosity "
                 f"({total} Mb, {big} segment(s) >5 Mb){' — a signal of ancestry from a small/endogamous population or distant shared parental ancestry.' if total>=40 else '.'}")
    return {"posterior":post,"aims_used":used,"roh_total_mb":total,"roh_big":big,
            "roh_longest":(roh[0] if roh else None),"prose":prose,"pop_labels":POPLBL}
