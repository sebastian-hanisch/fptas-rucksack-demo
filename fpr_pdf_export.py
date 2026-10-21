"""PDF-Export (fpdf2, Kernschriften): Einstellungen, Ergebnis von exakter Rechnung und FPTAS und die Pakete. Kein Gedankenstrich und kein Euro-Zeichen (Kernschriften)."""

from fpdf import FPDF

import fpr_constants as C
import fpr_evaluation as ev


def _text(value: str) -> str:
    """Zeichen, die die Kernschriften nicht kennen, ersetzen (Gedankenstrich, Pfeile, Fettdruck-Markierung, mathematische Zeichen)."""
    table = {"–": "-", "—": "-", "→": "->", "**": "", "€": "EUR", "·": "*", "³": "^3", "≤": "<=", "≥": ">=", "ε": "eps", "−": "-", "⌈": "", "⌉": "", "×": "x", "„": '"', "“": '"'}
    for old, new in table.items():
        value = value.replace(old, new)
    return value


def _para(pdf: FPDF, height: float, text: str) -> None:
    """Absatz über die volle Breite; danach steht der Cursor wieder am linken Rand (fpdf2 setzt ihn sonst an den rechten Rand)."""
    pdf.multi_cell(0, height, _text(text), new_x="LMARGIN", new_y="NEXT")


def build_pdf(a: ev.Analysis) -> bytes:
    s, inst = a.settings, a.instance
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _text("Zahlen und Härte: pseudopolynomiell, FPTAS, stark NP-schwer"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    _para(pdf, 5.5, f"Pakete: {s.n}   Stellen der Gewichte: {s.d}   Familie: {C.FAMILIES[s.family]}   Zufalls-Seed: {s.seed}   eps = {ev.fmt_eps(s.eps)}\n"
                    f"Kapazität: {ev.fmt_int(inst.capacity)} (40 % der Gewichtssumme)")
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Ergebnis", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    _para(pdf, 5.5, ev.verdict_run(a)[1])
    _para(pdf, 5.5, f"Exakte Rechnung: Optimum {ev.fmt_int(a.exact.value)}, Tabelle {ev.fmt_int(a.exact.cells)} Zellen.   FPTAS: Wert {ev.fmt_int(a.fptas.value)}, Tabelle {ev.fmt_int(a.fptas.cells)} Zellen.")
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Pakete", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    exact = None if a.exact.chosen is None else set(a.exact.chosen)
    fptas = set(a.fptas.chosen)
    for i in range(min(inst.n, 80)):
        marks = ("exakt: " + ("ja" if i in exact else "nein") + "   " if exact is not None else "") + "FPTAS: " + ("ja" if i in fptas else "nein")
        _para(pdf, 4.8, f"Paket {i + 1}: Gewicht {ev.fmt_int(inst.weights[i])}, Wert {ev.fmt_int(inst.values[i])}   {marks}")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    _para(pdf, 4.5, "Aufwand in Tabellenzellen und Zuständen, nicht in Sekunden. Sebastian Hanisch - Operations Research und Machine Learning.")
    return bytes(pdf.output())
