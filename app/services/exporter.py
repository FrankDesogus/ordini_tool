from __future__ import annotations

import pandas as pd
from PyQt6.QtGui import QGuiApplication


def to_tsv(rows: list[dict], columns: list[tuple[str, str]]) -> str:
    headers = [header for _, header in columns]
    lines = ["\t".join(headers)]
    for row in rows:
        values = []
        for key, _ in columns:
            raw = row.get(key)
            text = "" if raw is None else str(raw)
            values.append(text.replace("\t", " ").replace("\n", " "))
        lines.append("\t".join(values))
    return "\n".join(lines)


def export_excel(rows: list[dict], columns: list[tuple[str, str]], filepath: str) -> None:
    data = [{header: row.get(key) for key, header in columns} for row in rows]
    pd.DataFrame(data).to_excel(filepath, index=False)


def copy_to_clipboard(tsv: str) -> None:
    QGuiApplication.clipboard().setText(tsv)
