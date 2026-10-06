# -*- coding: utf-8 -*-
"""Catalog interpreter — per-genotype SNP cards. Generic (reads reference/catalog.json)."""
import json, os
import probes
REF = os.path.join(os.path.dirname(__file__), "..", "reference")

def _norm(gt):
    gt = (gt or "").strip().upper()
    if gt in ("", "--", "DD", "II", "DI", "ID"): return gt
    return "".join(sorted(gt))

def _apoe(a, b):
    if not a or not b: return None
    m = {("TT","CC"):("ε3/ε3","Most common (~60%) and reassuring: average Alzheimer's risk, no ε4.","good"),
         ("CC","CC"):("ε4/ε4","Two ε4 copies — substantially higher late-onset Alzheimer's & cardiovascular risk.","watch"),
         ("CT","CC"):("ε3/ε4","One ε4 copy — moderately higher Alzheimer's risk.","watch"),
         ("TT","CT"):("ε2/ε3","One ε2 — slightly protective for Alzheimer's.","good"),
         ("TT","TT"):("ε2/ε2","Protective for Alzheimer's; linked to type III hyperlipidemia.","note"),
         ("CT","CT"):("ε2/ε4","One protective, one risk allele.","note")}
    return m.get((a,b), ("Undetermined","Could not phase APOE from these two SNPs.","note"))

def run(calls):
    catalog = json.load(open(os.path.join(REF,"catalog.json"), encoding="utf-8"))
    results = []
    for e in catalog:
        _, rec = probes.find(calls, e)
        if not rec: continue
        raw = rec["genotype"]
        m = e["gt"].get(_norm(raw))
        if m: label, text, sev = m
        else: label, text, sev = (raw, "Genotype present but not among characterized outcomes.", "info")
        results.append({"cat":e["cat"],"gene":e["gene"],"rsid":e["rsid"],"title":e["title"],
                        "gt":raw,"label":label,"text":text,"sev":sev})
    # APOE (two-SNP diplotype)
    a = calls.get("rs429358"); b = calls.get("rs7412")
    if a and b:
        ap = _apoe(_norm(a["genotype"]), _norm(b["genotype"]))
        if ap:
            results.append({"cat":"Health","gene":"APOE","rsid":"rs429358+rs7412",
                "title":"APOE — Alzheimer's & cholesterol",
                "gt":f"{a['genotype']}/{b['genotype']}","label":ap[0],"text":ap[1],"sev":ap[2]})
    return {"markers": results, "n": len(results)}
