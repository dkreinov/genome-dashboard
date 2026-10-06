# Reference Data Manifest

Frozen snapshot bundled so the skill runs offline & reproducibly.
Re-pull with `python scripts/refresh_reference.py` (opt-in, needs network).

| file | source | pulled | notes / licence |
|------|--------|--------|-----------------|
| haplogroup_snps.json | SNPedia (bots.snpedia.com API, Template:Hgsnp) | 2026-07 | Y/mtDNA haplogroup-defining SNPs. SNPedia text CC-BY-SA-NC. |
| allele_freqs.json | Ensembl REST / 1000 Genomes phase 3 | 2026-07 | per-SNP superpopulation allele freqs (EUR/EAS/AFR/SAS/AMR). |
| gwas_weights_raw.json | EBI GWAS Catalog REST | 2026-07 | reported risk allele + odds ratios per SNP/trait. |
| prs_weights.json | derived (Step 5) from gwas_weights_raw + curated | 2026-07 | vetted, LD-pruned, palindrome-safe scoring weights. |
| vcf_panel.json | Ensembl REST (GRCh38 + GRCh37 /variation, MT rCRS sequence) | 2026-10 | rsID → GRCh37/38 position + REF allele for the VCF reader; rebuild with `scripts/build_vcf_panel.py`. 6 retired Y rsIDs not found. |

Data are used for educational interpretation only. Not clinical-grade.
