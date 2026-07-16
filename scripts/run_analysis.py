# -*- coding: utf-8 -*-
"""Orchestrator: parse a raw DNA file, run all engines, write results/analysis.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import parse_input, engine_catalog, engine_neanderthal, engine_haplo_y, engine_haplo_mt
import engine_ancestry, engine_prs, engine_pgx, engine_carrier, engine_appearance

def analyze(path):
    calls, meta = parse_input.parse_with_meta(path)
    res = {
        "meta": meta,
        "catalog": engine_catalog.run(calls),
        "haplo_y": engine_haplo_y.run(calls),
        "haplo_mt": engine_haplo_mt.run(calls),
        "ancestry": engine_ancestry.run(calls),
        "neanderthal": engine_neanderthal.run(calls),
        "prs": engine_prs.run(calls),
        "pgx": engine_pgx.run(calls),
        "carrier": engine_carrier.run(calls),
        "appearance": None,  # filled below (needs ancestry)
    }
    res["appearance"] = engine_appearance.profile(calls, res["ancestry"])
    return res

if __name__ == "__main__":
    path = sys.argv[1]
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)
    res = analyze(path)
    json.dump(res, open(os.path.join(out_dir,"analysis.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("catalog:", res["catalog"]["n"], "| Y:", res["haplo_y"].get("call"),
          "| mt:", res["haplo_mt"].get("call"),
          "| ancestry top:", (max(res["ancestry"]["posterior"], key=res["ancestry"]["posterior"].get) if res["ancestry"]["posterior"] else None),
          "| PRS:", len(res["prs"]["scores"]), "| pgx:", len(res["pgx"]["drugs"]),
          "| carrier:", len(res["carrier"]["variants"]))
    print("wrote results/analysis.json")
