# -*- coding: utf-8 -*-
"""Config & graceful-degradation.

Optional features are OFF unless their key is present. No key ⇒ the pipeline
still produces a full English, image-free dashboard offline.

Keys are read from (first wins): explicit args -> process env -> a .env file
(path via GENOME_DASHBOARD_ENV or ./.env). Generic, provider-agnostic names:
  LLM_API_KEY   / LLM_ENDPOINT   / LLM_MODEL     -> translation
  IMAGE_API_KEY / IMAGE_ENDPOINT / IMAGE_MODEL   -> hero images
"""
import os, re

def _load_env_file(path):
    out = {}
    if path and os.path.exists(path):
        for ln in open(path, encoding="utf-8", errors="ignore"):
            m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.+?)\s*$", ln)
            if m and not ln.strip().startswith("#"):
                out[m.group(1)] = m.group(2)
    return out

class Config:
    def __init__(self, overrides=None, env_file=None):
        env_file = env_file or os.environ.get("GENOME_DASHBOARD_ENV") or ".env"
        filed = _load_env_file(env_file)
        def get(k, default=None):
            if overrides and overrides.get(k): return overrides[k]
            return os.environ.get(k) or filed.get(k) or default
        self.llm_key      = get("LLM_API_KEY")
        self.llm_endpoint = get("LLM_ENDPOINT")
        self.llm_model    = get("LLM_MODEL")
        self.img_key      = get("IMAGE_API_KEY")
        self.img_endpoint = get("IMAGE_ENDPOINT")
        self.img_model    = get("IMAGE_MODEL", "wan2.2-t2i-flash")

    def has_translation(self): return bool(self.llm_key)
    def has_images(self):      return bool(self.img_key)

if __name__ == "__main__":
    c = Config()
    print(f"translation={c.has_translation()} images={c.has_images()}")
