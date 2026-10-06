# -*- coding: utf-8 -*-
"""Probe lookup for catalog entries.

23andMe v5 stores many clinical variants only under internal "i" IDs
(for example Tay-Sachs 1278insTATC = i4000391). A VCF has rsIDs only.
An entry lists its probes in order; the first probe with a call is used.
"""

def ids(entry):
    out = list(entry.get("probes") or [])
    rs = entry.get("rsid")
    if rs and rs not in out:
        out.append(rs)
    return out

def find(calls, entry):
    for pid in ids(entry):
        rec = calls.get(pid)
        if rec and rec.get("genotype") not in (None, "", "--"):
            return pid, rec
    return None, None

def alt_count(genotype, ref, alt):
    g = (genotype or "").upper()
    if any(ch not in (ref, alt) for ch in g):
        return None
    return g.count(alt)
