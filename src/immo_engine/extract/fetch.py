from __future__ import annotations
import re
import time
from dataclasses import dataclass
from typing import Optional

import requests
from playwright.sync_api import sync_playwright

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

@dataclass
class FetchResult:
    url: str
    html: str
    final_url: str

def fetch_html_requests(url: str, timeout: int = 25) -> FetchResult:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    r.raise_for_status()
    return FetchResult(url=url, html=r.text, final_url=str(r.url))

def fetch_html_playwright(url: str, timeout_ms: int = 30000) -> FetchResult:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=UA, viewport={"width": 1280, "height": 900})
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

        # Beaucoup de sites chargent après coup. On laisse une petite fenêtre.
        page.wait_for_timeout(1500)

        # Si la page a du contenu dynamique, un scroll peut déclencher des blocs.
        try:
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(800)
        except Exception:
            pass

        html = page.content()
        final_url = page.url
        browser.close()
        return FetchResult(url=url, html=html, final_url=final_url)

def fetch_html(url: str, prefer_playwright: bool = False) -> FetchResult:
    # Par défaut on tente requests (rapide). Si ça casse, on bascule Playwright.
    if prefer_playwright:
        return fetch_html_playwright(url)
    try:
        return fetch_html_requests(url)
    except Exception:
        return fetch_html_playwright(url)
