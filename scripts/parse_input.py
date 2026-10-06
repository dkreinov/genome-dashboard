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
- VCF / gVCF (.vcf or .vcf.gz) from whole-genome or exome sequencing, GRCh37 or
  GRCh38 (build auto-detected). See parse_vcf() for how it maps to the contract.
"""
import gzip, io, json, os, re
from bisect import bisect_left

_REF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reference")
VCF_BACKGROUND_STEP = 4   # keep every Nth non-panel autosomal SNV (ROH scan); 1 = all (more RAM)

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

def _open_text(path):
    with open(path, "rb") as fh:
        gz = fh.read(2) == b"\x1f\x8b"
    if gz:
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", errors="ignore")
    return io.open(path, encoding="utf-8", errors="ignore")

def is_vcf(path):
    with _open_text(path) as fh:
        return fh.readline().startswith("##fileformat=VCF")

# ── VCF ──────────────────────────────────────────────────────────────────────

_CHR1_LEN = {"249250621": "37", "248956422": "38"}

def _vcf_build(header_lines):
    """'37' / '38' from ##contig chr1 length, else from ##reference text, else None."""
    for ln in header_lines:
        m = re.match(r"##contig=<ID=(?:chr)?1,.*?length=(\d+)", ln)
        if m and m.group(1) in _CHR1_LEN:
            return _CHR1_LEN[m.group(1)]
    for ln in header_lines:
        if ln.startswith("##reference") or ln.startswith("##contig") or ln.startswith("##assembly"):
            low = ln.lower()
            if re.search(r"grch38|hg38|hs38|b38", low):
                return "38"
            if re.search(r"grch37|hg19|hs37|b37|human_g1k_v37", low):
                return "37"
    return None

def _vcf_chrom(c):
    c = c.strip()
    if c.lower().startswith("chr"):
        c = c[3:]
    c = c.upper()
    return "MT" if c in ("M", "MT") else _CHROM.get(c, c)

def _indel_tokens(ref, alts, bases):
    """23andMe I/D convention: I = the longer allele, D = the shorter one.
    The variant's direction comes from the first ALT; an allele as long as REF is
    the reference allele: I for a deletion variant, D for an insertion variant."""
    deletion = len(alts[0]) < len(ref)
    out = []
    for b in bases:
        if len(b) > len(ref):
            out.append("I")
        elif len(b) < len(ref):
            out.append("D")
        else:
            out.append("I" if deletion else "D")
    return "".join(sorted(out))

def _indel_ref_token(allele_string):
    """Hom-ref token for an indel probe from the Ensembl allele string ("-" = empty).
    Direction comes from the first ALT (the main variant), as in _indel_tokens."""
    al = [0 if a == "-" else len(a) for a in allele_string.split("/")]
    return "I" if al[0] > al[1] else "D"

def load_vcf_panel():
    p = os.path.join(_REF_DIR, "vcf_panel.json")
    if not os.path.exists(p):
        raise FileNotFoundError("reference/vcf_panel.json missing — run scripts/build_vcf_panel.py once (online).")
    return json.load(open(p, encoding="utf-8"))

