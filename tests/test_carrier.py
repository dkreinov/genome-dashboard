# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import engine_carrier as ec

TS = {"disease": "Tay-Sachs disease", "gene": "HEXA", "variant": "1278insTATC",
      "rsid": "rs387906309", "probes": ["i4000391", "rs387906309"], "ref": "D", "alt": "I",
      "inheritance": "recessive", "tier": "A", "aj_carrier_pct": 2.85, "residual": "1 in 2,700", "detection": "",
      "source": "https://example.org"}
BR = {"disease": "Hereditary breast and ovarian cancer", "gene": "BRCA2", "variant": "6174delT",
      "rsid": "rs80359550", "probes": ["rs80359550"], "confirm_probes": ["i4000379"],
      "ref": "I", "alt": "D", "inheritance": "dominant", "tier": "A",
      "aj_carrier_pct": 1.1, "residual": "", "source": "https://example.org"}
SMA = {"disease": "Spinal muscular atrophy", "gene": "SMN1", "variant": "copy number",
       "rsid": "", "untestable": "SMA needs an SMN1 copy-number test.", "inheritance": "recessive",
       "tier": "", "aj_carrier_pct": None, "residual": "", "source": "https://example.org"}

def g(gt): return {"genotype": gt}

def test_not_detected_shows_residual_risk():
    c = ec.classify(TS, {"i4000391": g("DD")})
    assert (c["result"], c["category"]) == ("Not detected", "reassuring")
    assert "the remaining risk to be a carrier after a negative full 23andMe test for this disease is 1 in 2,700." in c["text"]

def test_carrier_says_test_partner():
    c = ec.classify(TS, {"i4000391": g("DI")})
    assert (c["result"], c["category"]) == ("Possible carrier — confirm", "caution")
    assert "partner" in c["text"] and "accredited lab" in c["text"]

def test_homozygous_alt_flagged():
    c = ec.classify(TS, {"i4000391": g("II")})
    assert c["result"] == "Two copies — confirm" and c["category"] == "caution"
    assert "can mean the condition" in c["text"] and "test the partner" in c["text"]

def test_homozygous_rare_keeps_chip_error_text():
    rare = dict(TS, aj_carrier_pct=0.1)
    c = ec.classify(rare, {"i4000391": g("II")})
    assert c["result"] == "Two copies — probably a chip error, confirm"

def test_homozygous_dominant_common_has_no_partner_sentence():
    br = dict(BR, aj_carrier_pct=2.0)
    c = ec.classify(br, {"rs80359550": g("DD")})
    assert c["result"] == "Two copies — confirm" and "partner" not in c["text"]

def test_probes_disagree_recessive_says_partner():
    e = dict(TS, confirm_probes=["i4000392"])
    c = ec.classify(e, {"i4000391": g("DI"), "i4000392": g("II")})
    assert c["result"] == "Unclear — probes disagree, confirm" and "test the partner" in c["text"]

def test_detection_sentence():
    e = dict(TS, residual="", detection="93%")
    c = ec.classify(e, {"i4000391": g("DD")})
    assert "finds about 93% of carriers in Ashkenazi Jews" in c["text"]
    assert "remaining risk" not in c["text"] and c["detection"] == "93%"

def test_two_variants_in_one_gene_extra_card():
    a = dict(TS, variant="v1", probes=["rsA"], rsid="rsA")
    b = dict(TS, variant="v2", probes=["rsB"], rsid="rsB")
    c = dict(TS, gene="OTHER", variant="v3", probes=["rsC"], rsid="rsC")
    out = ec.run_entries([a, b, c], {"rsA": g("DI"), "rsB": g("DI"), "rsC": g("DI")})["variants"]
    extra = [v for v in out if v["variant"] == "two variants"]
    assert len(extra) == 1 and extra[0]["gene"] == "HEXA" and extra[0]["gt"] == "—"
    assert extra[0]["result"] == "Two variants in one gene — confirm" and extra[0]["category"] == "caution"
    assert "different copies" in extra[0]["text"] and "test the partner" in extra[0]["text"]
    assert len(out) == 4

def test_missing_probe_skipped():
    assert ec.classify(TS, {}) is None

def test_nocall_skipped():
    assert ec.classify(TS, {"i4000391": g("--")}) is None

def test_unexpected_alleles():
    assert ec.classify(TS, {"i4000391": g("AG")})["result"] == "Unexpected genotype — check"

def test_dominant_variant_wording():
    c = ec.classify(BR, {"rs80359550": g("DI")})
    assert c["result"] == "Possible variant — confirm"

def test_second_probe_disagreement():
    c = ec.classify(BR, {"rs80359550": g("DI"), "i4000379": g("II")})
    assert c["result"] == "Unclear — probes disagree, confirm"

def test_second_probe_agreement_keeps_result():
    c = ec.classify(BR, {"rs80359550": g("II"), "i4000379": g("II")})
    assert c["result"] == "Not detected"

def test_untestable_card():
    c = ec.classify(SMA, {})
    assert (c["result"], c["category"]) == ("Not testable on this chip", "untestable")

def test_run_uses_shipped_catalog():
    out = ec.run({})
    assert all(v["category"] == "untestable" for v in out["variants"])

def test_render_shows_carrier_details_and_untestable_color():
    import render_html, safety, run_analysis
    a = run_analysis.analyze(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", "mock_person.txt"))
    html = render_html.render(a, "unused.html", safety.load(), opts={})   # render() returns the HTML string
    assert "Ashkenazi carriers" in html          # carrier detail line
    assert "#6b7280" in html                     # grey untestable card (SMA / CYP2D6)
    assert "Not testable on this chip" in html
