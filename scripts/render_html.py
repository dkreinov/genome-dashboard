# -*- coding: utf-8 -*-
"""Render results/analysis.json -> one self-contained, offline HTML dashboard.
English by default; translatable text carries data-en so translate.py can add
data-<lang> and the built-in switch can swap languages. Images (optional) are
injected as base64 by gen_images.py before render (passed via `images`)."""
import html, json, os

ICONS = {
 "heart":'<path d="M12 20C7 16 3 12.5 3 8.8 3 6.4 4.9 5 7 5c1.6 0 2.9.9 3.5 2C11.1 5.9 12.4 5 14 5c2.1 0 4 1.4 4 3.8 0 3.7-4 7.2-6 9.2z"/>',
 "drop":'<path d="M12 3c3 4 5 6.7 5 9.5A5 5 0 0 1 7 12.5C7 9.7 9 7 12 3z"/>',
 "sun":'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.4 1.4M17.6 17.6L19 19M19 5l-1.4 1.4M6.4 17.6L5 19"/>',
 "moon":'<path d="M20 13A8 8 0 1 1 11 4a6.5 6.5 0 0 0 9 9z"/>',
 "pill":'<rect x="2.5" y="9" width="19" height="6" rx="3"/><path d="M12 9v6"/>',
 "eye":'<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z"/><circle cx="12" cy="12" r="2.5"/>',
 "bolt":'<path d="M13 2L5 13h5l-1 9 8-11h-5l1-9z"/>',
 "leaf":'<path d="M4 20C4 11 9 5 20 5c0 11-6 15-16 15z"/><path d="M5 19C9 15 12 13 18 10"/>',
 "dna":'<path d="M8 3c0 4 8 5 8 9s-8 5-8 9"/><path d="M16 3c0 4-8 5-8 9s8 5 8 9"/><path d="M9.5 6h5M9.5 18h5"/>',
 "shield":'<path d="M12 3l7 3v5c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6z"/>',
 "muscle":'<path d="M4 14c2-1 4-1 5 0 2 2 1 5 4 5 4 0 7-3 7-8 0-3-2-5-5-5H8L4 9z"/>',
 "clock":'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 "sparkle":'<path d="M12 3l1.7 6.3L20 11l-6.3 1.7L12 19l-1.7-6.3L4 11l6.3-1.7z"/>',
 "flame":'<path d="M12 3c1 4 5 5 5 9a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 3 3-1-3 0-6 0-8z"/>',
 "virus":'<circle cx="12" cy="12" r="5.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5.2 5.2l2 2M16.8 16.8l2 2M18.8 5.2l-2 2M5.2 18.8l2-2"/>',
}
_MAP=[("caffeine","leaf"),("coffee","leaf"),("jitter","bolt"),("lactose","drop"),("earwax","drop"),
 ("alcohol","drop"),("muscle","muscle"),("sprint","muscle"),("empathy","heart"),("memory","clock"),
 ("worrier","clock"),("eye","eye"),("macular","eye"),("freckl","sun"),("skin","sun"),("pigment","sun"),
 ("vitamin d","sun"),("cilantro","leaf"),("sleep","moon"),("clock","moon"),("lung","dna"),("blood type","drop"),
 ("norovirus","virus"),("secretor","virus"),("hepatitis","virus"),("sweet","sparkle"),("pain","flame"),
 ("clopidogrel","pill"),("warfarin","pill"),("statin","pill"),("cyp","pill"),("diabetes","drop"),
 ("parkinson","dna"),("iron","shield"),("gout","flame"),("nicotine","flame"),("longevity","clock"),
 ("cholesterol","heart"),("heart","heart"),("alzheimer","clock"),("salt","drop"),("aerobic","dna"),
 ("power vs endurance","bolt"),("tendon","muscle"),("klotho","clock"),("telomere","dna"),("height","sparkle"),
 ("inflammation","flame"),("antioxidant","leaf"),("appetite","flame"),("smell","virus"),("violet","leaf")]
