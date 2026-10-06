# -*- coding: utf-8 -*-
"""Opt-in, online: build reference/vcf_panel.json for the VCF reader.

A whole-genome VCF has no rsIDs (often), lists only variant sites, and is often
GRCh38. The engines look up ~475 rsIDs (GRCh37-era chip ids). This panel gives,
for every rsID the skill uses:
    {"chrom", "pos37", "pos38", "ref", "alleles", "kind"}
    (ref = forward-strand reference allele; alleles = Ensembl allele_string, "-" = none;
     kind = "snv" or "indel")
plus the rCRS mtDNA sequence (same in GRCh37 and GRCh38) so uncalled mtDNA
positions can be filled with the reference base.

Source: Ensembl REST (rest.ensembl.org = GRCh38, grch37.rest.ensembl.org = GRCh37).
Run:  python scripts/build_vcf_panel.py
"""
import glob, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "reference")
OUT = os.path.join(REF, "vcf_panel.json")
HOSTS = {"38": "https://rest.ensembl.org", "37": "https://grch37.rest.ensembl.org"}
CHROMS = {str(i) for i in range(1, 23)} | {"X", "Y", "MT"}

def used_rsids():
    """Every rsID mentioned in the reference data or the engines (case-insensitive)."""
    ids = set()
    for path in glob.glob(os.path.join(REF, "*.json")) + glob.glob(os.path.join(HERE, "engine_*.py")):
        if os.path.basename(path) == "vcf_panel.json":
            continue
        txt = open(path, encoding="utf-8", errors="ignore").read()
        ids |= {m.lower() for m in re.findall(r"\b[Rr]s\d{3,}\b", txt)}
    return sorted(ids)

def post(host, ids):
    req = urllib.request.Request(host + "/variation/homo_sapiens", data=json.dumps({"ids": ids}).encode(),
                                 headers={"Content-Type": "application/json", "Accept": "application/json"},
                                 method="POST")
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Ensembl request failed: {host}")

def vep_post(ids):
    """Ensembl VEP by rsID (canonical transcripts, HGVS)."""
    req = urllib.request.Request(HOSTS["38"] + "/vep/human/id?canonical=1&hgvs=1",
                                 data=json.dumps({"ids": ids}).encode(),
                                 headers={"Content-Type": "application/json", "Accept": "application/json"},
                                 method="POST")
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("Ensembl VEP request failed")

def annotated_rsids():
    """rsIDs that the carrier catalog and the PGx alleles use (these get gene and HGVS)."""
    ids = set()
    for e in json.load(open(os.path.join(REF, "carrier_catalog.json"), encoding="utf-8")):
        if e.get("rsid") and not e.get("untestable"):
            ids.add(e["rsid"].lower())
    pgx = os.path.join(REF, "pgx_catalog.json")
    if os.path.exists(pgx):
        for e in json.load(open(pgx, encoding="utf-8")):
            ids |= {a["rsid"].lower() for a in e.get("alleles", [])}
    return sorted(ids)

def _short(hgvs, part):
    """Strip the transcript prefix: 'ENST..:c.12A>G' -> 'c.12A>G'; protein part drops 'p.(..)' wrapper."""
    if not hgvs or ":" not in hgvs:
        return None
    h = hgvs.split(":", 1)[1].replace("p.(", "p.").rstrip(")") if part == "p" else hgvs.split(":", 1)[1]
    return h

def annotate(panel):
    """Add 'genes' and 'hgvs' (canonical transcripts) to the panel entries of annotated_rsids()."""
    ids = [i for i in annotated_rsids() if i in panel]
    for i in range(0, len(ids), 200):
        batch = ids[i:i + 200]
        for rec in vep_post(batch):
            rs = rec.get("id", "").lower()
            if rs not in panel:
                continue
            genes, hg = set(), set()
            for tc in rec.get("transcript_consequences", []):
                if tc.get("canonical") != 1:
                    continue
                if tc.get("gene_symbol"):
                    genes.add(tc["gene_symbol"])
                for key, part in (("hgvsp", "p"), ("hgvsc", "c")):
                    h = _short(tc.get(key), part)
                    if h:
                        hg.add(h)
            panel[rs]["genes"] = sorted(genes)
            panel[rs]["hgvs"] = sorted(hg)
    return panel

def primary_mapping(rec):
    """The mapping on a primary chromosome (skip patches / alt haplotypes)."""
    for m in rec.get("mappings", []):
        if m.get("seq_region_name") in CHROMS:
            return m
    return None

def kind_of(allele_string):
    al = allele_string.split("/")
    if all(len(a) == 1 and a in "ACGT" for a in al):
        return "snv"
    return "indel"

def main():
    ids = used_rsids()
    print(f"{len(ids)} rsIDs used by the skill")
    panel, missing = {}, []
    for i in range(0, len(ids), 200):
        batch = ids[i:i + 200]
        res = {b: post(HOSTS[b], batch) for b in ("37", "38")}
        for rs in batch:
            m37 = primary_mapping(res["37"].get(rs, {}))
            m38 = primary_mapping(res["38"].get(rs, {}))
            if not m38 and not m37:
                missing.append(rs)
                continue
            m = m38 or m37
            panel[rs] = {"chrom": m["seq_region_name"],
                         "pos37": m37["start"] if m37 else None,
                         "pos38": m38["start"] if m38 else None,
                         "ref": m["allele_string"].split("/")[0],
                         "alleles": m["allele_string"],
                         "kind": kind_of(m["allele_string"])}
        print(f"  {min(i + 200, len(ids))}/{len(ids)}")
    annotate(panel)
    rcrs = urllib.request.urlopen("https://rest.ensembl.org/sequence/region/human/MT:1..16569:1"
                                  "?content-type=text/plain", timeout=120).read().decode().strip()
    out = {"_note": "rsID -> GRCh37/GRCh38 position + forward-strand REF (Ensembl REST). "
                    "mt_rcrs = rCRS mtDNA sequence (1-based: mt_rcrs[pos-1]). Built by scripts/build_vcf_panel.py.",
           "_built": time.strftime("%Y-%m-%d"),
           "_missing": missing,
           "mt_rcrs": rcrs,
           "rsids": panel}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=0)
    print(f"wrote {OUT}: {len(panel)} rsIDs, {len(missing)} not found, rCRS {len(rcrs)} bp")

if __name__ == "__main__":
    if "--annotate-only" in sys.argv:
        d = json.load(open(OUT, encoding="utf-8"))
        annotate(d["rsids"])
        json.dump(d, open(OUT, "w", encoding="utf-8"), indent=0)
        print("annotated", OUT)
    else:
        main()
