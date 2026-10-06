# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import probes

E = {"rsid": "rs387906309", "probes": ["i4000391", "rs387906309"]}

def test_ids_uses_probes_then_rsid():
    assert probes.ids(E) == ["i4000391", "rs387906309"]
    assert probes.ids({"rsid": "rs123"}) == ["rs123"]
    assert probes.ids({"rsid": "rs9", "probes": ["i1"]}) == ["i1", "rs9"]

def test_find_prefers_first_available_probe():
    calls = {"i4000391": {"genotype": "DD"}, "rs387906309": {"genotype": "DI"}}
    assert probes.find(calls, E) == ("i4000391", {"genotype": "DD"})

def test_find_falls_back_to_rsid_and_skips_nocall():
    calls = {"i4000391": {"genotype": "--"}, "rs387906309": {"genotype": "DI"}}
    assert probes.find(calls, E) == ("rs387906309", {"genotype": "DI"})
    assert probes.find({}, E) == (None, None)

def test_alt_count():
    assert probes.alt_count("CC", "C", "T") == 0
    assert probes.alt_count("CT", "C", "T") == 1
    assert probes.alt_count("TT", "C", "T") == 2
    assert probes.alt_count("DI", "D", "I") == 1
    assert probes.alt_count("T", "C", "T") == 1          # haploid
    assert probes.alt_count("AG", "C", "T") is None      # unexpected alleles (strand error)