# Single source of truth for categories: (name, section order, fallback icon).
# To add a category, add ONE line here — SEV_ORDER and CATICON both derive from it.
CATEGORIES=[("Health","heart"),("Pharmacogenomics","pill"),("Athletic","muscle"),
            ("Nutrition","leaf"),("Longevity","clock"),("Facial","eye"),("Traits","sparkle")]
SEV_ORDER=[c for c,_ in CATEGORIES]
CATICON=dict(CATEGORIES)
PGXC={"avoid":"#d0454b","caution":"#d98016","adjust":"#7c4dff","standard":"#5b6bd6","reassuring":"#1f9d5c"}
POPCOL={"European":"#1f9d5c","East Asian":"#d98016","African":"#7c4dff","South Asian":"#5b6bd6","Amerindian/Admixed":"#6b7280"}

esc=lambda s: html.escape(str(s), quote=True)
def T(s):  # translatable inline text
    return f'<span data-en="{esc(s)}">{esc(s)}</span>'
def icon(cat,title,gene):
    t=(str(title)+" "+str(gene)).lower(); name=None
    for k,ic in _MAP:
        if k in t: name=ic; break
    name=name or CATICON.get(cat,"sparkle")
    return f'<svg class="isvg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'

def _card(m):
    return (f'<div class="card sev-{m["sev"]}"><div class="card-top"><span class="ico">{icon(m["cat"],m["title"],m["gene"])}</span>'
            f'<span class="gene">{esc(m["gene"])}</span><span class="gt">{esc(m["gt"])}</span></div>'
            f'<div class="title">{esc(m["title"])}</div>'
            f'<div class="label">{T(m["label"])}</div><div class="text">{T(m["text"])}</div>'
            f'<div class="rsid">{esc(m["rsid"])}</div></div>')

def _prs_gauge(s, disc):
    pct=s["pct"]; col="#1f9d5c" if pct<40 else ("#d98016" if pct<75 else "#d0454b")
    return (f'<div class="prscard"><div class="prstop"><div class="prsname">{T(s["trait"])}</div>'
            f'<div class="prsbig" style="color:{col}">{pct}<span class="prsth">th</span></div></div>'
            f'<div class="prsmeta">percentile · {s["rr"]}× vs average · {s["used"]} loci</div>'
            f'<div class="gauge"><div class="gtrack"></div><div class="gmark" style="inset-inline-start:{pct}%;background:{col}"></div><div class="gavg"></div></div>'
            f'<div class="gaxis"><span>0</span><span>avg</span><span>100</span></div>'
            f'<details class="method"><summary>Source &amp; method</summary><div class="mbody">{T(disc["prs"])} '
            f'<a href="{esc(s.get("source_url","https://www.ebi.ac.uk/gwas/"))}" target="_blank" rel="noopener">GWAS Catalog ↗</a></div></details></div>')

