# -*- coding: utf-8 -*-
import os, sys, tempfile, json
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import verify_probes as vp

def _raw(lines):
    p = os.path.join(tempfile.mkdtemp(), "raw.txt")
    open(p, "w").write("# rsid\tchromosome\tposition\tgenotype\n" + "\n".join(lines) + "\n")
    return p

def test_positions_and_alleles_without_genotype():
    p = _raw(["i4000415\t1\t155205634\tTT", "rs1\t2\t10\t--"])
    pos = vp.read_positions(p)
    assert pos["i4000415"] == ("1", 155205634, {"T"})
    assert pos["rs1"][2] == set()

def test_at_position():
    p = _raw(["i4000415\t1\t155205634\tTT", "rs76763715\t1\t155205634\tTT"])
    assert sorted(vp.at_position(p, "1", 155205634)) == ["i4000415", "rs76763715"]

def test_check_statuses():
    panel = json.load(open(os.path.join(ROOT, "reference", "vcf_panel.json")))["rsids"]
    e = json.load(open(os.path.join(ROOT, "reference", "carrier_catalog.json")))
    gba = next(x for x in e if x["gene"] == "GBA1" and x["variant"] == "N370S")
    pos37 = panel[gba["rsid"]]["pos37"]
    p = _raw([f"i4000415\t1\t{pos37}\tTT", "i4000391\t15\t1\tDD"])
    rows = {r[0]: r[2] for r in vp.check(p)}
    assert rows["i4000415"] == "OK"
    assert rows["i4000391"].startswith("POSITION MISMATCH")
    assert rows.get("i4000438") == "NOT ON CHIP"

def test_cli_never_prints_genotypes(capsys):
    p = _raw(["i4000415\t1\t155205634\tCT"])
    vp.main([p])
    out = capsys.readouterr().out
    assert "CT" not in out.replace("CTCT", "")

def _entry(rs):
    e = next(x for x in json.load(open(os.path.join(ROOT, "reference", "carrier_catalog.json"))) if x.get("rsid") == rs)
    pn = json.load(open(os.path.join(ROOT, "reference", "vcf_panel.json")))["rsids"][rs]
    return e, pn

def _status(rs, probe, shift, gt):
    e, pn = _entry(rs)
    p = _raw([f"{probe}\t{pn['chrom']}\t{pn['pos37']+shift}\t{gt}"])
    return {r[0]: r[2] for r in vp.check(p)}[probe]

def test_indel_shift_accepted():
    assert _status("rs80357906", "rs80357906", 3, "DD") == "OK (indel shift +3)"
    assert _status("rs80357906", "rs80357906", -1, "DD") == "OK (indel shift -1)"

def test_indel_shift_too_large():
    assert _status("rs80357906", "rs80357906", 12, "DD").startswith("POSITION MISMATCH")

def test_allele_mismatch_at_correct_position():
    assert _status("rs76763715", "i4000415", 0, "GG") == "ALLELE MISMATCH"

def test_allele_mismatch_with_position_mismatch():
    assert _status("rs76763715", "i4000415", 5, "GG") == "ALLELE MISMATCH"

def test_catalog_json_probes_checked_by_position():
    cat = next(x for x in json.load(open(os.path.join(ROOT, "reference", "catalog.json"))) if x.get("probes"))
    pid = cat["probes"][0]
    assert any(label == cat["title"] for label, _, ids, _, _ in vp._entries() if pid in ids)
    assert {r[0] for r in vp.check(_raw([f"{pid}\t1\t1\tAA"]))} >= {pid}
    rows = {r[0]: r[2] for r in vp.check(_raw([f"{pid}\t1\t1\tZZ"]))}
    assert rows[pid] != "ALLELE MISMATCH"
