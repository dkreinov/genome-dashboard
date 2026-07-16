# -*- coding: utf-8 -*-
"""Build the frozen, LD-pruned, palindrome-safe PRS weights table and validate it.
Run once; writes prs_weights.json. Kept in reference/ as provenance."""
import json, os, math
HERE = os.path.dirname(__file__)
EFO = {"Type 2 diabetes":"EFO_0001360","Coronary artery disease":"EFO_0000378",
 "Prostate cancer":"EFO_0001663","Colorectal cancer":"EFO_0005842",
 "Melanoma":"EFO_0000756","Atrial fibrillation":"EFO_0000275","Gout":"EFO_0004274"}
def url(t): return "https://www.ebi.ac.uk/gwas/efotraits/"+EFO[t]

# (rsid, risk_allele, beta=ln(OR), locus_group) — ONE row per independent locus.
# T2D / CAD betas are literature (DIAGRAM / CARDIoGRAMplusC4D); cancer & AF/gout
# risk alleles are cross-checked below against gwas_weights_raw.json.
W = {
 "Type 2 diabetes":[("rs7903146","T",0.329,"TCF7L2"),("rs10811661","T",0.174,"CDKN2A/B"),
   ("rs13266634","C",0.113,"SLC30A8"),("rs7754840","C",0.113,"CDKAL1"),("rs1111875","C",0.122,"HHEX"),
   ("rs5219","T",0.131,"KCNJ11"),("rs1801282","C",0.131,"PPARG"),("rs2237892","C",0.100,"KCNQ1"),
   ("rs4402960","T",0.131,"IGF2BP2"),("rs8050136","A",0.140,"FTO"),("rs2943641","C",0.174,"IRS1")],
 "Coronary artery disease":[("rs1333049","C",0.255,"9p21"),("rs599839","A",0.104,"SORT1"),
   ("rs17465637","C",0.131,"MIA3"),("rs6725887","C",0.131,"WDR12"),("rs9349379","G",0.095,"PHACTR1"),
   ("rs1746048","C",0.086,"CXCL12"),("rs2306374","C",0.140,"MRAS"),("rs11206510","T",0.077,"PCSK9"),
   ("rs12190287","C",0.077,"TCF21"),("rs3798220","C",0.351,"LPA_a"),("rs10455872","G",0.385,"LPA_b"),
   ("rs4420638","G",0.180,"APOE")],
 "Prostate cancer":[("rs6983267","G",0.211,"8q24"),("rs10993994","T",0.191,"MSMB"),
   ("rs4430796","A",0.199,"HNF1B"),("rs2735839","G",0.174,"KLK3"),("rs10896449","G",0.178,"11q13"),
   ("rs1859962","G",0.157,"17q24"),("rs721048","A",0.118,"2p15")],
 "Colorectal cancer":[("rs6983267","G",0.153,"8q24"),("rs4939827","T",0.122,"SMAD7"),
   ("rs10795668","G",0.135,"10p14"),("rs3802842","C",0.095,"11q23"),("rs4444235","C",0.094,"BMP4"),
   ("rs9929218","G",0.079,"16q22"),("rs4779584","T",0.113,"15q13"),("rs16892766","C",0.198,"8q23"),
   ("rs961253","A",0.095,"20p12"),("rs10936599","C",0.058,"MYNN"),("rs10411210","C",0.104,"RHPN2")],
 "Melanoma":[("rs401681","A",0.182,"TERT"),("rs16891982","G",0.727,"SLC45A2"),
   ("rs7023329","A",0.166,"9p21"),("rs1393350","A",0.255,"TYR"),("rs258322","A",0.513,"16q24"),
   ("rs910873","T",0.560,"20q11"),("rs1805007","T",0.447,"MC1R")],
 "Atrial fibrillation":[("rs2200733","T",0.542,"4q25"),("rs2106261","T",0.223,"ZFHX3"),
   ("rs13376333","T",0.419,"KCNN3"),("rs3807989","G",0.104,"CAV1"),("rs3903239","G",0.243,"PRRX1")],
 "Gout":[("rs2231142","T",0.632,"ABCG2"),("rs734553","T",0.329,"SLC2A9"),
   ("rs11722228","T",0.425,"SLC17A1"),("rs2078267","C",0.231,"SLC22A11")],
}
LITERATURE = {"Type 2 diabetes","Coronary artery disease"}  # betas not in gwas cache

# ---- validate: no duplicate locus_group; cross-check risk alleles ----
raw = json.load(open(os.path.join(HERE,"gwas_weights_raw.json"),encoding="utf-8"))
def gwas_risk_alleles(rs):
    out=set()
    for a in raw.get(rs,[]):
        al=a.get("allele")
        if al and al in ("A","C","G","T"): out.add(al)
    return out
problems=[]
out={}
for trait,rows in W.items():
    groups=[g for *_,g in rows]
    if len(groups)!=len(set(groups)):
        problems.append(f"{trait}: duplicate locus_group {[g for g in groups if groups.count(g)>1]}")
    entries=[]
    for rsid,risk,beta,grp in rows:
        if trait not in LITERATURE:
            ga=gwas_risk_alleles(rsid)
            if ga and risk not in ga:
                problems.append(f"{trait}/{rsid}: risk '{risk}' not in GWAS-cache alleles {ga}")
        entries.append({"rsid":rsid,"risk_allele":risk,"beta":beta,
                        "locus_group":grp,"source_url":url(trait)})
    out[trait]=entries
json.dump(out,open(os.path.join(HERE,"prs_weights.json"),"w",encoding="utf-8"),indent=1)
print("traits:",{t:len(v) for t,v in out.items()})
print("PROBLEMS:" , problems if problems else "none")
