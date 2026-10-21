"""Abbildungen: Reihen, Farben, gesperrte Achsen; der PDF-Bau mit Umlauten und ohne gewählte Menge der exakten Rechnung."""

from fractions import Fraction

import fpr_constants as C
import fpr_evaluation as ev
import fpr_visualization as V
from fpr_pdf_export import build_pdf


def _locked(fig):
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_items_figure_groups_the_choices():
    a = ev.analyse(ev.Settings(n=12, d=2, seed=4))
    fig = V.build_items(a.instance, a.exact.chosen, a.fptas.chosen)
    names = [t.name for t in fig.data]
    assert set(names) <= {"von beiden gewählt", "nur exakt gewählt", "nur vom FPTAS gewählt", "nicht gewählt"}
    assert sum(len(t.x) for t in fig.data) == 12                       # jedes Paket genau einmal
    _locked(fig)


def test_items_figure_without_the_exact_choice_shows_only_the_fptas_choice():
    a = ev.analyse(ev.Settings(n=12, d=2, seed=4))
    fig = V.build_items(a.instance, None, a.fptas.chosen)
    assert [t.name for t in fig.data] == ["vom FPTAS gewählt", "nicht gewählt"] or [t.name for t in fig.data] == ["vom FPTAS gewählt"]
    assert sum(len(t.x) for t in fig.data) == 12


def test_cells_and_table_figures():
    fig = V.build_cells(1000, 10)
    assert list(fig.data[0].y) == [1000, 10] and fig.layout.yaxis.type == "log"
    _locked(fig)
    a = ev.analyse(ev.Settings(n=8, d=1, seed=3))
    table_fig = V.build_table(a.table, a.instance.weights, a.instance.values)
    assert len(table_fig.data[0].z) == 9 and len(table_fig.data[0].y) == 9
    _locked(table_fig)


def test_digits_and_eps_figures_have_their_series_and_the_markers():
    digits = ev.sweep_digits(n=6, seeds=(1, 2), digits=(1, 2, 3), eps_list=(0.5, 0.2))
    fig = V.build_digits(digits, highlight_d=2)
    assert [t.name for t in fig.data] == ["exakte Tabelle n · (W + 1)", "FPTAS, ε = 0,5", "FPTAS, ε = 0,2", "gewählte Stellen"]
    assert list(fig.data[-1].x) == [2] and fig.layout.yaxis.type == "log"
    assert "gewählte Stellen" not in [t.name for t in V.build_digits(digits, highlight_d=9).data]
    _locked(fig)
    eps_rows = ev.sweep_eps(8, "unc", seeds=(1, 2, 3), digits=2, eps_list=(0.5, 0.1))
    q = V.build_eps_quality(eps_rows, highlight_eps=0.1)
    assert [t.name for t in q.data] == ["Garantie 1 − ε", "kleinste gemessene Güte", "mittlere (Median) Güte", "gewähltes ε"]
    assert list(q.data[0].y) == [0.5, 0.9] and list(q.data[-1].x) == ["0,1"]
    assert "gewähltes ε" not in [t.name for t in V.build_eps_quality(eps_rows).data]
    cells = V.build_eps_cells(eps_rows)
    assert [t.name for t in cells.data] == ["FPTAS", "exakte Rechnung"] and cells.layout.yaxis.type == "log"
    _locked(q)
    _locked(cells)


def test_trap_figure_marks_the_chosen_trap():
    rows = ev.sweep_trap(sizes=(10, 30), eps_list=(0.5, 0.1))
    chosen = ev.analyse_trap(20, 0.5)
    fig = V.build_trap(rows, highlight=chosen)
    assert [t.name for t in fig.data] == ["Garantie 1 − ε", "Falle mit 10 Paketen", "Falle mit 30 Paketen", "gewählt: 20 Pakete"]
    assert list(fig.data[0].y) == [0.5, 0.9] and list(fig.data[-1].y) == [float(Fraction(chosen.fptas_value, chosen.opt_value))]
    assert "gewählt: 20 Pakete" not in [t.name for t in V.build_trap(rows).data]
    _locked(fig)


def test_bin_figures():
    r = ev.analyse_bins(3, 20, 5)
    fig = V.build_bin_steps(r.states)
    assert list(fig.data[0].y) == list(r.states.steps) and list(fig.data[0].x) == list(range(1, len(r.states.steps) + 1))
    _locked(fig)
    fixed = V.build_bins_fixed(ev.sweep_bins_fixed(counts=(2, 3), bounds=(10, 20), seeds=(1, 2)))
    assert [t.name for t in fixed.data] == ["2 Behälter", "3 Behälter"] and fixed.layout.xaxis.type == "log" and fixed.layout.yaxis.type == "log"
    plant_rows = ev.sweep_plant(counts=(2, 3), seeds=(40, 41))
    plant = V.build_plant(plant_rows)
    assert list(plant.data[1].y) == [r["peak"] for r in plant_rows] and plant.layout.yaxis.type == "log"
    _locked(fixed)
    _locked(plant)


def test_pdf_builds_with_umlauts_and_without_the_exact_choice():
    for settings in (ev.Settings(), ev.Settings(n=20, d=6), ev.Settings(n=8, d=1, seed=3, eps=0.5)):
        pdf = build_pdf(ev.analyse(settings))
        assert pdf.startswith(b"%PDF") and len(pdf) > 1000


def test_color_constants_are_distinct():
    assert len(set(C.COLOR_SERIES)) == len(C.COLOR_SERIES)