def render(analysis, out_path, disclaimers, images=None):
    images = images or {}
    A=analysis
    # ---- stats ----
    y=A["haplo_y"].get("call") or "—"; mt=A["haplo_mt"].get("call") or "—"
    sev_counts={}
    for m in A["catalog"]["markers"]: sev_counts[m["sev"]]=sev_counts.get(m["sev"],0)+1
    blood=next((m["label"] for m in A["catalog"]["markers"] if m["gene"]=="ABO"), "—")
    stats=[(f'{A["meta"]["n_parsed"]:,}',"SNPs in file"),(A["catalog"]["n"],"Markers read"),
           (mt,"Maternal line"),(y,"Paternal line"),
           (f'{A["neanderthal"]["nean_markers"]}/{A["neanderthal"]["tested"]}',"Neanderthal markers"),
           (sev_counts.get("good",0),"Reassuring")]
    stat_html="".join(f'<div class="stat"><div class="n">{esc(n)}</div><div class="k">{T(k)}</div></div>' for n,k in stats)
    # ---- ancestry ----
    anc=A["ancestry"]; comp=""
    if anc.get("posterior"):
        for p in sorted(anc["posterior"], key=anc["posterior"].get, reverse=True):
            lbl=anc["pop_labels"][p]; pctv=100*anc["posterior"][p]
            comp+=(f'<div class="brow"><span class="bl" style="width:150px;text-align:start">{esc(lbl)}</span>'
                   f'<div class="btrack" style="height:14px"><div class="bfill" style="width:{max(pctv,0.6):.1f}%;background:{POPCOL.get(lbl,"#5b6bd6")}"></div></div>'
                   f'<span class="bv">{pctv:.1f}%</span></div>')
    ychain=" → ".join(A["haplo_y"].get("chain",[]) or [y])
    mtm=", ".join(A["haplo_mt"].get("matched_mutations",[]) or [])
    anc_html=(f'<div class="anc"><div class="apanel"><div class="atag">Paternal · Y-DNA</div>'
              f'<div class="atitle">Haplogroup {esc(y)}</div><div class="atext">{T("Direct paternal line. Backbone: ")}{esc(ychain)}. '
              f'{T("A best-estimate from chip markers; confirm the exact terminal clade with a dedicated Y tool.")}</div></div>'
              f'<div class="apanel"><div class="atag">Maternal · mtDNA</div>'
              f'<div class="atitle">Haplogroup {esc(mt)}</div><div class="atext">{T("Direct maternal line. Diagnostic mutations: ")}{esc(mtm)}. '
              f'{T(disclaimers["ancestry"])}</div></div></div>'
              f'<div class="viz"><h3>🧭 {T("Continental ancestry (closest 1000G populations)")}</h3>{comp}'
              f'<p class="blurb">{T(anc.get("prose") or "")}</p></div>'
              f'<div class="anc"><div class="apanel"><div class="atag">🦴 {T("Neanderthal")}</div>'
              f'<div class="atext">{T("You carry the Neanderthal allele at "+str(A["neanderthal"]["nean_markers"])+" of "+str(A["neanderthal"]["tested"])+" tested markers (European average 5–10). "+disclaimers["neanderthal"])}</div></div>'
              f'<div class="apanel"><div class="atag">🧬 {T("Endogamy (runs of homozygosity)")}</div>'
              f'<div class="atext">{T(str(anc["roh_total_mb"])+" Mb in long homozygous runs, "+str(anc["roh_big"])+" segment(s) over 5 Mb. Elevated values suggest ancestry from a small/intermarrying community.")}</div></div></div>')
    # ---- appearance / DNA portrait ----
    appearance=""
    ap=A.get("appearance")
    if ap:
        gallery="".join(f'<figure class="genimg"><img src="{images[k]}" alt=""></figure>'
                        for k in sorted(images) if k.startswith("portrait_"))
        if gallery: gallery=f'<div class="pgallery">{gallery}</div>'
        appearance=(f'<h2 class="sec">🎨 {T("How your DNA suggests you might look")}</h2>'
                    f'<div class="viz"><div class="atext">{T(ap["description"].capitalize()+".")}</div>'
                    f'<p class="blurb">⚠ {T(ap["caveat"])}</p>{gallery}</div>')
    # ---- PRS ----
    prs_html="".join(_prs_gauge(s, disclaimers) for s in A["prs"]["scores"])
    # ---- carrier ----
    carrier_html=""
    if A["carrier"]["variants"]:
        cc=""
        for v in A["carrier"]["variants"]:
            col=PGXC.get(v["category"],"#5b6bd6")
            cc+=(f'<div class="pgxcard" style="border-inline-start-color:{col}"><div class="pgxtop">'
                 f'<span class="pgxdrug">{esc(v["disease"])}</span><span class="pgxpill" style="background:{col}">{T(v["result"])}</span></div>'
                 f'<div class="pgxgene">{esc(v["gene"])} · {esc(v["variant"])} · {esc(v["gt"])}</div>'
                 f'<div class="text">{T(v["text"])}</div>'
                 f'<a class="pgxsrc" href="{esc(v["source"])}" target="_blank" rel="noopener">MedlinePlus ↗</a></div>')
        carrier_html=(f'<h2 class="sec">🧬 {T("Carrier screen (founder variants)")}</h2>'
                      f'<div class="pgxgrid">{cc}</div>'
                      f'<div class="warnbox"><div class="warnh">⚠ {T("Important — what this does NOT tell you")}</div>'
                      f'<div class="warntext">{T(disclaimers["carrier"])}</div></div>')
    # ---- pgx ----
    pgx_html=""
    if A["pgx"]["drugs"]:
        pc=""
        for d in A["pgx"]["drugs"]:
            col=PGXC.get(d["category"],"#5b6bd6")
            pc+=(f'<div class="pgxcard" style="border-inline-start-color:{col}"><div class="pgxtop">'
                 f'<span class="pgxdrug">{esc(d["drug"])}</span><span class="pgxpill" style="background:{col}">{T(d["category"])}</span></div>'
                 f'<div class="pgxgene">{esc(d["gene"])} · {esc(d["gt"])} · {esc(d["phenotype"])}</div>'
                 f'<div class="text">{T(d["text"])}</div>'
                 f'<a class="pgxsrc" href="{esc(d["source"])}" target="_blank" rel="noopener">CPIC ↗</a></div>')
        pgx_html=(f'<h2 class="sec">💊 {T("Medications (pharmacogenomics)")}</h2>'
                  f'<p class="blurb">{T(disclaimers["pgx"])}</p><div class="pgxgrid">{pc}</div>')
    # ---- catalog sections + filter ----
    sections=""
    for c in SEV_ORDER:
        items=[m for m in A["catalog"]["markers"] if m["cat"]==c]
        if not items: continue
        sections+=(f'<section class="catsec"><h2 class="sec">{T(c)}<span class="cnt">{len(items)}</span></h2>'
                   f'<div class="grid">'+"".join(_card(m) for m in items)+"</div></section>")
    filterbar=('<div class="filters"><span class="fl">'+T("Filter:")+'</span>'
        +'<button class="fbtn on" data-sev="all" onclick="filterSev(\'all\')">'+T("All")+'</button>'
        +''.join(f'<button class="fbtn" data-sev="{s}" onclick="filterSev(\'{s}\')"><span class="fdot" style="background:{col}"></span>{T(lbl)}</button>'
                 for s,col,lbl in [("good","#1f9d5c","Reassuring"),("watch","#d98016","Attention"),("note","#6b7280","Carrier/minor"),("info","#5b6bd6","Neutral")])
        +'</div>')
    hero=f'<div class="hero"><img src="{images["hero"]}" alt=""></div>' if images.get("hero") else ""
    return _PAGE.format(stats=stat_html, anc=anc_html, appearance=appearance, prs=prs_html, carrier=carrier_html,
                        pgx=pgx_html, filterbar=filterbar, sections=sections, hero=hero,
                        disc=T(disclaimers["global"]), lang_switch=_LANG_SWITCH)

