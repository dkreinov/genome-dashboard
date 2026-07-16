# -*- coding: utf-8 -*-
"""Generic Y-DNA haplogroup caller. Walks the SNPedia hgsnp DB over Y calls,
scores the deepest ISOGG-longhand branch consistent with the most markers."""
import json, os, re
REF = os.path.join(os.path.dirname(__file__), "..", "reference")
COMP = {"A":"T","T":"A","C":"G","G":"C"}

def _allele(x):
    if not x: return None
    m = re.search(r"\(([ACGT]);", x)
    if m: return m.group(1)
    return x if re.fullmatch(r"[ACGT]", x or "") else None

def _build_db(pages):
    db = {}
    for title, wt in pages.items():
        rsid = title.lower()
        mo = re.search(r"StabilizedOrientation\s*=\s*(\w+)", wt)
        orient = (mo.group(1).strip().lower() if mo else "plus")
        mc = re.search(r"Chromosome\s*=\s*(\w+)", wt)
        chrom = mc.group(1).strip() if mc else None
        entries = []
        for b in re.findall(r"\{\{hgsnp(.*?)\}\}", wt, re.S):
            def g(k):
                m = re.search(r"\|\s*"+k+r"\s*=\s*([^\n|}]+)", b)
                return m.group(1).strip() if m else None
            anc, der, dh = _allele(g("ancestral_allele")), _allele(g("derived_allele")), g("derived_haplogroup")
            if anc and der and dh:
                entries.append({"dh":dh.strip(),"anc":anc,"der":der,"orient":orient,"chrom":chrom})
        if entries: db[rsid] = entries
    return db

def _is_prefix(p,n):
    return n.startswith(p) and (len(n)==len(p) or n[len(p)].isalnum())

def run(calls):
    ycalls = {rs.lower(): rec["genotype"][0] for rs,rec in calls.items()
              if rec["chrom"]=="Y" and rec["genotype"] not in ("--","")}
    if len(ycalls) < 20:
        return {"call": None, "note": "Too few Y calls (female sample or sparse chip).", "n_tested": len(ycalls)}
    db = _build_db(json.load(open(os.path.join(REF,"haplogroup_snps.json"), encoding="utf-8")))
    D, A = set(), set()
    for rsid, entries in db.items():
        if rsid not in ycalls: continue
        call = ycalls[rsid]
        for e in entries:
            if e["chrom"] not in ("Y", None): continue
            der, anc = e["der"], e["anc"]
            if e["orient"] == "minus": der, anc = COMP.get(der,der), COMP.get(anc,anc)
            if call == der: D.add(e["dh"])
            elif call == anc: A.add(e["dh"])
    clean = lambda n: bool(re.fullmatch(r"[A-Z][A-Za-z0-9]*", n))
    D = {n for n in D if clean(n)}; A = {n for n in A if clean(n)}
    if not D:
        return {"call": None, "note": "No derived Y markers resolved.", "n_tested": len(ycalls)}
    best = None
    for cand in sorted(D, key=len, reverse=True):
        support = sum(1 for d in D if _is_prefix(d,cand))
        conflict = sum(1 for a in A if _is_prefix(a,cand) and a!=cand)
        score = support - 3*conflict
        if best is None or score>best[0] or (score==best[0] and len(cand)>len(best[1])):
            best = (score, cand, support, conflict)
    chain = sorted([d for d in D if _is_prefix(d,best[1])], key=len)
    return {"call": best[1], "chain": chain, "support": best[2], "conflict": best[3],
            "n_tested": len(ycalls), "excluded": sorted(A, key=len)[:20]}
