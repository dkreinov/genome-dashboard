# -*- coding: utf-8 -*-
"""Check catalog probes against a 23andMe raw file. PRIVACY: prints probe IDs,
labels, positions and OK/MISMATCH only — never a genotype.

Usage:
  python scripts/verify_probes.py RAW_FILE              # check all catalog probes
  python scripts/verify_probes.py RAW_FILE --at 13:32914438   # probe IDs at a GRCh37 position
"""
import json, os, sys

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reference")

def _load(f):
    return json.load(open(os.path.join(REF, f), encoding="utf-8"))

def read_positions(raw_path):
    out = {}
    with open(raw_path, encoding="utf-8", errors="ignore") as fh:
        for ln in fh:
            if ln.startswith("#") or not ln.strip():
                continue
            c = ln.rstrip("\n").split("\t")
            if len(c) < 4 or not c[2].isdigit():
                continue
            seen = {ch for ch in c[3].upper() if ch in "ACGTID"}
            out[c[0]] = (c[1].upper().replace("MT", "MT"), int(c[2]), seen)
    return out

def at_position(raw_path, chrom, pos):
    return [pid for pid, (ch, p, _) in read_positions(raw_path).items() if ch == str(chrom) and p == int(pos)]

def _entries():
    """Yield (label, rsid, probe_ids, ref, alt). ref/alt are None when the allele check is skipped."""
    for e in _load("carrier_catalog.json"):
        if not e.get("untestable"):
            yield e["variant"], e["rsid"], e.get("probes", [e["rsid"]]) + e.get("confirm_probes", []), e["ref"], e["alt"]
    for e in _load("pgx_catalog.json"):
        for a in e.get("alleles", []):
            yield a["name"], a["rsid"], a["probes"], a["ref"], a["alt"]
    for e in _load("catalog.json"):
        if e.get("probes"):                         # position check only: no allele check
            yield e["title"], e["rsid"], e["probes"], None, None

def check(raw_path):
    pos = read_positions(raw_path)
    panel = _load("vcf_panel.json")["rsids"]
    rows = []
    for label, rsid, probe_ids, ref, alt in _entries():
        exp = panel.get(rsid)
        for pid in probe_ids:
            if pid not in pos:
                rows.append((pid, label, "NOT ON CHIP"))
                continue
            ch, p, seen = pos[pid]
            status = "OK"
            if exp and (ch != exp["chrom"] or p != exp["pos37"]):
                shift = p - exp["pos37"]
                if ch == exp["chrom"] and exp.get("kind") == "indel" and 1 <= abs(shift) <= 10:
                    status = f"OK (indel shift {shift:+d})"
                else:
                    status = f"POSITION MISMATCH (expected {exp['chrom']}:{exp['pos37']})"
            if ref and seen and not seen <= {ref, alt}:
                status = "ALLELE MISMATCH"
            rows.append((pid, label, status))
    return rows

def main(argv):
    if len(argv) >= 3 and argv[1] == "--at":
        ch, p = argv[2].split(":")
        for pid in at_position(argv[0], ch, p):
            print(pid)
        return
    for pid, label, status in check(argv[0]):
        print(f"{pid:14} {label:22} {status}")

if __name__ == "__main__":
    main(sys.argv[1:])
