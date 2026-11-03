"""Offline journal-style table exports (DOCX, HTML, and LaTeX)."""
from __future__ import annotations

from html import escape
from io import BytesIO
import math
from typing import Sequence

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


def _number(value: float | int | None, digits: int = 3) -> str:
    if value is None or not math.isfinite(float(value)):
        return "Not estimable"
    return f"{float(value):.{digits}f}"


def publication_rows(counts: Sequence[int], result: dict) -> tuple[list[str], list[list[str]]]:
    if len(counts) != 4:
        raise ValueError("counts must be in (a,b,c,d) order")
    a, b, c, d = counts
    headers = ["Measure", "Estimate", "95% CI", "Method"]
    rows = []
    for key, label, ci_key, method in (
        ("risk_ratio", "Risk ratio", "risk_ratio_katz_ci", "Katz log CI"),
        ("odds_ratio", "Odds ratio", "odds_ratio_woolf_ci", "Woolf log CI"),
        ("risk_difference", "Risk difference", "risk_difference_wald_ci", "Wald CI"),
    ):
        ci = result.get(ci_key)
        interval = f"{_number(ci[0])}–{_number(ci[1])}" if ci and len(ci) == 2 else "Not estimable"
        rows.append([label, _number(result.get(key)), interval, method])
    rows.insert(0, ["Exposed / cases (a)", str(a), "", "Count"])
    rows.insert(1, ["Exposed / non-cases (b)", str(b), "", "Count"])
    rows.insert(2, ["Unexposed / cases (c)", str(c), "", "Count"])
    rows.insert(3, ["Unexposed / non-cases (d)", str(d), "", "Count"])
    return headers, rows


def export_journal_html(counts: Sequence[int], result: dict, *, title: str = "Clinical epidemiology results") -> str:
    headers, rows = publication_rows(counts, result)
    head = "".join(f"<th scope=\"col\">{escape(value)}</th>" for value in headers)
    body = "".join("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>" for row in rows)
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>" + escape(title) +
            "</title><style>body{font:11pt Arial,sans-serif}table{border-collapse:collapse;width:100%;border-top:2px solid #111;border-bottom:2px solid #111}"
            "th{border-bottom:1px solid #111;text-align:left}th,td{padding:.35rem .5rem;vertical-align:top}td{border:0}</style></head><body><h1>" +
            escape(title) + "</h1><table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table></body></html>")


def export_journal_latex(counts: Sequence[int], result: dict, *, title: str = "Clinical epidemiology results") -> str:
    headers, rows = publication_rows(counts, result)
    def tex(value: str) -> str:
        return value.replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
    row_break = " " + chr(92) * 2
    table_rows = [" & ".join(tex(v) for v in headers) + row_break]
    for label, estimate, interval, method in rows:
        if method == "Count":
            estimate_tex, interval_tex = f"${tex(estimate)}$", ""
        else:
            estimate_tex = f"${tex(estimate)}$" if estimate != "Not estimable" else r"$\text{Not estimable}$"
            if "–" in interval:
                low, high = interval.split("–", maxsplit=1)
                interval_tex = f"$({tex(low.strip())},{chr(92)};{tex(high.strip())})$"
            else:
                interval_tex = r"$\text{Not estimable}$"
        table_rows.append(" & ".join([tex(label), estimate_tex, interval_tex, tex(method)]) + row_break)
    return ("% Requires \\usepackage{booktabs}\n\\begin{table}[htbp]\n\\centering\n\\caption{" + tex(title) +
            "}\n\\begin{tabular}{llll}\n\\toprule\n" + "\n\\midrule\n".join([table_rows[0], "\n".join(table_rows[1:])]) +
            "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")


def export_journal_docx(counts: Sequence[int], result: dict, *, title: str = "Clinical epidemiology results") -> bytes:
    headers, rows = publication_rows(counts, result)
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph("Cell order: a=exposed cases; b=exposed non-cases; c=unexposed cases; d=unexposed non-cases.")
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = True
    for cell, value in zip(table.rows[0].cells, headers):
        cell.text = value
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.size = Pt(9)
    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
            for run in cell.paragraphs[0].runs:
                run.font.size = Pt(9)
    # Three-rule table: top and bottom on table; header bottom only; no vertical borders.
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            tc_pr = cell._tc.get_or_add_tcPr()
            borders = tc_pr.first_child_found_in("w:tcBorders")
            if borders is None:
                from docx.oxml import OxmlElement
                borders = OxmlElement("w:tcBorders")
                tc_pr.append(borders)
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn
            for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
                tag = "w:" + edge
                element = borders.find(qn(tag))
                if element is None:
                    element = OxmlElement(tag)
                    borders.append(element)
                if edge in {"top"} and row_index == 0 or edge == "bottom" and row_index == 0 or edge == "bottom" and row_index == len(table.rows) - 1:
                    element.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "single")
                    element.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz", "8" if edge != "bottom" or row_index != 0 else "6")
                    element.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color", "000000")
                else:
                    element.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "nil")
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()
