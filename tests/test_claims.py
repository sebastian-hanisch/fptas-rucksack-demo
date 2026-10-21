"""Jede Zahl der README steht hier und wird über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Alle Instanzen kommen aus dem eigenen SplitMix64-Generator (plattform- und versionsunabhängig); Zähler und Mediane sind exakte Werte, Güten stehen als abgerundete Prozentzahlen (`fmt_quality`)."""

from fractions import Fraction

import pytest

import fpr_algorithm as A
import fpr_constants as C
import fpr_evaluation as ev
from fpr_scenario import make_instance

# --- Befund 1: die exakte Tabelle wächst mit den Stellen --------------------------------------------------------------------------------------------


def test_claim_cells_grow_by_a_factor_of_ten_per_digit_while_the_fptas_table_stays():
    """README (30 Pakete, unkorreliert, 5 feste Instanzen je Stelle, Median): exakte Tabelle bei 1 bis 9 Stellen; FPTAS-Tabelle konstant 74.580 (ε = 0,2) und 299.580 (ε = 0,05); billiger ab 3 bzw. 4 Stellen."""
    rows = ev.sweep_digits()
    assert [r["d"] for r in rows] == list(range(1, 10)) and all(r["count"] == 5 for r in rows)
    assert [r["exact"] for r in rows] == [2040, 18630, 184920, 1654920, 17510040, 183110040, 1575110040, 17737357410, 170632667430]
    assert all(r["fptas"] == {0.2: 74580, 0.05: 299580} for r in rows)
    assert (ev.cheaper_from(rows, 0.2), ev.cheaper_from(rows, 0.05)) == (3, 4)
    assert "Faktor 9,8 je Stelle" in ev.verdict_digits(rows)[1]
    assert round(rows[-1]["exact"] / rows[0]["exact"]) == 83_643_464                           # 170.632.667.430 / 2.040: das 83,6-Millionen-Fache bei 9-mal so vielen Stellen


def test_claim_the_cell_formula_holds_on_real_runs_up_to_six_digits():
    """README: die Zellenformel n · (W + 1) ist an echten Läufen bestätigt (alle fünf Instanzen bis 4 Stellen, je eine bei 5 und 6 Stellen)."""
    for d in range(1, 7):
        for seed in (C.E1_SEEDS if d <= 4 else C.E1_SEEDS[:1]):
            inst = make_instance(30, d, "unc", seed)
            assert A.capacity_dp(inst.weights, inst.values, inst.capacity).cells == A.knapsack_cells(30, inst.capacity)


# --- Befund 2: Güte gegen Garantie -------------------------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def eps_rows():
    return ev.sweep_eps(30, "unc")


def test_claim_quality_over_epsilon(eps_rows):
    """README (30 Pakete, unkorreliert, Gewichte bis 1.000, 40 feste Instanzen): kleinste Güte, Median, exakt optimal, FPTAS-Zellen und exakte Zellen je ε."""
    assert [r["eps"] for r in eps_rows] == [0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01] and all(r["count"] == 40 for r in eps_rows)
    assert [ev.fmt_quality(r["min"]) for r in eps_rows] == ["99,8 %", "99,9 %", "99,9 %", "99,9 %", "99,9 %", "100 %", "100 %"]
    assert [ev.fmt_quality(r["median"]) for r in eps_rows] == ["100 %"] * 7
    assert [r["exact_hits"] for r in eps_rows] == [33, 37, 36, 38, 39, 40, 40]
    assert [r["cells_fptas"] for r in eps_rows] == [28095, 47025, 70875, 142110, 284505, 711960, 1424355]
    assert all(r["cells_exact"] == 179310 for r in eps_rows)
    assert all(r["violations"] == 0 for r in eps_rows)
    assert min(r["min"] for r in eps_rows) == Fraction(2793, 2797)                           # die kleinste Güte aller 280 Läufe, bei ε = 0,5


def test_claim_the_fptas_pays_off_only_for_coarse_epsilon_at_three_digits(eps_rows):
    """README: bei Gewichten bis 1.000 ist die FPTAS-Tabelle ab ε = 0,1 kleiner als die exakte (142.110 gegen 179.310), bei ε = 0,05 größer (284.505)."""
    cheaper = {r["eps"]: r["cells_fptas"] < r["cells_exact"] for r in eps_rows}
    assert cheaper == {0.5: True, 0.3: True, 0.2: True, 0.1: True, 0.05: False, 0.02: False, 0.01: False}


