# 🧬 Genome Dashboard (Claude Code Skill)

Turn a personal raw DNA file into a single **offline, self-contained HTML dashboard** —
traits, health, pharmacogenomics, athletic, nutrition, longevity, ancestry (Y & mtDNA
haplogroups + continental composition + runs of homozygosity), a Neanderthal estimate,
polygenic risk scores, and an ancestry carrier screen.

## Quick start
```
python run.py --input your_raw_dna.txt --out dashboard.html
```
Open `dashboard.html` in any browser. **Fully offline. Your DNA never leaves the machine.**

- `--input`  23andMe (v3/v4/v5) or AncestryDNA raw file (format auto-detected)
- `--out`    output path (default dashboard.html)
- `--lang ru,es`  add languages (needs `LLM_API_KEY`; a live switch appears in the report)
- `--images`      decorative hero art (needs `IMAGE_API_KEY`; generic prompts only, never your DNA)
- `--env path`    a .env file holding optional API keys

No API keys ⇒ English-only, image-free, fully offline (graceful degradation).

## ⚠️ Not medical advice
Educational only. Consumer chips test a small subset of positions and can err. A genotype is
a tendency, not a diagnosis. **Confirm anything actionable — especially BRCA / carrier status /
pharmacogenomics — with an accredited lab and a clinician or genetic counselor.**

## How it works / stays generic
`run.py` → `scripts/run_analysis.py` runs 8 engines over the parsed genotypes + **bundled,
frozen reference data** (`reference/*.json`: SNPedia haplogroup DB, 1000G frequencies, GWAS
Catalog PRS weights, CPIC/carrier catalogs, mtDNA PhyloTree). No personal data is bundled; the
SNP catalog is keyed by genotype so it works for anyone. Refresh reference data with
`python scripts/refresh_reference.py` (opt-in, online).

## Data sources
SNPedia · Ensembl/1000 Genomes · GWAS Catalog · CPIC/PharmGKB · MITOMAP/PhyloTree · MedlinePlus.
See `reference/MANIFEST.md`.

## Getting more markers (imputation vs sequencing)

A genotyping chip reads a fixed subset of positions. Two ways to expand it:

- **Imputation (free).** Servers like the TOPMed or Michigan Imputation Server statistically
  infer tens of millions of extra SNPs from your existing file using reference panels — no new
  sample needed. Good for pulling in more common trait/GWAS markers you didn't get measured.
- **Whole-genome sequencing (~$200–600).** Reads all ~3 billion bases directly: every known
  variant, rare variants arrays skip, and things arrays genuinely can't resolve — e.g. **CYP2D6
  copy number** (why codeine/tamoxifen may be "undetermined") and **full BRCA / carrier-gene
  sequencing** (not just the founder SNPs).

**Note on facial prediction:** neither meaningfully improves it. Facial structure is hugely
polygenic and heavily environmental (age, weight), so even a full genome yields only coarse,
population-level tendencies — not a face. The real payoff of sequencing is **clinical
completeness**, not portraits.

## Example output

`examples/example_dashboard.html` is a complete dashboard rendered from
`examples/mock_person.txt` — **fully synthetic, fabricated genotypes, not a real person**.
Open it in a browser to see what the report looks like. Regenerate with:
`python scripts/make_mock.py && python run.py --input examples/mock_person.txt --out examples/example_dashboard.html`
