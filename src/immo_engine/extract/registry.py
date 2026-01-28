from __future__ import annotations
from immo_engine.extract.base import Extractor
from immo_engine.extract.leboncoin import LeboncoinExtractor

EXTRACTORS: list[Extractor] = [
    LeboncoinExtractor(),
]

def get_extractor(url: str) -> Extractor | None:
    for ex in EXTRACTORS:
        try:
            if ex.can_handle(url):
                return ex
        except Exception:
            continue
    return None
