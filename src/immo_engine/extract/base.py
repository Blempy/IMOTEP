from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Protocol
from urllib.parse import urlparse

@dataclass
class ExtractedListing:
    url: str
    title: Optional[str] = None
    price_eur: Optional[float] = None
    surface_m2: Optional[float] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    raw: dict | None = None

class Extractor(Protocol):
    def can_handle(self, url: str) -> bool: ...
    def extract(self, url: str) -> ExtractedListing: ...

def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower()
