# -*- coding: utf-8 -*-
"""Generic raw-DNA input normalizer.

FROZEN CONTRACT (Phase 1, Step 2) — every engine consumes this:
    parse(path) -> dict {
        rsid(str): {"chrom": str, "pos": int, "genotype": str}
    }
    plus a companion meta dict from parse_with_meta().

Rules:
- Genotype is on the reference PLUS strand (both 23andMe and AncestryDNA report
  GRCh37 plus strand). Alleles are UPPERCASED and SORTED so AG == GA.
- Diploid calls are 2 chars ("AG"); haploid (Y / MT in males) are kept as given
  (1 char). No-calls ("--", "00", "0", "", "II"/"DD" handled by callers) pass through
  as "--" for missing, but indel tokens I/D are preserved (some carrier probes use them).
- Chromosomes normalized to: 1..22, "X", "Y", "MT".
- Unknown / malformed lines are counted, never crash.

Supported formats (auto-detected):
- 23andMe v3/v4/v5:  tab  rsid  chrom  pos  genotype
- AncestryDNA:       tab  rsid  chrom  pos  allele1  allele2
"""
import io, re

_CHROM = {"23": "X", "24": "Y", "25": "MT", "26": "MT", "MT": "MT", "X": "X", "Y": "Y"}

def _norm_chrom(c):
    c = c.strip().upper()
    return _CHROM.get(c, c)

def _norm_geno(g):
    g = g.strip().upper()
    if g in ("", "--", "00", "0", "NN"):
        return "--"
    if g in ("I", "D", "II", "DD", "DI", "ID"):          # indel probes: keep, sort
        return "".join(sorted(g))
    g = "".join(ch for ch in g if ch in "ACGT")
    if not g:
        return "--"
    return "".join(sorted(g))

def detect_format(sample_lines):
    """Return '23andme', 'ancestrydna', or 'unknown' from the first data rows."""
    for ln in sample_lines:
        if ln.startswith("#") or not ln.strip():
            if "ancestry" in ln.lower():
                return "ancestrydna"
            continue
        cols = ln.rstrip("\n").split("\t")
        if cols[0].lower() == "rsid":                     # header row
            n = len(cols)
            return "ancestrydna" if n >= 5 else "23andme"
        n = len(cols)
        if n == 4:
            return "23andme"
        if n >= 5:
            return "ancestrydna"
    return "unknown"

def parse_with_meta(path):
    calls, meta = {}, {"format": None, "n_lines": 0, "n_parsed": 0, "n_skipped": 0,
                       "chroms": {}}
    with io.open(path, encoding="utf-8", errors="ignore") as fh:
        head = [next(fh, "") for _ in range(40)]
    fmt = detect_format(head)
    meta["format"] = fmt
    with io.open(path, encoding="utf-8", errors="ignore") as fh:
        for ln in fh:
            if not ln.strip() or ln.startswith("#"):
                continue
            cols = ln.rstrip("\n").split("\t")
            if cols[0].lower() == "rsid":                 # header
                continue
            meta["n_lines"] += 1
            try:
                if fmt == "ancestrydna" and len(cols) >= 5:
                    rsid, chrom, pos, a1, a2 = cols[0], cols[1], cols[2], cols[3], cols[4]
                    geno = _norm_geno(a1 + a2)
                elif len(cols) >= 4:
                    rsid, chrom, pos, geno = cols[0], cols[1], cols[2], _norm_geno(cols[3])
                else:
                    meta["n_skipped"] += 1
                    continue
                chrom = _norm_chrom(chrom)
                pos = int(pos) if pos.isdigit() else 0
                calls[rsid] = {"chrom": chrom, "pos": pos, "genotype": geno}
                meta["chroms"][chrom] = meta["chroms"].get(chrom, 0) + 1
                meta["n_parsed"] += 1
            except Exception:
                meta["n_skipped"] += 1
    return calls, meta

def parse(path):
    return parse_with_meta(path)[0]

if __name__ == "__main__":
    import sys, json
    for p in sys.argv[1:]:
        calls, meta = parse_with_meta(p)
        print(f"{p}: format={meta['format']} parsed={meta['n_parsed']} "
              f"skipped={meta['n_skipped']} chroms={len(meta['chroms'])}")
        # show a couple sample records
        for rsid in list(calls)[:2]:
            print("   ", rsid, calls[rsid])
