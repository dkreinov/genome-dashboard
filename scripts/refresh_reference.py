# -*- coding: utf-8 -*-
"""Opt-in: re-pull the frozen reference datasets from their live sources.
Network + time heavy. Not run at dashboard-generate time. Import-safe."""
import json, os
REF = os.path.join(os.path.dirname(__file__), "..", "reference")

def refresh_allele_freqs(rsids):
    """Pull 1000G EUR/EAS/AFR/SAS/AMR freqs from Ensembl for rsids (stub kept
    minimal; see project history for the full fetch loop)."""
    raise NotImplementedError("Run online; see scripts/README for the fetch loop.")

def refresh_gwas_weights(rsids):
    raise NotImplementedError("Run online; EBI GWAS Catalog associationBySnp.")

def refresh_haplogroup_snps():
    raise NotImplementedError("Run online; SNPedia embeddedin Template:Hgsnp.")

if __name__ == "__main__":
    print("Reference refresh is opt-in and online. Edit this script to enable.")
