# -*- coding: utf-8 -*-
"""Derive a genetically-grounded APPEARANCE profile (pigmentation, hair, build, sex)
from parsed genotypes, and build an image prompt. Predicts COLORING/BUILD only — NOT
facial structure (highly polygenic, not readable here). Generic for any user."""
def _n(gt): return "".join(sorted(gt)) if gt and gt not in ("--",) else gt

def profile(calls, ancestry=None):
    g = lambda rs: _n(calls[rs]["genotype"]) if rs in calls else None
    male = any(r["chrom"]=="Y" and r["genotype"] not in ("--","") for r in calls.values())

    # Eye colour is polygenic — don't trust rs12913832 alone. rs1667394 TT (and
    # OCA2 modifiers) can turn a heterozygote blue, so integrate them.
    e = g("rs12913832"); mod_blue = g("rs1667394")=="TT" and g("rs1800407")=="CC"
    if e == "AA": eye = "blue"
    elif e == "AG": eye = "blue or light" if mod_blue else "hazel or light-brown"
    elif e == "GG": eye = "brown"
    else: eye = "brown"
    fr  = {"TT":"noticeably freckled","CT":"lightly freckled","CC":"few freckles"}.get(g("rs12203592"), "some freckles")
    light = g("rs1426654")=="AA" and g("rs16891982")=="GG"
    skin = "fair to light-olive" if light else ("light-olive to medium" if g("rs16891982") in ("GG","GT") else "medium to darker")

    # hair colour: red > blonde > dark
    red = "CT" in (g("rs1805007"), g("rs1805008")) or g("rs1805007")=="TT" or g("rs1805008")=="TT"
    blonde = g("rs12821256")=="CC" or g("rs12896399")=="TT"
    hair_color = "auburn / red-tinted" if red else ("blonde to light-brown" if blonde else "dark brown to near-black")
    hair_tex = {"AA":"fine, European-type (straight to wavy)","AG":"medium thickness","GG":"thick, straight"}.get(g("rs3827760"), "straight to wavy")
    build = {"CC":"athletic, power/muscular","CT":"balanced","TT":"lean, endurance-type"}.get(g("rs1815739"), "average")

    anc = None
    if ancestry and ancestry.get("posterior"):
        top = max(ancestry["posterior"], key=ancestry["posterior"].get)
        anc = ancestry["pop_labels"].get(top, top)

    parts = [("an adult man" if male else "an adult woman")]
    if anc: parts.append(f"of {anc} genetic ancestry")
    parts += [f"{skin} skin", fr, f"{eye} eyes",
              f"{hair_color} hair ({hair_tex})",
              (f"{build} build")]
    desc = ", ".join(parts)
    prompt = ("photorealistic studio portrait, head and shoulders, " + desc +
              ", warm soft cinematic light, neutral grey background, calm friendly expression, "
              "generic non-specific face, respectful, high detail")
    return {"sex":"male" if male else "female","eye":eye,"skin":skin,"freckles":fr,
            "hair_color":hair_color,"hair_texture":hair_tex,"build":build,"ancestry":anc,
            "description":desc,"prompt":prompt,
            "caveat":"Predicts coloring & build only — NOT facial structure. An artistic impression, not a real likeness."}
