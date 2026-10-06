# -*- coding: utf-8 -*-
"""Round-trip test for the VCF reader (offline; needs reference/vcf_panel.json).

1. Parse the synthetic chip file examples/mock_person.txt (23andMe format, GRCh37).
2. Write it as a whole-genome-style VCF: variant sites ONLY, NO rsIDs in the ID
   column, SNVs and anchored indels, positions in GRCh37 and in GRCh38 (and one
   gzipped copy).
3. Check: every panel genotype the chip has comes back IDENTICAL from the VCF
   (SNVs, I/D indel probes, mtDNA), and every engine runs on the VCF.

Engine outputs are not compared one-to-one: the VCF reader fills untested panel
sites as reference (a real WGS covers them), so Y/mt/catalog get MORE data than
the chip by design. The differences are printed for information.
Run:  python tests/test_vcf_reader.py
"""
import gzip, json, os, sys, tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import parse_input, run_analysis  # noqa: E402

CHIP = os.path.join(ROOT, "examples", "mock_person.txt")
CHR1 = {"37": 249250621, "38": 248956422}

def write_vcf(calls, panel, build, path):
    rs_panel, rcrs = panel["rsids"], panel["mt_rcrs"]
    rows = []
    for rs, rec in calls.items():
        g = rec["genotype"]
        if g == "--" or any(b not in "ACGTID" for b in g):
            continue
        if rec["chrom"] == "MT":
            ref = rcrs[rec["pos"] - 1]
            if g[0] != ref:
                rows.append(("MT", rec["pos"], ref, g[0], "1"))
            continue
        v = rs_panel.get(rs.lower())
        if not v:
            continue
        if v["kind"] == "indel":
            # chip I/D tokens -> anchored VCF indel (anchor base 'A' + allele, POS = start - 1)
            ref_tok = parse_input._indel_ref_token(v["alleles"])
            if set(g) == {ref_tok}:
                continue
            seqs = ["" if a == "-" else a for a in v["alleles"].split("/")]
            gt_idx = ["0" if t == ref_tok else "1" for t in g]
            gt = gt_idx[0] if len(g) == 1 else "/".join(sorted(gt_idx))
            rows.append((v["chrom"], v["pos" + build] - 1, "A" + seqs[0], "A" + seqs[1], gt))
            continue
        if any(b not in "ACGT" for b in g):
            continue
        ref, pos = v["ref"], v["pos" + build]
        if set(g) == {ref}:
            continue                                  # hom-ref: absent from a variant-only VCF
        alts = sorted({b for b in g if b != ref})
        idx = ["0" if b == ref else str(alts.index(b) + 1) for b in g]
        gt = idx[0] if len(g) == 1 else "/".join(sorted(idx))
        rows.append((v["chrom"], pos, ref, ",".join(alts), gt))
    order = {str(i): i for i in range(1, 23)} | {"X": 23, "Y": 24, "MT": 25}
    rows.sort(key=lambda r: (order[r[0]], r[1]))
    head = ["##fileformat=VCFv4.2",
            f"##contig=<ID=chr1,length={CHR1[build]}>",
            '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1"]
    body = [f"chr{c}\t{p}\t.\t{r}\t{a}\t50\tPASS\t.\tGT\t{gt}" for c, p, r, a, gt in rows]
    text = "\n".join(head + body) + "\n"
    if path.endswith(".gz"):
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            fh.write(text)
    else:
        open(path, "w", encoding="utf-8").write(text)
    return len(rows)

def comparable(res):
    res = json.loads(json.dumps(res))
    res.pop("meta", None)
    anc = res.get("ancestry") or {}
    for k in ("roh_total_mb", "roh_big", "roh_longest", "prose"):
        anc.pop(k, None)
    return res

def diff(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            out += diff(a.get(k), b.get(k), f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f"{path}[{i}]")
    elif a != b:
        out.append(f"{path}: chip={str(a)[:80]!r} vcf={str(b)[:80]!r}")
    return out

def main():
    panel = parse_input.load_vcf_panel()
    chip_calls, _ = parse_input.parse_with_meta(CHIP)
    want = comparable(run_analysis.analyze(CHIP))
    tmp = tempfile.mkdtemp()
    failed = False
    rs_panel = panel["rsids"]
    for build, name in (("37", "mock_b37.vcf"), ("38", "mock_b38.vcf"), ("38", "mock_b38.vcf.gz")):
        path = os.path.join(tmp, name)
        n = write_vcf(chip_calls, panel, build, path)
        vcf_calls, m = parse_input.parse_with_meta(path)
        assert m["format"] == "vcf" and m["build"] == "GRCh" + build, m
        bad, checked = [], 0
        for rs, rec in chip_calls.items():
            g = rec["genotype"]
            if g == "--" or rs.lower() not in rs_panel or rec["chrom"] == "MT":
                continue
            checked += 1
            got = vcf_calls.get(rs.lower(), {}).get("genotype")
            if got != g:
                bad.append(f"{rs}: chip={g} vcf={got}")
        # mtDNA: positions the mt caller uses (reference bases elsewhere are not filled, by design)
        tree = json.load(open(os.path.join(ROOT, "reference", "mt_phylotree.json"), encoding="utf-8"))
        mt_used = {p for k, muts in tree.items() if not k.startswith("_") for p, _ in muts}
        mt_bad = [p for p, b in ((r["pos"], r["genotype"]) for r in chip_calls.values() if r["chrom"] == "MT"
                                 and r["genotype"] not in ("--", "") and r["pos"] in mt_used)
                  if not any(v["chrom"] == "MT" and v["pos"] == p and v["genotype"] == b[0] for v in vcf_calls.values())]
        res = run_analysis.analyze(path)                 # every engine must run on VCF input
        info = diff(want, comparable(res))
        ok = not bad and not mt_bad
        print(f"{name}: {n} variant rows | {checked} panel genotypes checked, {len(bad)} wrong | "
              f"mt wrong {len(mt_bad)} | engines ran, {len(info)} info-diffs (extra coverage) -> "
              f"{'OK' if ok else 'FAIL'}")
        for line in bad[:10] + [f"MT:{p}" for p in mt_bad[:5]]:
            print("   ", line)
        failed |= not ok
    print("engine differences (from extra WGS coverage, informational):")
    for line in info[:12]:
        print("   ", line)
    print("FAIL" if failed else "PASS")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
