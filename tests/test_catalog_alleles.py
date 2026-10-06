# -*- coding: utf-8 -*-
"""Guard: every carrier/PGx allele must match Ensembl (GRCh37 plus strand) in vcf_panel.json.
For indels, ref/alt must be the I/D tokens that the VCF reader produces."""
import json, os, sys, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import parse_input, engine_carrier

def load(f): return json.load(open(os.path.join(ROOT, "reference", f), encoding="utf-8"))
PANEL = load("vcf_panel.json")["rsids"]

def _check(rsid, ref, alt, where):
    v = PANEL.get(rsid)
    assert v, f"{where}: {rsid} missing from vcf_panel.json — run scripts/build_vcf_panel.py"
    if v["kind"] == "snv":
        alleles = v["alleles"].split("/")
        assert ref == v["ref"], f"{where}: {rsid} ref {ref} != Ensembl {v['ref']}"
        assert alt in alleles[1:], f"{where}: {rsid} alt {alt} not in {v['alleles']}"
    else:
        rt = parse_input._indel_ref_token(v["alleles"])
        assert (ref, alt) == (rt, "D" if rt == "I" else "I"), f"{where}: {rsid} indel tokens wrong"

def test_catalog_alleles_match_ensembl():
    for e in load("carrier_catalog.json"):
        if not e.get("untestable"):
            _check(e["rsid"], e["ref"], e["alt"], e["variant"])
    for e in load("pgx_catalog.json"):
        for a in e.get("alleles", []):
            _check(a["rsid"], a["ref"], a["alt"], a["name"])

def test_vcf_input_finds_carrier_by_rsid():
    e = next(x for x in load("carrier_catalog.json") if x["gene"] == "GBA1")
    v = PANEL[e["rsid"]]
    vcf = ("##fileformat=VCFv4.2\n##contig=<ID=chr1,length=249250621>\n"
           "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\n"
           f"chr{v['chrom']}\t{v['pos37']}\t.\t{e['ref']}\t{e['alt']}\t50\tPASS\t.\tGT\t0/1\n")
    p = os.path.join(tempfile.mkdtemp(), "t.vcf")
    open(p, "w").write(vcf)
    calls, _ = parse_input.parse_with_meta(p)
    card = engine_carrier.classify(e, calls)
    assert card and card["result"] == "Possible carrier — confirm"

ALIAS = {"GBA1": {"GBA1", "GBA"}, "ELP1": {"ELP1", "IKBKAP"}}

def test_catalog_rsid_matches_gene_and_hgvs():
    """The allele guard cannot detect a wrong rsID. Check the gene and the HGVS string too."""
    for e in load("carrier_catalog.json"):
        if e.get("untestable"):
            continue
        v = PANEL[e["rsid"]]
        names = ALIAS.get(e["gene"], {e["gene"]})
        assert names & set(v.get("genes", [])), f"{e['variant']}: {e['rsid']} genes {v.get('genes')} != {e['gene']}"
        assert e.get("hgvs") in v.get("hgvs", []), f"{e['variant']}: {e['rsid']} hgvs {e.get('hgvs')} not in {v.get('hgvs')}"
