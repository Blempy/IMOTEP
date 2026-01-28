from __future__ import annotations
import json
import re
from bs4 import BeautifulSoup

from immo_engine.extract.base import ExtractedListing

EURO_RE = re.compile(r"(?<!\d)(\d{1,3}(?:[ \u00A0]\d{3})+|\d{2,})(?:[,.]\d+)?\s*€", re.IGNORECASE)
M2_RE = re.compile(r"(\d{1,3}(?:[,.]\d+)?)\s*m²", re.IGNORECASE)

def _to_float_fr(s: str) -> float:
    s = s.replace("\u00A0", " ").replace(" ", "").replace(",", ".")
    return float(s)

def extract_from_jsonld(soup: BeautifulSoup) -> dict:
    # JSON-LD peut être un objet ou une liste d'objets
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.get_text(strip=True))
            # normalise en liste
            items = data if isinstance(data, list) else [data]
            for it in items:
                if isinstance(it, dict):
                    # On prend le premier dict "utile"
                    return it
        except Exception:
            continue
    return {}

def extract_generic(url: str, html: str) -> ExtractedListing:
    soup = BeautifulSoup(html, "html.parser")

    title = None
    if soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(strip=True)

    # OpenGraph (souvent très utile)
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()

    # JSON-LD
    ld = extract_from_jsonld(soup)

    price = None
    surface = None
    city = None
    postal = None

    # Tentative via JSON-LD
    # Certaines annonces utilisent "offers": {"price": "..."}
    try:
        offers = ld.get("offers") if isinstance(ld, dict) else None
        if isinstance(offers, dict) and offers.get("price"):
            price = float(str(offers["price"]).replace(",", "."))
    except Exception:
        pass

    # Fallback regex € dans le HTML
    if price is None:
        m = EURO_RE.search(soup.get_text(" ", strip=True))
        if m:
            price = _to_float_fr(m.group(1))

    # Surface (regex m²)
    m2m = M2_RE.search(soup.get_text(" ", strip=True))
    if m2m:
        try:
            surface = float(m2m.group(1).replace(",", "."))
        except Exception:
            pass

    return ExtractedListing(
        url=url,
        title=title,
        price_eur=price,
        surface_m2=surface,
        city=city,
        postal_code=postal,
        raw={"jsonld": ld} if ld else None,
    )
