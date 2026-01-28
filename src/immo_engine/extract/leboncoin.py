from __future__ import annotations
import json
import re
from bs4 import BeautifulSoup

from immo_engine.extract.base import ExtractedListing, Extractor
from immo_engine.extract.fetch import fetch_html
from immo_engine.extract.generic import extract_generic

# Leboncoin change souvent. Stratégie robuste :
# 1) charger via Playwright (souvent nécessaire)
# 2) chercher JSON-LD
# 3) chercher des blobs JSON dans <script> (PRELOADED_STATE, etc.)
# 4) fallback generic

PRELOADED_RE = re.compile(r"__PRELOADED_STATE__\s*=\s*({.*?})\s*;", re.DOTALL)
PRICE_IN_JSON_RE = re.compile(r'"price"\s*:\s*("?)(\d+)\1')
SURFACE_IN_JSON_RE = re.compile(r'"square"\s*:\s*("?)(\d+(?:\.\d+)?)\1|"(?:surface|area)"\s*:\s*("?)(\d+(?:\.\d+)?)\2')
CITY_RE = re.compile(r'"city"\s*:\s*"([^"]+)"')
POSTAL_RE = re.compile(r'"zipcode"\s*:\s*"(\d{5})"')

class LeboncoinExtractor:
    def can_handle(self, url: str) -> bool:
        return "leboncoin.fr" in url

    def extract(self, url: str) -> ExtractedListing:
        fr = fetch_html(url, prefer_playwright=True)
        html = fr.html
        soup = BeautifulSoup(html, "html.parser")

        # 1) Tente JSON-LD via generic (souvent ça suffit)
        gen = extract_generic(fr.final_url, html)
        if gen.price_eur or gen.surface_m2 or gen.title:
            # On garde, mais on tente encore d’enrichir
            listing = gen
        else:
            listing = ExtractedListing(url=fr.final_url)

        # 2) Extraction via scripts JSON internes
        text = html

        # Prix
        if listing.price_eur is None:
            m = PRICE_IN_JSON_RE.search(text)
            if m:
                listing.price_eur = float(m.group(2))

        # Surface
        if listing.surface_m2 is None:
            m = SURFACE_IN_JSON_RE.search(text)
            if m:
                # le regex a 2 groupes possibles, on prend celui qui matche
                val = m.group(2) or m.group(4)
                try:
                    listing.surface_m2 = float(val)
                except Exception:
                    pass

        # Ville / CP
        if listing.city is None:
            m = CITY_RE.search(text)
            if m:
                listing.city = m.group(1)
        if listing.postal_code is None:
            m = POSTAL_RE.search(text)
            if m:
                listing.postal_code = m.group(1)

        # Titre (si pas déjà)
        if not listing.title:
            if soup.title and soup.title.get_text(strip=True):
                listing.title = soup.title.get_text(strip=True)

        listing.raw = listing.raw or {}
        listing.raw["final_url"] = fr.final_url

        return listing
