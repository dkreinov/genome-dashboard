---
name: genome-dashboard
description: >-
  Turn a personal raw DNA file (23andMe v3/v4/v5, AncestryDNA best-effort, or a
  whole-genome/exome VCF or gVCF in GRCh37/GRCh38) into a single self-contained,
  offline HTML dashboard: traits, health,
  pharmacogenomics, athletic, nutrition, longevity, ancestry (Y & mtDNA
  haplogroups), Neanderthal estimate, polygenic risk scores, and an
  ancestry-specific carrier screen. English by default; any language optional
  via generate-time LLM translation. Privacy-first — the DNA file never leaves
  the machine. Use when a user wants to interpret their own consumer-genotyping
  raw data and get a shareable, cited report.
---

# Genome Dashboard

## ⚠️ Non-negotiable framing (read first, applies in every language)

- **This is educational, NOT medical advice** and NOT a diagnosis. A genotype is
  a tendency shaped by lifestyle, environment, and thousands of untested genes.
- **Privacy-first.** The raw DNA file is read locally and never uploaded. Only
  generic art prompts (never genotype data) are ever sent to the optional image API.
- **Consumer chips are not clinical-grade.** They test a small, specific subset of
  positions and can err. Anything actionable — especially **BRCA / carrier status /
  pharmacogenomics** — must be confirmed by an accredited lab and a clinician /
  genetic counselor. A "clear" result never rules out untested variants.
- These caveats are rendered on the relevant panels and must survive translation.

## What it produces

One offline `dashboard.html` (self-contained: inline CSS/SVG, embedded images) with:
Traits · Health · Pharmacogenomics (CPIC) · Athletic · Nutrition · Longevity ·
Ancestry (generic Y + mtDNA haplogroup callers, continental composition, runs of
homozygosity) · Neanderthal estimate · Polygenic risk scores (frozen GWAS-Catalog
weights) · Ashkenazi founder carrier screen with residual risk; CPIC gene-level calls for CYP2C19, TPMT/NUDT15 and DPYD · good/bad filters · PDF button · optional
language switch.

## Usage

```
python run.py --input <raw_dna.txt> [--out dashboard.html] [--lang ru,es,...] [--images]
```

- `--input`  path to the user's raw file (required). Format auto-detected:
             23andMe / AncestryDNA text, or VCF/gVCF (`.vcf`, `.vcf.gz`; build
             GRCh37/GRCh38 read from the header). For a VCF, panel sites absent from
             a plain VCF are read as homozygous reference (see README "Using a
             whole-genome VCF"). Needs `reference/vcf_panel.json` (bundled).
- `--out`    output HTML path (default `dashboard.html`).
- `--lang`   comma-separated target languages; each is filled by an LLM at
             generate-time. Omitted ⇒ English only. Needs `LLM_API_KEY`.
- `--images` generate a hero image and four section banners (carrier, medications, health, ancestry). Needs `IMAGE_API_KEY`. Set `IMAGE_PROVIDER=openai` for GPT images; the default is DashScope. Omitted/absent ⇒ skipped.
- `scripts/verify_probes.py RAW_FILE` checks the catalog probe IDs and positions against a raw file. It prints no genotypes.
- The medications panel shows a grey "Not tested on this chip" card for CYP2D6, because the chip cannot call it.

No API keys ⇒ runs fully offline in English with no images (graceful degradation).

## How it stays generic

- No personal data is bundled. The SNP catalog is keyed by *genotype* (per-allele
  interpretation), so it works for anyone.
- Reference data (haplogroup SNP DB, allele frequencies, PRS weights) is **frozen
  and bundled** under `reference/` — runs offline and reproducibly. `scripts/refresh_reference.py`
  re-pulls it on demand (opt-in, online).

## Layout

```
SKILL.md              this file
run.py                orchestrator CLI (Phase 3)
scripts/              parse_input, config, engines, render, translate, gen_images, safety
reference/            frozen datasets + catalogs + disclaimers + MANIFEST
templates/            HTML/CSS template fragments
samples/              scrubbed/synthetic sample inputs (never a real full genome)
results/              per-run intermediate JSON (git-ignored)
```

## Data sources (all open)

SNPedia (haplogroups, Neanderthal panel) · Ensembl / 1000 Genomes (allele
frequencies, ancestry) · GWAS Catalog (polygenic risk weights) · CPIC / PharmGKB
(pharmacogenomics) · MITOMAP / PhyloTree (mtDNA). Each score links to its source
in the report.
