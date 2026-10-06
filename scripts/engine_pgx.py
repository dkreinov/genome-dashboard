# -*- coding: utf-8 -*-
"""Pharmacogenomics — CPIC guidance. Single-SNP entries use a genotype table;
gene-level entries ("rule") use pgx_rules; "untestable" entries always show."""
import json, os
import probes, pgx_rules

REF = os.path.join(os.path.dirname(__file__), "..", "reference")

def _norm(gt):
    gt = (gt or "").strip().upper()
    return gt if gt in ("", "--") else "".join(sorted(gt))

def _gene_card(e, calls):
    counts, untested = pgx_rules.count_alleles(e, calls)
    if len(untested) == len(e["alleles"]):
        return None
    phenotype, category, text = pgx_rules.RULES[e["rule"]](e, counts)
    if untested:
        if category == "reassuring":
            phenotype, category = "Normal at tested positions (incomplete)", "standard"
        text += f" Not tested on this chip: {', '.join(untested)}; the result assumes the normal allele there."
    found = [f"{n} ×{k}" for n, k in counts.items() if k]
    used = [probes.find(calls, a)[0] for a in e["alleles"]]
    return {"drug": e["drug"], "gene": e["gene"], "rsid": ",".join(p for p in used if p),
            "gt": ", ".join(found) or "no variant found", "phenotype": phenotype,
            "category": category, "text": text, "source": e["source"]}

def run(calls):
    cat = json.load(open(os.path.join(REF, "pgx_catalog.json"), encoding="utf-8"))
    out = []
    for e in cat:
        if e.get("untestable"):
            out.append({"drug": e["drug"], "gene": e["gene"], "rsid": "", "gt": "—",
                        "phenotype": "Not tested on this chip", "category": "untestable",
                        "text": e["untestable"], "source": e["source"]})
            continue
        if "rule" in e:
            card = _gene_card(e, calls)
            if card:
                out.append(card)
            continue
        _, rec = probes.find(calls, e)
        if not rec:
            continue
        m = e["gt"].get(_norm(rec["genotype"]))
        if not m:
            continue
        out.append({"drug": e["drug"], "gene": e["gene"], "rsid": e["rsid"], "gt": rec["genotype"],
                    "phenotype": m[0], "category": m[1], "text": m[2], "source": e["source"]})
    return {"drugs": out}
