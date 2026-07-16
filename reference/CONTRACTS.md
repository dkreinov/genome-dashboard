# Frozen Contracts (Phase 1)

## Parsed genotype (scripts/parse_input.py :: parse)
`{ rsid: { "chrom": <"1".."22"|"X"|"Y"|"MT">, "pos": int, "genotype": <str> } }`
- genotype: PLUS strand, UPPERCASE, alleles SORTED (AG==GA); "--" = no-call;
  indel tokens I/D preserved & sorted. Haploid Y/MT may be 1 char.

## Reference filenames (reference/)
haplogroup_snps.json · allele_freqs.json · gwas_weights_raw.json ·
prs_weights.json · pgx_catalog.json · carrier_catalog.json · mt_phylotree.json ·
disclaimers.json

## PRS weights (reference/prs_weights.json)
`{ trait: [ { "rsid","risk_allele","beta","locus_group","source_url" } ] }`
- one entry per independent locus_group (LD-pruned); palindromic SNPs aligned to
  the allele_freqs reference set at scoring time.

## Engine result JSON (results/*.json) — finalized in Phase 2.
