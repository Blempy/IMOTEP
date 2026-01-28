from __future__ import annotations
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class Operation(BaseModel):
    # Identité
    title: str = Field(default="Opération sans titre")
    source_url: Optional[HttpUrl] = None

    # Entrées financières
    purchase_price_eur: float
    notary_fees_eur: float = 0
    agency_fees_eur: float = 0
    works_budget_eur: float = 0
    holding_costs_eur: float = 0  # taxes, intérêts, charges, etc.

    # Sortie
    resale_price_eur: float

    # Timing
    duration_months: int = 9

    # Données “immo”
    surface_m2: Optional[float] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