def test_claim_families():
    """README: kleinste / mittlere Güte je Familie bei ε = 0,5 / 0,2 / 0,1 (40 feste Instanzen, 30 Pakete)."""
    got = {(r["family"], r["eps"]): (ev.fmt_quality(r["min"]), ev.fmt_quality(r["median"])) for r in ev.sweep_families(30)}
    assert got == {
        ("unc", 0.5): ("99,8 %", "100 %"), ("unc", 0.2): ("99,9 %", "100 %"), ("unc", 0.1): ("99,9 %", "100 %"),
        ("cor", 0.5): ("99,8 %", "99,9 %"), ("cor", 0.2): ("99,8 %", "99,9 %"), ("cor", 0.1): ("99,9 %", "100 %"),
        ("sub", 0.5): ("99,6 %", "99,8 %"), ("sub", 0.2): ("99,8 %", "99,9 %"), ("sub", 0.1): ("99,9 %", "99,9 %"),
    }


# --- Befund 3: die Falle -----------------------------------------------------------------------------------------------------------------------

TRAP = {
    10: ["71,4 %", "81,3 %", "86,2 %", "92,5 %", "96,1 %", "98,4 %", "99,2 %"],
    30: ["68,1 %", "78,1 %", "84,2 %", "91,4 %", "95,5 %", "98,1 %", "99,0 %"],
    50: ["67,5 %", "77,8 %", "83,8 %", "91,2 %", "95,4 %", "98,1 %", "99,0 %"],
}


def test_claim_trap_quality():
    """README: Güte der Falle bei ε = 0,5 / 0,3 / 0,2 / 0,1 / 0,05 / 0,02 / 0,01 für n = 10, 30, 50; das FPTAS wählt immer das große Paket (Wert 1.000.000)."""
    rows = ev.sweep_trap()
    for n, expected in TRAP.items():
        mine = [r for r in rows if r["n"] == n]
        assert [ev.fmt_quality(r["quality"]) for r in mine] == expected, n
        assert all(r["fptas_value"] == 1_000_000 for r in mine)
    worst = min(rows, key=lambda r: r["quality"])
    assert (worst["n"], worst["eps"], ev.fmt_quality(worst["quality"])) == (50, 0.5, "67,5 %")
    assert all(r["quality"] >= 1 - A.to_fraction(r["eps"]) for r in rows)


def test_claim_trap_values_for_30_packages():
    """README: Falle mit 30 Paketen und ε = 0,2: FPTAS 1.000.000, Optimum 1.186.639 (29 kleine Pakete); ε = 0,5 und n = 10: Optimum 1.399.991."""
    t = ev.analyse_trap(30, 0.2)
    assert (t.fptas_value, t.opt_value) == (1_000_000, 1_186_639)
    assert t.opt_value == sum(A.trap_instance(30, 0.2)[1][1:]) and t.small_value == 39_999     # Summe der 29 kleinen Werte, kleinster kleiner Wert 39.999
    assert ev.analyse_trap(10, 0.5).opt_value == 1_399_991


# --- Befund 4: Zustandsräume --------------------------------------------------------------------------------------------------------------------

BINS_FIXED = {
    (2, 10): (43, 47), (2, 20): (80, 98), (2, 40): (159, 166), (2, 80): (310, 325),
    (3, 10): (462, 523), (3, 20): (1483, 2249), (3, 40): (5720, 6172), (3, 80): (21883, 24074),
    (4, 10): (2727, 3103), (4, 20): (15496, 25215), (4, 40): (115980, 123922), (4, 80): (810333, 936131),
}
PLANT = {2: (5, 5, 8), 3: (49, 31, 52), 4: (390, 192, 684), 5: (5624, 2310, 8217), 6: (46182, 16161, 190771), 7: (802653, 282709, 1314516)}


def test_claim_state_space_with_a_fixed_number_of_bins():
    """README (30 Zahlen aus 1 bis B, Obergrenze ⌈Summe / m⌉, 5 feste Verteilungen, Median und Maximum der Zustandsspitze): m = 2, 3, 4 und B = 10, 20, 40, 80."""
    rows = ev.sweep_bins_fixed()
    assert {(r["m"], r["b"]): (r["peak"], r["max"]) for r in rows} == BINS_FIXED
    text = ev.verdict_bins_fixed(rows)[1]
    assert "m = 2: von B = 10 auf 80 wächst die Spitze von 43 auf 310 Zustände, im Mittel um den Faktor 1,9 je Verdopplung von B" in text
    assert "m = 3: von B = 10 auf 80 wächst die Spitze von 462 auf 21.883 Zustände, im Mittel um den Faktor 3,6 je Verdopplung von B" in text
    assert "m = 4: von B = 10 auf 80 wächst die Spitze von 2.727 auf 810.333 Zustände, im Mittel um den Faktor 6,7 je Verdopplung von B" in text


