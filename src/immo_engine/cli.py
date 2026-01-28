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

    # input
    with open(out_dir / "operation.json", "w", encoding="utf-8") as f:
        f.write(op.model_dump_json(indent=2))

    # report
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
    holding = float(input("Portage (charges/in
