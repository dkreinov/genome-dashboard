# -*- coding: utf-8 -*-
"""Optional: fill data-<lang> attributes on every data-en element via an LLM.
No-op unless a key is configured. Provider = OpenAI-compatible chat endpoint."""
import json, re, urllib.request
def _translate_batch(strings, lang, cfg):
    prompt=("Translate each JSON array item to "+lang+". Keep genotype tokens "
            "(e.g. AG, Gly/Gly, ε3/ε3, rsIDs) unchanged. Return ONLY a JSON array, same length.\n"
            +json.dumps(strings, ensure_ascii=False))
    body={"model":cfg.llm_model or "gpt-4o-mini","messages":[{"role":"user","content":prompt}],"temperature":0}
    req=urllib.request.Request((cfg.llm_endpoint or "https://api.openai.com/v1")+"/chat/completions",
        data=json.dumps(body).encode(),headers={"Authorization":"Bearer "+cfg.llm_key,"Content-Type":"application/json"})
    txt=json.load(urllib.request.urlopen(req,timeout=120))["choices"][0]["message"]["content"]
    m=re.search(r"\[.*\]",txt,re.S); return json.loads(m.group(0)) if m else strings
def fill(html_str, langs, cfg):
    uniq=sorted(set(re.findall(r'data-en="([^"]*)"', html_str)))
    for lang in langs:
        out={}
        for i in range(0,len(uniq),40):
            chunk=uniq[i:i+40]
            try:
                tr=_translate_batch([s.replace("&amp;","&").replace("&#x27;","'") for s in chunk],lang,cfg)
                for s,t in zip(chunk,tr): out[s]=t
            except Exception: pass
        import html as _h
        def add(m):
            en=m.group(1); t=out.get(en)
            if not t: return m.group(0)
            return m.group(0)[:-1]+f' data-{lang}="{_h.escape(t,quote=True)}">'
        html_str=re.sub(r'data-en="([^"]*)">', add, html_str)
    return html_str
