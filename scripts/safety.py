# -*- coding: utf-8 -*-
"""Centralized, non-negotiable safety text. Sections that touch medication, carrier
status or cancer MUST include their caveat in the rendered output (every language)."""
import json, os
REF = os.path.join(os.path.dirname(__file__), "..", "reference")
def load():
    return json.load(open(os.path.join(REF,"disclaimers.json"), encoding="utf-8"))