def test_claim_state_space_of_planted_three_partition():
    """README (B = 100, 3m Zahlen zwischen 25 und 50, 5 feste Instanzen je m): Median, kleinster und größter Wert der Zustandsspitze für m = 2 bis 7; alle 30 Instanzen lösbar, keine abgebrochen."""
    rows = ev.sweep_plant()
    assert {r["m"]: (r["peak"], r["min"], r["max"]) for r in rows} == PLANT
    assert all(r["solvable"] == 5 and r["aborted"] == 0 for r in rows)
    text = ev.verdict_plant(rows)[1]
    assert "von 5 (m = 2) auf 802.653 Zustände (m = 7)" in text and "Faktor 8,0 bis 17,4" in text and "Alle 30 von 30" in text
    factors = [rows[i + 1]["peak"] / rows[i]["peak"] for i in range(len(rows) - 1)]
    assert [round(f, 1) for f in factors] == [9.8, 8.0, 14.4, 8.2, 17.4]


# --- Presets (Einzelinstanzen) --------------------------------------------------------------------------------------------------------------------


def test_claim_presets_are_single_instances_with_these_values():
    """README, Preset-Tabelle: Optimum, Wert des FPTAS, Güte, Zellen exakt, Zellen FPTAS, Kapazität je Preset."""
    got = {}
    for name, p in C.PRESETS.items():
        a = ev.analyse(ev.Settings(**p))
        got[name] = (a.exact.value, a.fptas.value, ev.fmt_quality(a.quality), a.exact.cells, a.fptas.cells, a.instance.capacity)
    assert got == {
        "Standardfall (Voreinstellung)": (10631, 10631, "100 %", 199470, 67590, 6648),
        "Lehrbeispiel (8 Pakete)": (2257, 2257, "100 %", 136, 872, 16),
        "Viele Stellen (Gewichte bis 10^6)": (11211, 11211, "100 %", 190843470, 67590, 6361448),
        "Grobes ε (0,5)": (10631, 10631, "100 %", 199470, 26820, 6648),
        "Feines ε (0,01)": (10631, 10631, "100 %", 199470, 1359150, 6648),
        "Teilsumme (Wert = Gewicht)": (6648, 6642, "99,9 %", 199470, 75810, 6648),
        "Stark korreliert": (8348, 8342, "99,9 %", 199470, 81210, 6648),
    }


def test_claim_the_maximum_instance():
    """README: n = 50 mit Gewichten bis 10^6 (Zufalls-Seed 35, unkorreliert) hat eine Tabelle von 541.066.000 Zellen (Optimum 19.709), die FPTAS-Tabelle bei ε = 0,2 hat 330.750."""
    a = ev.analyse(ev.Settings(n=50, d=6))
    assert (a.exact.cells, a.exact.value, a.fptas.cells, a.fptas.value) == (541_066_000, 19709, 330_750, 19709)
    assert a.exact.chosen is None                                                              # über der Grenze für die gewählte Menge


def test_claim_presets_of_the_bins_section():
    """README: Standardverteilung (30 Zahlen aus 1 bis 20, 3 Behälter, Obergrenze 107): höchstens 1.316 Zustände, lösbar; das Lehrbeispiel (2 Behälter, 1 bis 10): 39."""
    s = ev.analyse(ev.Settings()).bins
    assert (s.cap, sum(s.items), s.states.peak, s.states.total, s.states.solvable) == (107, 321, 1316, 15673, True)
    assert ev.analyse(ev.Settings(**C.PRESETS["Lehrbeispiel (8 Pakete)"])).bins.states.peak == 39


def test_claim_unit_is_cells_and_states_never_seconds():
    """README: Aufwand in Tabellenzellen und Zuständen, nie in Sekunden."""
    a = ev.analyse(ev.Settings())
    for text in (ev.verdict_run(a)[1], ev.verdict_trap(a.trap)[1], ev.verdict_bins_live(a.bins, 3, 20)[1]):
        assert "Sekunden" not in text
    assert "Zellen" in ev.verdict_run(a)[1] and "Zustände" in ev.verdict_bins_live(a.bins, 3, 20)[1]