def parse_vcf(path, build=None, background_step=VCF_BACKGROUND_STEP):
    """VCF -> (calls, meta) in the frozen contract.

    How the contract is met:
    - Panel rsIDs (the ~475 the engines use) are matched by POSITION in the
      file's build via reference/vcf_panel.json (WGS VCFs usually have no rsIDs);
      an rsID in the ID column is used too. Keys are lowercase "rs..." ids.
    - Only SNVs are read (the engines have no indel probes). First sample only.
    - Haploid calls (male X/Y, MT) give 1 char; diploid calls give 2 sorted chars.
    - A plain VCF lists only variant sites. A panel SNV that is NOT in the file is
      filled as homozygous REFERENCE (meta["n_inferred_ref"] counts these). In a
      gVCF, reference blocks (<NON_REF>/END=) confirm hom-ref instead of inferring.
      Y is filled only if the file has Y calls (male); X is filled diploid for
      females and haploid for males.
    - mtDNA: every MT SNV is kept (key "MT:<pos>"); uncalled positions used by
      the mt caller are filled with the rCRS base.
    - For the ROH scan, every `background_step`-th other autosomal SNV is kept
      under key "<chrom>:<pos>" (homozygous-ALT and het sites; ROH = runs with no het).
    """
    panel = load_vcf_panel()
    rs_panel = panel["rsids"]
    meta = {"format": "vcf", "build": None, "gvcf": False, "sample": None, "n_lines": 0, "n_parsed": 0,
            "n_skipped": 0, "n_panel_called": 0, "n_inferred_ref": 0, "n_panel_missing": 0,
            "background_step": background_step, "chroms": {}}
    header = []
    with _open_text(path) as fh:
        for ln in fh:
            if not ln.startswith("#"):
                break
            header.append(ln.rstrip("\n"))
    build = build or _vcf_build(header)
    if build not in ("37", "38"):
        raise ValueError("Cannot detect genome build (GRCh37/GRCh38) from the VCF header; pass build='37' or '38'.")
    meta["build"] = "GRCh" + build
    cols = header[-1].lstrip("#").split("\t") if header else []
    meta["sample"] = cols[9] if len(cols) > 9 else None
    poskey = "pos" + build

    by_pos = {}                                     # (chrom, pos) -> rsid
    indel_win = {}                                  # chrom -> [(lo, hi, rsid)] for indel probes
    for rs, v in rs_panel.items():
        if not v.get(poskey):
            continue
        if v["kind"] == "snv":
            by_pos[(v["chrom"], v[poskey])] = rs
        else:
            # VCF left-aligns indels with an anchor base, so the VCF POS can sit a little
            # before Ensembl's start or anywhere inside the repeat.
            ref_len = 0 if v["ref"] == "-" else len(v["ref"])
            indel_win.setdefault(v["chrom"], []).append((v[poskey] - 2, v[poskey] + ref_len, rs))
    ref_blocks = {}                                 # chrom -> list of (start, end) hom-ref blocks (gVCF)
    calls, n_bg = {}, 0

    with _open_text(path) as fh:
        for ln in fh:
            if ln.startswith("#") or not ln.strip():
                continue
            meta["n_lines"] += 1
            f = ln.rstrip("\n").split("\t")
            if len(f) < 10:
                meta["n_skipped"] += 1
                continue
            chrom, pos, vid, ref, alt = _vcf_chrom(f[0]), int(f[1]), f[2], f[3].upper(), f[4].upper()
            fmt_keys, sample = f[8].split(":"), f[9].split(":")
            gt = dict(zip(fmt_keys, sample)).get("GT", ".")
            alts = [a for a in alt.split(",")]
            if alts in (["<NON_REF>"], ["<*>"], ["."]):             # gVCF reference block
                meta["gvcf"] = meta["gvcf"] or alts != ["."]
                end = re.search(r"(?:^|;)END=(\d+)", f[7])
                if gt.replace("|", "/") in ("0/0", "0") and end:
                    ref_blocks.setdefault(chrom, []).append((pos, int(end.group(1))))
                continue
            alleles = [ref] + alts
            idx = re.split(r"[/|]", gt)
            if any(i in (".", "") for i in idx):
                meta["n_skipped"] += 1
                continue
            try:
                bases = [alleles[int(i)] for i in idx]
            except (IndexError, ValueError):
                meta["n_skipped"] += 1
                continue
            if any(len(a) != len(ref) for a in alts):                 # indel record
                rsid = next((rs for lo, hi, rs in indel_win.get(chrom, ()) if lo <= pos <= hi), None)
                if rsid and rsid not in calls:
                    calls[rsid] = {"chrom": chrom, "pos": pos, "genotype": _indel_tokens(ref, alts, bases)}
                    meta["n_panel_called"] += 1
                    meta["n_parsed"] += 1
                else:
                    meta["n_skipped"] += 1
                continue
            if len(ref) != 1:
                meta["n_skipped"] += 1
                continue
            if any(len(b) != 1 or b not in "ACGT" for b in bases):  # indel / symbolic allele
                meta["n_skipped"] += 1
                continue
            rsid = by_pos.get((chrom, pos)) or (vid.lower() if vid.lower().startswith("rs") else None)
            if chrom == "MT":
                base = bases[-1] if len(set(bases)) > 1 else bases[0]   # heteroplasmy: take the ALT
                key, geno = rsid or f"MT:{pos}", base
            else:
                geno = "".join(sorted(bases))
                if rsid and rsid in rs_panel:
                    key = rsid
                    meta["n_panel_called"] += 1
                elif chrom in ("X", "Y") or len(set(bases)) == 1 and bases[0] == ref:
                    continue                                          # no ROH value
                else:
                    n_bg += 1
                    if n_bg % background_step:
                        continue
                    key = rsid or f"{chrom}:{pos}"
            calls[key] = {"chrom": chrom, "pos": pos, "genotype": geno}
            meta["chroms"][chrom] = meta["chroms"].get(chrom, 0) + 1
            meta["n_parsed"] += 1

    # Fill panel SNVs absent from the file as homozygous reference.
    male = any(r["chrom"] == "Y" for r in calls.values())
    for blocks in ref_blocks.values():
        blocks.sort()
    def in_ref_block(chrom, pos):
        b = ref_blocks.get(chrom)
        if not b:
            return False
        i = bisect_left(b, (pos + 1,)) - 1
        return i >= 0 and b[i][0] <= pos <= b[i][1]
    for rs, v in rs_panel.items():
        if rs in calls or not v.get(poskey):
            continue
        ch = v["chrom"]
        if ch == "MT" or (ch == "Y" and not male):
            continue
        if meta["gvcf"] and not in_ref_block(ch, v[poskey]):
            meta["n_panel_missing"] += 1            # gVCF: not covered -> genuinely unknown
            continue
        haploid = ch == "Y" or (ch == "X" and male)
        tok = v["ref"] if v["kind"] == "snv" else _indel_ref_token(v["alleles"])
        calls[rs] = {"chrom": ch, "pos": v[poskey], "genotype": tok if haploid else tok * 2,
                     "inferred": True}
        meta["n_inferred_ref"] += 1
    # mtDNA: uncalled positions used by the mt haplogroup caller -> rCRS base.
    rcrs = panel.get("mt_rcrs", "")
    mt_called = {r["pos"] for r in calls.values() if r["chrom"] == "MT"}
    if rcrs and any(r["chrom"] == "MT" for r in calls.values()):
        tree = json.load(open(os.path.join(_REF_DIR, "mt_phylotree.json"), encoding="utf-8"))
        for clade, muts in tree.items():
            if clade.startswith("_"):
                continue
            for p, _ in muts:
                if p not in mt_called and 0 < p <= len(rcrs):
                    calls[f"MT:{p}"] = {"chrom": "MT", "pos": p, "genotype": rcrs[p - 1], "inferred": True}
                    mt_called.add(p)
    return calls, meta

# ── chip arrays (23andMe / AncestryDNA) ──────────────────────────────────────

def parse_with_meta(path):
    if is_vcf(path):
        return parse_vcf(path)
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
        if meta["format"] == "vcf":
            print(f"    build={meta['build']} gvcf={meta['gvcf']} panel_called={meta['n_panel_called']} "
                  f"inferred_ref={meta['n_inferred_ref']} panel_missing={meta['n_panel_missing']}")
        # show a couple sample records
        for rsid in list(calls)[:2]:
            print("   ", rsid, calls[rsid])
