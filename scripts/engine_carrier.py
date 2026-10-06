# -*- coding: utf-8 -*-
"""Carrier and founder-variant screen — allele-count rule (generic).

Each catalog entry gives ref/alt alleles on the GRCh37 plus strand (or I/D for
indels). The first available probe ("i" ID or rsID) is used. Founder variants
are reliable on the chip; a homozygous call at a rare variant is usually a chip
error. Every result says to confirm with an accredited lab."""
import json, os
import probes

REF = os.path.join(os.path.dirname(__file__), "..", "reference")
CONFIRM = "Confirm with an accredited lab before a medical or family-planning decision."

def _card(e, pid, gt, result, category, text):
    return {"disease": e["disease"], "gene": e["gene"], "variant": e["variant"],
            "rsid": pid or e.get("rsid", ""), "gt": gt, "result": result, "category": category,
            "text": text, "type": e.get("type", e.get("inheritance", "")), "source": e["source"],
            "tier": e.get("tier", ""), "aj_carrier_pct": e.get("aj_carrier_pct"),
            "residual": e.get("residual", ""), "detection": e.get("detection", "")}

PARTNER = " If you plan a family, test the partner."

def _partner(e):
    return PARTNER if e.get("inheritance") == "recessive" else ""

def classify(e, calls):
    if e.get("untestable"):
        return _card(e, "", "—", "Not testable on this chip", "untestable",
                     e["untestable"] + " A clean chip result does not replace clinical screening.")
    pid, rec = probes.find(calls, e)
    if not rec:
        return None
    gt = rec["genotype"]
    n = probes.alt_count(gt, e["ref"], e["alt"])
    if n is None:
        return _card(e, pid, gt, "Unexpected genotype — check", "caution",
                     "The chip reports alleles that this entry does not expect. "
                     "This can be a strand or chip error. " + CONFIRM)
    for cid in e.get("confirm_probes", []):
        crec = calls.get(cid)
        if crec and crec.get("genotype") not in (None, "", "--"):
            if probes.alt_count(crec["genotype"], e["ref"], e["alt"]) != n:
                return _card(e, pid, gt, "Unclear — probes disagree, confirm", "caution",
                             "Two chip probes for this variant give different results. " + CONFIRM + _partner(e))
    if n == 0:
        res = (f" For a person of Ashkenazi Jewish ancestry, the remaining risk to be a carrier after a negative "
               f"full 23andMe test for this disease is {e['residual']}.") if e.get("residual") else ""
        det = (f" This test finds about {e['detection']} of carriers in Ashkenazi Jews.") if e.get("detection") else ""
        return _card(e, pid, gt, "Not detected", "reassuring",
                     "No copy of this variant at the tested position." + res + det +
                     " The chip tests only this position, not the whole gene.")
    if n == 2:
        pct = e.get("aj_carrier_pct")
        if pct is not None and pct >= 1:
            return _card(e, pid, gt, "Two copies — confirm", "caution",
                         "Two copies of this variant can mean the condition, or a chip error. "
                         "See a doctor and confirm with an accredited lab." + _partner(e))
        return _card(e, pid, gt, "Two copies — probably a chip error, confirm", "caution",
                     "Two copies of a rare variant are unusual and often a chip error. " + CONFIRM)
    if e.get("inheritance") == "dominant":
        return _card(e, pid, gt, "Possible variant — confirm", "caution",
                     "The chip shows one copy of this variant. Chips sometimes misread rare variants. " + CONFIRM)
    return _card(e, pid, gt, "Possible carrier — confirm", "caution",
                 "The chip shows one copy. A carrier is usually healthy. "
                 "If you plan a family, test the partner: the risk applies only if both partners carry a variant in this gene. "
                 + CONFIRM)

def run_entries(entries, calls):
    out = [c for c in (classify(e, calls) for e in entries) if c]
    by_gene = {}
    for c in out:
        if c["type"] == "recessive" and c["result"].startswith("Possible carrier"):
            by_gene.setdefault(c["gene"], []).append(c)
    for gene, cards in by_gene.items():
        if len(cards) >= 2:
            x = dict(cards[0], variant="two variants", gt="—",
                     result="Two variants in one gene — confirm", category="caution",
                     text="The chip shows two different variants in this gene. "
                          "If they are on different copies, this can mean the condition. "
                          "See a doctor and confirm with an accredited lab." + PARTNER)
            out.append(x)
    return {"variants": out}

def run(calls):
    cat = json.load(open(os.path.join(REF, "carrier_catalog.json"), encoding="utf-8"))
    return run_entries(cat, calls)
