# -*- coding: utf-8 -*-
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import config, gen_images

def test_provider_defaults(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "openai")
    monkeypatch.setenv("IMAGE_API_KEY", "x")
    monkeypatch.delenv("IMAGE_MODEL", raising=False)
    c = config.Config(env_file="__none__")
    assert (c.img_provider, c.img_model) == ("openai", "gpt-image-1")
    monkeypatch.delenv("IMAGE_PROVIDER")
    c = config.Config(env_file="__none__")
    assert (c.img_provider, c.img_model) == ("dashscope", "wan2.2-t2i-flash")

def test_prompts_are_generic():
    banned = re.compile(r"rs\d+|\bi\d{7}\b|genotype|carrier of|haplogroup [A-Z]\d", re.I)
    for k, p in gen_images.SECTION_PROMPTS.items():
        assert not banned.search(p), k

def test_openai_request_shape(monkeypatch):
    sent = {}
    class R:
        def read(self): return b'{"data":[{"b64_json":"QUJD"}]}'
    def fake(req, timeout=0):
        sent["url"] = req.full_url
        sent["body"] = req.data
        sent["auth"] = req.headers.get("Authorization")
        return R()
    monkeypatch.setattr(gen_images.urllib.request, "urlopen", fake)
    class C: img_key = "k"; img_model = "gpt-image-1"; img_endpoint = None
    uri = gen_images._openai(C, "a calm abstract banner", "1536x1024")
    assert uri == "data:image/jpeg;base64,QUJD"
    assert sent["url"] == "https://api.openai.com/v1/images/generations"
    assert sent["auth"] == "Bearer k" and b'"gpt-image-1"' in sent["body"]

def test_render_places_section_banner():
    import render_html, safety, run_analysis
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    a = run_analysis.analyze(os.path.join(root, "examples", "mock_person.txt"))
    out = os.path.join(root, "results", "_test_banner.html")
    html = render_html.render(a, out, safety.load(), images={"sec-carrier": "data:image/png;base64,QUJD"}, opts={})
    i = html.index('id="sec-carrier"')
    assert 'class="secbanner"' in html[i:i + 400]

def _http_error(code):
    import urllib.error
    return urllib.error.HTTPError("https://x", code, "err", {}, None)

def test_openai_retries_on_429(monkeypatch):
    calls, sleeps = [], []
    class R:
        def read(self): return b'{"data":[{"b64_json":"QUJD"}]}'
    def fake(req, timeout=0):
        calls.append(1)
        if len(calls) <= 2: raise _http_error(429)
        return R()
    monkeypatch.setattr(gen_images.urllib.request, "urlopen", fake)
    monkeypatch.setattr(gen_images.time, "sleep", lambda s: sleeps.append(s))
    class C: img_key = "k"; img_model = "gpt-image-1"; img_endpoint = None
    assert gen_images._openai(C, "p") == "data:image/jpeg;base64,QUJD"
    assert len(sleeps) == 2

def test_openai_no_retry_on_400(monkeypatch):
    calls, sleeps = [], []
    def fake(req, timeout=0):
        calls.append(1); raise _http_error(400)
    monkeypatch.setattr(gen_images.urllib.request, "urlopen", fake)
    monkeypatch.setattr(gen_images.time, "sleep", lambda s: sleeps.append(s))
    class C: img_key = "k"; img_model = "gpt-image-1"; img_endpoint = None
    assert gen_images._openai(C, "p") is None
    assert len(calls) == 1 and sleeps == []
