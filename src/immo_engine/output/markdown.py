from __future__ import annotations
from immo_engine.domain.operation import Operation
from immo_engine.core.analysis import AnalysisResult

def render_md(op: Operation, res: AnalysisResult) -> str:
    verdict_emoji = {"OK": "✅", "REVIEW": "⚠️", "REJECT": "❌"}[res.verdict]
    reasons = "\n".join([f"- {r}" for r in res.reasons]) or "- Aucun point bloquant détecté"

    return f"""# Fiche opération — {op.title}

**Verdict** : {verdict_emoji} **{res.verdict}**  
**URL** : {op.source_url or "—"}

## Chiffres clés
- Coût total (hors fiscalité) : **{res.total_cost_eur:,.0f} €**
- Profit net estimé (V1) : **{res.net_profit_eur:,.0f} €**
- Marge : **{res.margin_pct:.1f} %**
- Durée estimée : **{op.duration_months} mois**
- Score de risque (V1) : **{res.risk_score:.2f} / 1.00**

## Entrées
- Achat : {op.purchase_price_eur:,.0f} €
- Notaire : {op.notary_fees_eur:,.0f} €
- Agence : {op.agency_fees_eur:,.0f} €
- Travaux : {op.works_budget_eur:,.0f} €
- Portage (charges/intérêts) : {op.holding_costs_eur:,.0f} €
- Revente : {op.resale_price_eur:,.0f} €

## Points d’attention
{reasons}

## Notes
- V1 : fiscalité non intégrée (sera ajoutée après arbitrage expert-comptable).
"""
