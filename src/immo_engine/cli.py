from __future__ import annotations

import json
import uuid
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

    with open(out_dir / "operation.json", "w", encoding="utf-8") as f:
        f.write(op.model_dump_json(indent=2))

    report_path = out_dir / "report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

    return report_path


def load_operation_file(path: str) -> Operation:
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith((".yaml", ".yml")):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)
    return Operation(**data)


def interactive_input() -> Operation:
    console.print("[bold]Mode interactif[/bold]")

    title = input("Titre: ").strip() or "Operation"
    purchase = float(input("Prix achat EUR: ").strip())
    works = float(input("Travaux EUR [0]: ").strip() or "0")
    notary = float(input("Frais notaire EUR [0]: ").strip() or "0")
    agency = float(input("Frais agence EUR [0]: ").strip() or "0")
    holding = float(input("Portage charges EUR [0]: ").strip() or "0")
    resale = float(input("Prix revente EUR: ").strip())
    duration = int(input("Duree mois [9]: ").strip() or "9")

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


def operation_from_url(url: str, debug: bool = False) -> Operation:
    from immo_engine.extract.registry import get_extractor
    from immo_engine.extract.fetch import fetch_html
    from immo_engine.extract.generic import extract_generic

    ex = get_extractor(url)
    if ex and hasattr(ex, "extract"):
        listing = ex.extract(url, debug=debug)  # <-- debug
    else:
        fr = fetch_html(url)
        listing = extract_generic(fr.final_url, fr.html)

    console.print("[bold]Extraction URL[/bold]")
    console.print(f"URL: {listing.url}")
    console.print(f"Titre: {listing.title or '-'}")
    console.print(f"Prix: {listing.price_eur or '-'}")
    console.print(f"Surface: {listing.surface_m2 or '-'}")
    console.print(f"Ville: {listing.city or '-'} {listing.postal_code or ''}")

    title = (listing.title or "Operation URL").strip()
    purchase = float(listing.price_eur or input("Prix achat EUR: ").strip())
    works = float(input("Travaux EUR [0]: ").strip() or "0")
    notary = float(input("Frais notaire EUR [0]: ").strip() or "0")
    agency = float(input("Frais agence EUR [0]: ").strip() or "0")
    holding = float(input("Portage charges EUR [0]: ").strip() or "0")
    resale = float(input("Prix revente EUR: ").strip())
    duration = int(input("Duree mois [9]: ").strip() or "9")

    return Operation(
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


def main():
    import argparse

    parser = argparse.ArgumentParser(prog="immo")
    parser.add_argument("--file", help="Chemin YAML/JSON d'une operation")
    parser.add_argument("--url", help="URL annonce immobiliere")
    parser.add_argument("--strategy", default="config/strategy.yaml")
    args = parser.parse_args()

    parser.add_argument("--debug-url", action="store_true", help="Debug extraction URL (sauve HTML + XHR)")

    strategy = load_strategy(args.strategy)

    if args.file:
        op = load_operation_file(args.file)
    elif args.url:
        op = operation_from_url(args.url, debug=args.debug_url)
    else:
        op = interactive_input()

    res = analyze(op, strategy)
    md = render_md(op, res)
    report_path = save_report(op, md)

    table = Table(title="Resultat analyse")
    table.add_column("Verdict")
    table.add_column("Net EUR", justify="right")
    table.add_column("Marge %", justify="right")
    table.add_column("Risque", justify="right")

    table.add_row(
        res.verdict,
        f"{res.net_profit_eur:,.0f}",
        f"{res.margin_pct:.1f}",
        f"{res.risk_score:.2f}",
    )

    console.print(table)
    console.print(f"[green]Report genere:[/green] {report_path}")


if __name__ == "__main__":
    main()