# minimal langs the switch offers if translations exist (populated dynamically by JS)
_LANG_SWITCH = '<button class="theme" onclick="cycleLang()" id="langbtn">🌐 EN</button>'

_PAGE = """<!doctype html><html lang="en" dir="ltr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Genome Dashboard</title>
<style>
:root{{--bg:#f6f7f9;--panel:#fff;--ink:#12151c;--mut:#5b6472;--line:#e6e8ec;--good:#1f9d5c;--info:#5b6bd6;--watch:#d98016;--note:#6b7280;--acc:#7c4dff}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0d0f14;--panel:#161a22;--ink:#eef1f6;--mut:#9aa4b2;--line:#242a35}}}}
:root[data-theme=dark]{{--bg:#0d0f14;--panel:#161a22;--ink:#eef1f6;--mut:#9aa4b2;--line:#242a35}}
:root[data-theme=light]{{--bg:#f6f7f9;--panel:#fff;--ink:#12151c;--mut:#5b6472;--line:#e6e8ec}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,Segoe UI,Roboto,Arial,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:28px 20px 80px}}
header{{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}}
h1{{font-size:24px;margin:0;letter-spacing:-.02em}}.controls{{display:flex;gap:8px}}
.theme{{background:var(--panel);border:1px solid var(--line);color:var(--ink);border-radius:9px;padding:7px 12px;cursor:pointer;font-size:13px}}
.pgallery{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-top:12px}}.pgallery img{{width:100%;border-radius:12px;display:block}}
.hero{{margin:16px 0 4px;border-radius:16px;overflow:hidden;border:1px solid var(--line)}}.hero img{{width:100%;height:auto;display:block}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:20px 0 6px}}
.stat{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 15px}}.stat .n{{font-size:22px;font-weight:700}}.stat .k{{color:var(--mut);font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;margin-top:2px}}
.sec{{font-size:19px;margin:32px 0 10px;display:flex;align-items:center;gap:10px}}.sec .cnt{{font-size:12px;color:var(--mut);background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:2px 9px}}
.blurb{{color:var(--mut);font-size:13.5px;margin:0 0 14px}}
.grid,.pgxgrid,.prsgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
.card,.pgxcard,.prscard,.apanel,.viz{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px 16px}}
.card{{position:relative;overflow:hidden}}.card::before{{content:"";position:absolute;inset-inline-start:0;top:0;bottom:0;width:4px}}
.sev-good::before{{background:var(--good)}}.sev-info::before{{background:var(--info)}}.sev-watch::before{{background:var(--watch)}}.sev-note::before{{background:var(--note)}}
.card-top{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}.ico{{display:inline-flex;width:26px;height:26px;align-items:center;justify-content:center;border-radius:8px;background:var(--bg);border:1px solid var(--line)}}.isvg{{width:16px;height:16px}}
.sev-good .ico{{color:var(--good)}}.sev-watch .ico{{color:var(--watch)}}.sev-note .ico{{color:var(--note)}}.sev-info .ico{{color:var(--info)}}
.gene{{font-weight:650;font-size:13px}}.gt{{margin-inline-start:auto;font-family:ui-monospace,Consolas,monospace;font-size:12px;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:1px 7px;color:var(--mut)}}
.title{{font-size:13px;color:var(--mut);margin-bottom:4px}}.label{{font-size:16px;font-weight:600;margin-bottom:5px}}.text{{font-size:13.5px;opacity:.9}}.rsid{{font-family:ui-monospace,monospace;font-size:11px;color:var(--mut);margin-top:9px;opacity:.7}}
.anc{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:6px}}@media(max-width:760px){{.anc{{grid-template-columns:1fr}}}}
.apanel{{position:relative;overflow:hidden;border-inline-start:4px solid var(--acc)}}.atag{{font-size:12px;color:var(--acc);font-weight:700;text-transform:uppercase;letter-spacing:.05em}}.atitle{{font-size:18px;font-weight:750;margin:4px 0 8px}}.atext{{font-size:13.5px;opacity:.9}}
.viz{{margin-top:14px}}.viz h3{{margin:0 0 10px;font-size:15px}}
.brow{{display:flex;align-items:center;gap:10px;margin-bottom:6px;font-size:12px}}.btrack{{flex:1;background:var(--bg);border-radius:5px;height:9px;overflow:hidden}}.bfill{{height:100%;border-radius:5px}}.bv{{width:64px;text-align:end;color:var(--mut);font-family:ui-monospace,monospace}}.bl{{color:var(--mut)}}
.prscard .prstop{{display:flex;justify-content:space-between;align-items:baseline;gap:10px}}.prsname{{font-size:16px;font-weight:700}}.prsbig{{font-size:34px;font-weight:800;line-height:1}}.prsth{{font-size:15px;font-weight:600}}.prsmeta{{font-size:12px;color:var(--mut);margin:4px 0 14px}}
.gauge{{position:relative;height:12px;margin:6px 0 4px}}.gtrack{{position:absolute;inset:0;border-radius:6px;background:linear-gradient(90deg,#1f9d5c,#d9c516,#d0454b)}}.gmark{{position:absolute;top:-4px;width:6px;height:20px;border-radius:3px;box-shadow:0 0 0 2px var(--panel);transform:translateX(-50%)}}.gavg{{position:absolute;inset-inline-start:50%;top:-3px;width:2px;height:18px;background:var(--ink);opacity:.35}}.gaxis{{display:flex;justify-content:space-between;font-size:10.5px;color:var(--mut);margin-top:2px}}
.method{{margin-top:12px;font-size:12px}}.method summary{{cursor:pointer;color:var(--acc);font-weight:600}}.mbody{{margin-top:8px;color:var(--mut);border-top:1px dashed var(--line);padding-top:8px}}.mbody a,.pgxsrc{{color:var(--acc);font-weight:600;text-decoration:none}}
.pgxcard{{border-inline-start-width:4px}}.pgxtop{{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:3px}}.pgxdrug{{font-size:16px;font-weight:700}}.pgxpill{{color:#fff;font-size:10.5px;font-weight:700;text-transform:uppercase;padding:3px 8px;border-radius:20px}}.pgxgene{{font-size:12px;color:var(--mut);font-family:ui-monospace,monospace;margin-bottom:7px}}.pgxsrc{{display:inline-block;margin-top:9px;font-size:11.5px}}
.warnbox{{margin-top:16px;background:var(--panel);border:1px solid var(--line);border-inline-start:4px solid var(--watch);border-radius:12px;padding:16px 18px}}.warnh{{font-weight:700;font-size:14px;color:var(--watch);margin-bottom:8px}}.warntext{{font-size:13px;opacity:.9;line-height:1.6}}
.filters{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0 18px;position:sticky;top:0;background:var(--bg);padding:10px 0;z-index:5}}.fl{{font-size:12.5px;color:var(--mut)}}.fbtn{{display:inline-flex;align-items:center;gap:6px;background:var(--panel);border:1px solid var(--line);color:var(--ink);border-radius:20px;padding:6px 13px;font-size:13px;cursor:pointer}}.fbtn.on{{background:var(--acc);color:#fff;border-color:var(--acc)}}.fdot{{width:9px;height:9px;border-radius:50%}}
.disc{{margin-top:32px;font-size:12.5px;color:var(--mut);background:var(--panel);border:1px solid var(--line);border-inline-start:4px solid var(--watch);border-radius:10px;padding:14px 16px}}
@media print{{:root{{--bg:#fff;--panel:#fff;--ink:#111;--mut:#555;--line:#ccc}}.controls,.filters{{display:none!important}}.card,.pgxcard,.prscard,.apanel{{break-inside:avoid}}.method{{display:none}}}}
</style></head><body><div class="wrap">
<header><div><h1>🧬 {T_title}</h1><div class="blurb">100% local · nothing uploaded</div></div>
<div class="controls">{lang_switch}<button class="theme" onclick="window.print()">⬇ PDF</button>
<button class="theme" onclick="var r=document.documentElement;r.dataset.theme=r.dataset.theme==='dark'?'light':'dark'">◐</button></div></header>
{hero}
<div class="stats">{stats}</div>
<h2 class="sec">🌍 {T_anc}</h2>{anc}
{appearance}
<h2 class="sec">📊 {T_prs}</h2><div class="prsgrid">{prs}</div>
{carrier}
{pgx}
{filterbar}
{sections}
<div class="disc">{disc}</div>
</div>
<script>
var LANGS=["en"];
document.querySelectorAll('[data-en]').forEach(function(e){{
  Object.keys(e.dataset).forEach(function(k){{ if(k!=='en' && LANGS.indexOf(k)<0) LANGS.push(k); }});
}});
var li=0;
function cycleLang(){{
  li=(li+1)%LANGS.length; var l=LANGS[li];
  document.documentElement.lang=l; document.documentElement.dir=(l==='he'||l==='ar')?'rtl':'ltr';
  document.querySelectorAll('[data-en]').forEach(function(e){{var v=e.getAttribute('data-'+l);if(v!==null)e.textContent=v;}});
  document.getElementById('langbtn').textContent='🌐 '+l.toUpperCase();
}}
function filterSev(s){{
  document.querySelectorAll('.fbtn').forEach(function(b){{b.classList.toggle('on',b.getAttribute('data-sev')===s);}});
  document.querySelectorAll('.catsec').forEach(function(sec){{var v=0;sec.querySelectorAll('.card').forEach(function(c){{var sh=s==='all'||c.classList.contains('sev-'+s);c.style.display=sh?'':'none';if(sh)v++;}});sec.style.display=v?'':'none';}});
}}
</script></body></html>"""
# fill fixed English section titles
_PAGE = _PAGE.replace("{T_title}", T("Genome Dashboard")).replace("{T_anc}", T("Ancestry")).replace("{T_prs}", T("Polygenic risk scores"))
