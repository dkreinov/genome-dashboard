# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import pgx_rules as pr, engine_pgx

def A(name, gene, rsid, ref, alt, value=0):
    return {"name": name, "gene": gene, "rsid": rsid, "probes": [rsid], "ref": ref, "alt": alt, "value": value}

C19 = {"drug": "Clopidogrel", "gene": "CYP2C19", "rule": "cyp2c19", "source": "x",
       "alleles": [A("*2", "CYP2C19", "rs4244285", "G", "A"), A("*3", "CYP2C19", "rs4986893", "G", "A"),
                   A("*4", "CYP2C19", "rs28399504", "A", "G"), A("*17", "CYP2C19", "rs12248560", "C", "T")]}
TP = {"drug": "Thiopurines", "gene": "TPMT + NUDT15", "rule": "thiopurine", "source": "x",
      "alleles": [A("TPMT*2", "TPMT", "rs1800462", "C", "G"), A("TPMT*3B", "TPMT", "rs1800460", "C", "T"),
                  A("TPMT*3C", "TPMT", "rs1142345", "T", "C"), A("NUDT15*3", "NUDT15", "rs116855232", "C", "T")]}
DP = {"drug": "Fluoropyrimidines", "gene": "DPYD", "rule": "dpyd", "source": "x",
      "alleles": [A("*2A", "DPYD", "rs3918290", "C", "T", 0), A("*13", "DPYD", "rs55886062", "A", "C", 0),
                  A("c.2846A>T", "DPYD", "rs67376798", "T", "A", 0.5), A("HapB3", "DPYD", "rs75017182", "G", "C", 0.5)]}

def calls(**gts): return {k: {"genotype": v} for k, v in gts.items()}

def pheno(entry, c):
    counts, _ = pr.count_alleles(entry, c)
    return pr.RULES[entry["rule"]](entry, counts)[0]

def test_cyp2c19():
    base = dict(rs4244285="GG", rs4986893="GG", rs28399504="AA", rs12248560="CC")
    assert pheno(C19, calls(**base)) == "Normal metabolizer"
    assert pheno(C19, calls(**{**base, "rs28399504": "AG"})) == "Intermediate metabolizer"   # *4
    assert pheno(C19, calls(**{**base, "rs4244285": "AA"})) == "Poor metabolizer"
    assert pheno(C19, calls(**{**base, "rs12248560": "CT"})) == "Rapid metabolizer"
    assert pheno(C19, calls(**{**base, "rs12248560": "TT"})) == "Ultrarapid metabolizer"
    assert pheno(C19, calls(**{**base, "rs4244285": "AG", "rs12248560": "CT"})) == "Intermediate metabolizer"

def test_thiopurine():
    base = dict(rs1800462="CC", rs1800460="CC", rs1142345="TT", rs116855232="CC")
    assert pheno(TP, calls(**base)) == "Normal metabolizer"
    assert pheno(TP, calls(**{**base, "rs1800460": "CT", "rs1142345": "CT"})) == "Intermediate metabolizer"  # *3A
    assert pheno(TP, calls(**{**base, "rs1142345": "CC"})) == "Poor metabolizer"
    assert pheno(TP, calls(**{**base, "rs1142345": "CT", "rs116855232": "CT"})) == "Compound intermediate metabolizer"

def test_dpyd_activity_score():
    base = dict(rs3918290="CC", rs55886062="AA", rs67376798="TT", rs75017182="GG")
    assert pheno(DP, calls(**base)) == "Normal metabolizer"
    assert pheno(DP, calls(**{**base, "rs75017182": "CG"})) == "Intermediate metabolizer"   # AS 1.5
    assert pheno(DP, calls(**{**base, "rs3918290": "CT"})) == "Intermediate metabolizer"    # AS 1
    assert pheno(DP, calls(**{**base, "rs3918290": "TT"})) == "Poor metabolizer"            # AS 0

def test_missing_allele_probe_reported():
    counts, untested = pr.count_alleles(C19, calls(rs4244285="GG", rs12248560="CC"))
    assert untested == ["*3", "*4"] and counts["*3"] == 0

def test_engine_shipped_catalog_runs_and_reports_cyp2d6():
    out = engine_pgx.run({})
    names = [d["gene"] for d in out["drugs"]]
    assert "CYP2D6" in names                       # the "not tested" card always shows
    assert all("rs12769205" not in d["rsid"] for d in out["drugs"])

def test_every_non_normal_pgx_text_says_confirm():
    import json
    cat = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reference", "pgx_catalog.json"), encoding="utf-8"))
    bad = []
    for e in cat:
        for gt, (ph, category, text) in e.get("gt", {}).items():
            if category != "reassuring" and "confirm" not in text.lower():
                bad.append((e["rsid"], gt))
    assert not bad, bad

def test_incomplete_normal_is_not_reassuring():
    c = calls(rs55886062="AA", rs67376798="TT", rs75017182="GG")   # rs3918290 not tested
    card = engine_pgx._gene_card(DP, c)
    assert card["phenotype"] == "Normal at tested positions (incomplete)"
    assert card["category"] == "standard"
    assert "Not tested on this chip" in card["text"]
