from __future__ import annotations
import json, os, uuid
from pathlib import Path
import yaml
from rich.console import Console
from rich.table import Table

from immo_engine.domain.operation import Operation
from immo_engine.core.analysis import analyze
from immo_engine.output.markdown import render_md

console = Console()

def load_strategy(path: str = "config/strategy.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_report(op: Operation, md: str) -> Path:
    op_id = uuid.uuid4().hex[:10]
    out_dir = Path("data/operations") / op_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # sauvegarde input
    with open(out_dir / "operation.json", "w", encoding="utf-8") as f:
        f.write(op.model_dump_json(indent=2))

    # sauvegarde report
    report_path = out_dir / "report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

    return report_path

def interactive_input() -> Operation:
    console.print("[bold]Mode interactif[/bold]")
    title = input("Titre: ").strip() or "Opération"
    purchase = float(input("Prix achat (€): ").strip())
    works = float(input("Travaux (€) [0]: ").strip() or "0")
    notary = float(input("Frais notaire (€) [0]: ").strip() or "0")
    agency = float(input("Frais agence (€) [0]: ").strip() or "0")
    holding = float(input("Portage (charges/intérêts) (€) [0]: ").strip() or "0")
    resale = float(input("Prix revente (€): ").strip())
    duration = int(input("Durée (mois) [9]: ").strip() or "9")

    return Operation(
        title=title,
        purchase_price_eur=purchase,
        works_budget_eur=works,
        notary_fees_eur=notary,
        agency_fees_eur=agency,
        holding_costs_eur=holding,
        resale_price_eur=resale,
        duration_months=duration,
    )

def load_operation_file(path: str) -> Operation:
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith((".yaml", ".yml")):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)
    return Operation(**data)

def main():
    import argparse
    parser = argparse.ArgumentParser(prog="immo")
    parser.add_argument("--file", help="Chemin YAML/JSON d'une opération")
    parser.add_argument("--url", help="URL annonce immobilière")
    parser.add_argument("--strategy", default="config/strategy.yaml")
    args = parser.parse_args()

    strategy = load_strategy(args.strategy)

    # --- CHOIX DU MODE D'ENTRÉE ---
    if args.file:
        op = load_operation_file(args.file)

    elif args.url:
        from immo_engine.extract.registry import get_extractor
        from immo_engine.extract.fetch import fetch_html
        from immo_engine.extract.generic import extract_generic

        ex = get_extractor(args.url)
        if ex:
            listing = ex.extract(args.url)
        else:
            fr = fetch_html(args.url)
            listing = extract_generic(fr.final_url, fr.html)

        console.print("[bold]Extraction URL[/bold]")
        console.print(f"URL: {listing.url}")
        console.print(f"Titre: {listing.title or '—'}")
        console.print(f"Prix: {listing.price_eur or '—'}")
        console.print(f"Surface: {listing.surface_m2 or '—'}")
        console.print(f"Ville: {listing.city or '—'} {listing.postal_code or ''}")

        title = (listing.title or "Opération URL").strip()
        purchase = float(listing.price_eur or input("Prix achat (€): ").strip())
        works = float(input("Travaux (€) [0]: ").strip() or "0")
        notary = float(input("Frais notaire (€) [0]: ").strip() or "0")
        agency = float(input("Frais agence (€) [0]: ").strip() or "0")
        holding = float(input("Portage (charges/intérêts) (€) [0]: ").strip() or "0")
        resale = float(input("Prix revente (€): ").strip())
        duration = int(input("Durée (mois) [9]: ").strip() or "9")

        op = Operation(
            title=title,
            source_url=listing.url,
            purchase_price_eur=purchase,
            works_budget_eur=works,
            notary_fees_eur=notary,
            agency_fees_eur=agency,
            holding_costs_eur=holding,
            resale_price_eur=resale,
            duration_months=duration,
            surface_m2=listing.surface_m2,
            city=listing.city,
            postal_code=listing.postal_code,
        )

    else:
        op = interactive_input()

    # --- ANALYSE ---
    res = analyze(op, strategy)
    md = render_md(op, res)
    report_path = save_report(op, md)

    t = Table(title="Résultat analyse")
    t.add_column("Verdict")
    t.add_column("Net (€)", justify="right")
    t.add_column("Marge (%)", justify="right")
    t.add_column("Risque", justify="right")

    t.add_row(
        res.verdict,
        f"{res.net_profit_eur:,.0f}",
        f"{res.margin_pct:.1f}",
        f"{res.risk_score:.2f}",
    )

    console.print(t)
    console.print(f"[green]Report généré:[/green] {report_path}")
