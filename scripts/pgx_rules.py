# -*- coding: utf-8 -*-
"""CPIC phenotype rules for genes that need several alleles. Phase is unknown on a
chip, so two different variants in one gene are treated as one on each copy
(the worse case), except TPMT *3B + *3C, which is most likely one *3A allele."""
import probes

CONFIRM = " Confirm with a clinical test before a drug decision."

def count_alleles(entry, calls):
    counts, untested = {}, []
    for a in entry["alleles"]:
        _, rec = probes.find(calls, a)
        n = probes.alt_count(rec["genotype"], a["ref"], a["alt"]) if rec else None
        if n is None:
            untested.append(a["name"])
            n = 0
        counts[a["name"]] = n
    return counts, untested

def cyp2c19(entry, c):
    nf = c.get("*2", 0) + c.get("*3", 0) + c.get("*4", 0)
    inc = c.get("*17", 0)
    if nf >= 2:
        return ("Poor metabolizer", "avoid",
                "Clopidogrel does not work well for you. CPIC advises another antiplatelet drug, for example prasugrel or ticagrelor."
                " Some antidepressants and stomach-acid drugs (PPIs) also need a different dose." + CONFIRM)
    if nf == 1:
        return ("Intermediate metabolizer", "caution",
                "Clopidogrel activates less in your body. After a stent or heart event, CPIC advises another antiplatelet drug." + CONFIRM)
    if inc == 2:
        return ("Ultrarapid metabolizer", "adjust",
                "You break down some antidepressants (citalopram, sertraline) and PPIs fast. CPIC can advise a different drug or dose." + CONFIRM)
    if inc == 1:
        return ("Rapid metabolizer", "standard",
                "Clopidogrel works normally. Some PPIs can need a higher dose." + CONFIRM)
    return ("Normal metabolizer", "reassuring", "CYP2C19 drugs work as usual at the tested positions." + CONFIRM)

def thiopurine(entry, c):
    tpmt = c.get("TPMT*2", 0) + max(c.get("TPMT*3B", 0), c.get("TPMT*3C", 0))
    nudt = c.get("NUDT15*3", 0)
    if tpmt >= 2 or nudt >= 2:
        return ("Poor metabolizer", "avoid",
                "Normal doses of azathioprine or mercaptopurine can cause severe bone-marrow toxicity. CPIC advises a much lower dose or another drug." + CONFIRM)
    if tpmt == 1 and nudt == 1:
        return ("Compound intermediate metabolizer", "caution",
                "One reduced copy in both TPMT and NUDT15. CPIC (2025) advises a larger dose reduction than for one gene." + CONFIRM)
    if tpmt == 1 or nudt == 1:
        note = " TPMT *3B and *3C together are most likely one *3A allele; *3B/*3C cannot be excluded." if c.get("TPMT*3B") and c.get("TPMT*3C") else ""
        return ("Intermediate metabolizer", "adjust",
                "CPIC advises a lower starting dose of thiopurines." + note + CONFIRM)
    return ("Normal metabolizer", "reassuring", "Thiopurine drugs: standard dose at the tested positions." + CONFIRM)

def dpyd(entry, c):
    activity = 2.0
    for a in entry["alleles"]:
        activity -= c.get(a["name"], 0) * (1 - a["value"])
    activity = max(activity, 0.0)
    pending = " A pending CPIC update (2026) can change the HapB3 value from 0.5 to 0.75." if c.get("HapB3") else ""
    if activity <= 0.5:
        return ("Poor metabolizer", "avoid",
                f"DPYD activity score {activity:g}. 5-FU and capecitabine can be life-threatening. CPIC advises to avoid them." + CONFIRM)
    if activity < 2:
        return ("Intermediate metabolizer", "caution",
                f"DPYD activity score {activity:g}. CPIC advises to start 5-FU or capecitabine at 50% of the dose." + pending + CONFIRM)
    return ("Normal metabolizer", "reassuring", "DPYD activity score 2: standard fluoropyrimidine dose at the tested positions." + CONFIRM)

RULES = {"cyp2c19": cyp2c19, "thiopurine": thiopurine, "dpyd": dpyd}
