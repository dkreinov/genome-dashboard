# -*- coding: utf-8 -*-
"""Optional hero and section art. Supports DashScope (async API) and OpenAI (GPT image). Generic prompts only —
NEVER genotype data. No-op unless IMAGE_API_KEY set."""
import json, time, base64, urllib.request

SECTION_PROMPTS = {
    "hero": "An elegant glowing DNA double helix woven from blue, teal and violet light on a dark navy background, minimal premium editorial banner",
    "sec-carrier": "Abstract editorial illustration of two intertwined family-tree branches made of soft light, with small glowing nodes, calm teal and warm amber palette, dark background, no text",
    "sec-meds": "Minimal editorial illustration of medicine capsules and a molecular ring structure floating in soft light, violet and teal palette, dark background, no text",
    "sec-health": "Abstract editorial illustration of a human silhouette made of flowing light lines with a calm heartbeat line, deep blue and coral palette, dark background, no text",
    "sec-ancestry": "Artistic glowing map of ancient human migration routes across a dark globe, luminous golden and blue lines, minimal editorial art, no text",
}

def _openai(cfg, prompt, size="1536x1024"):
    body = {"model": cfg.img_model, "prompt": prompt, "size": size, "n": 1,
            "output_format": "jpeg", "output_compression": 70}   # keeps the HTML small
    req = urllib.request.Request((cfg.img_endpoint or "https://api.openai.com") + "/v1/images/generations",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + cfg.img_key, "Content-Type": "application/json"})
    delays = [5, 15, 45]   # backoff in seconds; one retry per entry
    for attempt in range(len(delays) + 1):
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=180).read())
            return "data:image/jpeg;base64," + d["data"][0]["b64_json"]
        except Exception as e:
            code = getattr(e, "code", None)
            # Print the error class and HTTP status only. Never print the request, headers or str(e).
            print("openai image error:", type(e).__name__, code or "", file=__import__("sys").stderr)
            retry = isinstance(code, int) and (code == 429 or 500 <= code < 600)
            if not retry or attempt == len(delays):
                return None
            wait = delays[attempt]
            ra = getattr(e, "headers", None) and e.headers.get("Retry-After")
            if ra and str(ra).strip().isdigit():
                wait = min(int(ra), 90)
            time.sleep(wait)

def generate_sections(cfg, keys):
    out = {}
    for k in keys:
        if getattr(cfg, "img_provider", "dashscope") == "openai":
            img = _openai(cfg, SECTION_PROMPTS[k])
        else:
            img = _one(cfg, SECTION_PROMPTS[k])
        if img:
            out[k] = img
    return out

def generate(cfg):
    if getattr(cfg, "img_provider", "dashscope") == "openai":
        return generate_sections(cfg, ["hero"])
    ep=cfg.img_endpoint or "https://dashscope-intl.aliyuncs.com"
    H={"Authorization":"Bearer "+cfg.img_key,"Content-Type":"application/json","X-DashScope-Async":"enable"}
    body={"model":cfg.img_model,"input":{"prompt":"elegant glowing DNA double helix, blue teal violet light, dark navy, minimal editorial banner"},"parameters":{"size":"1280*720","n":1}}
    try:
        req=urllib.request.Request(ep+"/api/v1/services/aigc/text2image/image-synthesis",data=json.dumps(body).encode(),headers=H)
        tid=json.load(urllib.request.urlopen(req,timeout=60))["output"]["task_id"]
        for _ in range(60):
            time.sleep(6)
            s=json.load(urllib.request.urlopen(urllib.request.Request(ep+"/api/v1/tasks/"+tid,headers={"Authorization":"Bearer "+cfg.img_key}),timeout=30))
            st=s["output"]["task_status"]
            if st=="SUCCEEDED":
                raw=urllib.request.urlopen(s["output"]["results"][0]["url"],timeout=60).read()
                return {"hero":"data:image/png;base64,"+base64.b64encode(raw).decode()}
            if st=="FAILED": break
    except Exception: pass
    return {}

def _one(cfg, prompt):
    if getattr(cfg, "img_provider", "dashscope") == "openai": return _openai(cfg, prompt, "1024x1024")
    import json, time, base64, urllib.request
    ep=cfg.img_endpoint or "https://dashscope-intl.aliyuncs.com"
    H={"Authorization":"Bearer "+cfg.img_key,"Content-Type":"application/json","X-DashScope-Async":"enable"}
    body={"model":cfg.img_model,"input":{"prompt":prompt},"parameters":{"size":"1024*1024","n":1}}
    try:
        req=urllib.request.Request(ep+"/api/v1/services/aigc/text2image/image-synthesis",data=json.dumps(body).encode(),headers=H)
        tid=json.load(urllib.request.urlopen(req,timeout=60))["output"]["task_id"]
        for _ in range(70):
            time.sleep(6)
            s=json.load(urllib.request.urlopen(urllib.request.Request(ep+"/api/v1/tasks/"+tid,headers={"Authorization":"Bearer "+cfg.img_key}),timeout=30))
            st=s["output"]["task_status"]
            if st=="SUCCEEDED":
                raw=urllib.request.urlopen(s["output"]["results"][0]["url"],timeout=60).read()
                return "data:image/png;base64,"+base64.b64encode(raw).decode()
            if st=="FAILED": break
    except Exception: pass
    return None

def generate_portraits(cfg, base_prompt, n=3):
    """Generate n speculative portrait variants from the appearance prompt.
    Only a phenotype description is sent (dark hair, hazel eyes, ...) — never raw genotypes."""
    styles=[", short neat beard, slightly wavy hair",
            ", clean-shaven, short tidy hair",
            ", around 55 years old, some grey, receding temples, gentle wrinkles",
            ", lighter end of the pigmentation range, prominent freckles"]
    out={}
    for i in range(min(n,len(styles))):
        img=_one(cfg, base_prompt+styles[i])
        if img: out[f"portrait_{i+1}"]=img
    return out
