# -*- coding: utf-8 -*-
"""Optional hero art via a DashScope-style async image API. Generic prompts only —
NEVER genotype data. No-op unless IMAGE_API_KEY set."""
import json, time, base64, urllib.request
def generate(cfg):
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
