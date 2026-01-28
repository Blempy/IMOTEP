from __future__ import annotations
from dataclasses import dataclass
from immo_engine.domain.operation import Operation

@dataclass(frozen=True)
class AnalysisResult:
    total_cost_eur: float
    gross_profit_eur: float
    net_profit_eur: float
    margin_pct: float
    verdict: str              # "OK" | "REVIEW" | "REJECT"
    reasons: list[str]
    risk_score: float         # 0..1 (simple au début)

def analyze(op: Operation, strategy: dict) -> AnalysisResult:
    total_cost = (
        op.purchase_price_eur
        + op.notary_fees_eur
        + op.agency_fees_eur
        + op.works_budget_eur
        + op.holding_costs_eur
    )
    gross_profit = op.resale_price_eur - total_cost
    net_profit = gross_profit  # V1: net = brut (V2: impôts, IS/IR, etc.)
    margin_pct = (net_profit / total_cost * 100) if total_cost > 0 else 0.0

    reasons: list[str] = []

    # Règles (strategy-as-code)
    min_net = strategy["objectives"]["min_net_profit_eur"]
    min_margin = strategy["objectives"]["min_margin_pct"]
    max_dur = strategy["operation"]["max_duration_months"]

    if net_profit < min_net:
        reasons.append(f"Net < seuil: {net_profit:,.0f}€ < {min_net:,.0f}€")
    if margin_pct < min_margin:
        reasons.append(f"Marge < seuil: {margin_pct:.1f}% < {min_margin:.1f}%")
    if op.duration_months > max_dur:
        reasons.append(f"Durée > seuil: {op.duration_months} mois > {max_dur}")

    # Risk score V1 (heuristique simple)
    risk = 0.0
    if op.works_budget_eur > 0:
        # plus les travaux pèsent lourd dans le coût total, plus ça risque de déraper
        risk += min(0.6, op.works_budget_eur / max(1.0, total_cost))
    if op.duration_months >= 12:
        risk += 0.2
    risk = min(1.0, risk)

    # Verdict
    if len(reasons) == 0 and risk <= strategy["risk"]["max_risk_score"]:
        verdict = "OK"
    elif net_profit <= 0:
        verdict = "REJECT"
        if "Net < seuil" not in " ".join(reasons):
            reasons.append("Net <= 0 : opération non viable en l’état")
    else:
        verdict = "REVIEW"
        if risk > strategy["risk"]["max_risk_score"]:
            reasons.append(f"Risque élevé: {risk:.2f} > {strategy['risk']['max_risk_score']:.2f}")

    return AnalysisResult(
        total_cost_eur=total_cost,
        gross_profit_eur=gross_profit,
        net_profit_eur=net_profit,
        margin_pct=margin_pct,
        verdict=verdict,
        reasons=reasons,
        risk_score=risk,
    )
