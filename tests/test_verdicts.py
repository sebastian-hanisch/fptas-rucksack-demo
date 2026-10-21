"""Verdikte und Zahlenformate an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds. Damit prüft der Test die Grenzen und jede genannte Zahl direkt."""

from fractions import Fraction

import pytest

import fpr_algorithm as A
import fpr_constants as C
import fpr_evaluation as ev
from fpr_scenario import Instance


def _analysis(exact_value, exact_cells, fptas_value, fptas_cells, eps=0.2):
    inst = Instance((1,), (1,), 1)
    trap = ev.TrapResult(10, eps, 1000, 1250, 10)
    bins = ev.BinResult((1, 2, 3), 3, A.BinStates((1, 2, 1), 2, 4, 1, True, False))
    return ev.Analysis(ev.Settings(eps=eps), inst, A.DpResult(exact_value, exact_cells, None), A.FptasResult(fptas_value, (), fptas_cells, Fraction(1), 1, 1), None, trap, bins)


# --- Formate ------------------------------------------------------------------------------------------------------------------------------


def test_number_formats():
    assert ev.fmt_int(1234567) == "1.234.567" and ev.fmt_int(12) == "12"
    assert ev.fmt_num(22.7) == "22,7" and ev.fmt_num(3, 2) == "3,00"
    assert ev.fmt_median(1234) == "1.234" and ev.fmt_median(52.5) == "52,5" and ev.fmt_median(Fraction(7, 2)) == "3,5"
    assert ev.fmt_percent(80.0) == "80" and ev.fmt_percent(2.5) == "2,5"
    assert ev.fmt_eps(0.05) == "0,05" and ev.fmt_eps(0.5) == "0,5"
    assert ev.fmt_factor(7.04) == "7,0" and ev.fmt_factor(99.9) == "99,9" and ev.fmt_factor(100) == "100" and ev.fmt_factor(1352.4) == "1.352"


def test_fmt_k():
    assert ev.fmt_k(Fraction(50, 3)) == "16,67" and ev.fmt_k(Fraction(1, 6)) == "0,1667" and ev.fmt_k(Fraction(6593, 1)) == "6.593" and ev.fmt_k(Fraction(1999, 2)) == "999,5" and ev.fmt_k(Fraction(1001)) == "1.001"
    assert ev.fmt_k(Fraction(0)) == "0"


def test_quality_is_rounded_down_and_only_exact_is_one_hundred_percent():
    assert ev.fmt_quality(Fraction(1)) == "100 %"
    assert ev.fmt_quality(Fraction(999, 1000)) == "99,9 %"
    assert ev.fmt_quality(Fraction(9996, 10000)) == "99,9 %"      # nicht „100 %“: abgerundet
    assert ev.fmt_quality(Fraction(1, 2)) == "50,0 %"


def test_loss_is_rounded_up_and_complements_the_quality():
    assert ev.fmt_loss(Fraction(4, 5)) == "20,0 %" and ev.fmt_loss(Fraction(1)) == "0,0 %"
    q = Fraction(1_000_000, 1_186_639)
    assert ev.fmt_quality(q) == "84,2 %" and ev.fmt_loss(q) == "15,8 %"


def test_guarantee_format():
    assert [ev.fmt_guarantee(e) for e in (0.5, 0.3, 0.2, 0.05, 0.01)] == ["50 %", "70 %", "80 %", "95 %", "99 %"]


# --- Verdikte -----------------------------------------------------------------------------------------------------------------------------


def test_verdict_run_success_when_the_fptas_table_is_smaller():
    kind, text = ev.verdict_run(_analysis(200, 1000, 199, 250))
    assert kind == "success"
    assert "199 von 200" in text and "99,5 %" in text and "mindestens 80 %" in text and "250 statt 1.000" in text and "Faktor 4,0" in text and "ε = 0,2" in text


def test_verdict_run_info_when_the_exact_table_is_not_larger():
    kind, text = ev.verdict_run(_analysis(200, 250, 200, 250))               # gleich große Tabellen: nicht „billiger“
    assert kind == "info" and "100 %" in text and "exakte Rechnung billiger" in text
    assert ev.verdict_run(_analysis(200, 100, 200, 250))[0] == "info"


def test_verdict_run_without_value():
    kind, text = ev.verdict_run(_analysis(0, 10, 0, 0))
    assert kind == "info" and "Kein Paket" in text


def test_verdict_trap_names_both_values_quality_and_allowed_loss():
    kind, text = ev.verdict_trap(ev.TrapResult(10, 0.5, 1000, 1250, 100))
    assert kind == "warning"
    assert "10 Pakete, ε = 0,5" in text and "Wert 1.000" in text and "9 kleinen Pakete (Wert 1.250)" in text
    assert "Die Güte ist 80,0 %" in text and "mindestens 50 %" in text and "Verlust von 20,0 %" in text and "erlaubten 50 %" in text


DIGIT_ROWS = [{"d": d, "count": 5, "exact": 10 ** (d + 2), "fptas": {0.2: 100, 0.05: 400}} for d in (1, 2, 3)]


def test_verdict_digits_names_growth_and_crossing():
    kind, text = ev.verdict_digits(DIGIT_ROWS)
    assert kind == "info"
    assert "Von 1 Stelle (1.000 Zellen) bis 3 Stellen (100.000 Zellen)" in text and "Faktor 10,0 je Stelle" in text
    assert "bei ε = 0,2 bei 100 Zellen und ist ab 1 Stelle billiger" in text
    assert "bei ε = 0,05 bei 400 Zellen und ist ab 1 Stelle billiger" in text


def test_verdict_digits_range_and_never_cheaper():
    rows = [{"d": 1, "count": 5, "exact": 100, "fptas": {0.2: 500}}, {"d": 2, "count": 5, "exact": 1000, "fptas": {0.2: 800}}, {"d": 3, "count": 5, "exact": 10000, "fptas": {0.2: 600}}]
    text = ev.verdict_digits(rows)[1]
    assert "zwischen 500 und 800 Zellen" in text and "ab 2 Stellen billiger" in text
    rows[-1]["fptas"][0.2] = 20000
    assert "in der Messreihe nie billiger" in ev.verdict_digits(rows)[1]


def test_cheaper_from_needs_the_advantage_for_all_larger_sizes():
    rows = [{"d": 1, "exact": 400, "fptas": {0.2: 500}}, {"d": 2, "exact": 4000, "fptas": {0.2: 600}}, {"d": 3, "exact": 500, "fptas": {0.2: 600}}, {"d": 4, "exact": 5000, "fptas": {0.2: 600}}]
    assert ev.cheaper_from(rows, 0.2) == 4                       # bei 3 Stellen ist es wieder teurer: erst ab 4 dauerhaft billiger
    assert ev.cheaper_from(rows[:2], 0.2) == 2
    assert ev.cheaper_from(rows[:1], 0.2) is None


EPS_ROWS = [
    {"eps": 0.5, "count": 40, "min": Fraction(998, 1000), "median": Fraction(1), "exact_hits": 33, "violations": 0, "cells_fptas": 10, "cells_exact": 20},
    {"eps": 0.1, "count": 40, "min": Fraction(999, 1000), "median": Fraction(1), "exact_hits": 38, "violations": 0, "cells_fptas": 30, "cells_exact": 20},
]


def test_verdict_eps_success_names_worst_case_and_median():
    kind, text = ev.verdict_eps(EPS_ROWS)
    assert kind == "success"
    assert "In allen 80 Läufen" in text and "99,8 % (bei ε = 0,5, garantiert 50 %)" in text
    assert "bei ε = 0,5 lag sie im Median bei 100 % statt der garantierten 50 %" in text and "33 von 40 Läufen waren exakt optimal" in text


def test_verdict_eps_reports_a_violated_guarantee_as_error():
    rows = [dict(EPS_ROWS[0], violations=2), dict(EPS_ROWS[1], violations=1)]
    kind, text = ev.verdict_eps(rows)
    assert kind == "error" and "3 von 80" in text


def test_verdict_families():
    rows = [{"family": "unc", "eps": 0.5, "min": Fraction(99, 100), "median": Fraction(1), "violations": 0, "count": 40},
            {"family": "sub", "eps": 0.2, "min": Fraction(97, 100), "median": Fraction(98, 100), "violations": 0, "count": 40}]
    kind, text = ev.verdict_families(rows)
    assert kind == "info" and "97,0 % (Teilsumme (Wert = Gewicht), ε = 0,2, garantiert 80 %)" in text
    assert ev.verdict_families([dict(rows[0], violations=4)])[0] == "error"


def test_verdict_trap_sweep_names_worst_and_best():
    rows = [{"n": 10, "eps": 0.5, "quality": Fraction(3, 4)}, {"n": 50, "eps": 0.5, "quality": Fraction(2, 3)}, {"n": 10, "eps": 0.01, "quality": Fraction(99, 100)}]
    kind, text = ev.verdict_trap_sweep(rows)
    assert kind == "warning"
    assert "bis auf 66,6 % (n = 50, ε = 0,5, garantiert 50 %)" in text and "bei ε = 0,01 und n = 10 bleibt sie bei 99,0 %" in text
    assert "bleibt aber über der Garantie" in text


def test_verdict_bins_live_branches():
    states = A.BinStates((1, 2, 1), 2, 4, 1, True, False)
    kind, text = ev.verdict_bins_live(ev.BinResult((1, 2, 3), 3, states), 2, 20)
    assert kind == "info" and "Es gibt eine Verteilung der 3 Zahlen (1 bis 20, Summe 6) auf 2 Behälter mit höchstens 3 je Behälter" in text
    assert "höchstens 2 Zustände" in text and "insgesamt 4" in text
    no = A.BinStates((1, 0), 1, 1, 0, False, False)
    assert "Es gibt keine Verteilung" in ev.verdict_bins_live(ev.BinResult((1, 2, 3), 3, no), 2, 20)[1]
    aborted = A.BinStates((9, 2_000_000), 2_000_000, 2_000_009, 0, False, True)
    kind, text = ev.verdict_bins_live(ev.BinResult((1, 2, 3), 3, aborted), 2, 20)
    assert kind == "warning" and "Abbruch" in text and "1.500.000" in text and "mindestens 2.000.000" in text


def test_verdict_bins_fixed_names_growth_per_doubling():
    rows = [{"m": 2, "b": 10, "count": 5, "peak": 40, "max": 50}, {"m": 2, "b": 20, "count": 5, "peak": 80, "max": 90}, {"m": 2, "b": 40, "count": 5, "peak": 160, "max": 170}, {"m": 2, "b": 80, "count": 5, "peak": 320, "max": 330},
            {"m": 3, "b": 10, "count": 5, "peak": 100, "max": 110}, {"m": 3, "b": 80, "count": 5, "peak": 6400, "max": 6500}]
    kind, text = ev.verdict_bins_fixed(rows)
    assert kind == "info"
    assert "m = 2: von B = 10 auf 80 wächst die Spitze von 40 auf 320 Zustände, im Mittel um den Faktor 2,0 je Verdopplung von B" in text
    assert "m = 3: von B = 10 auf 80 wächst die Spitze von 100 auf 6.400 Zustände, im Mittel um den Faktor 4,0 je Verdopplung von B" in text


def test_verdict_plant_names_range_factors_and_solvability():
    rows = [{"m": 2, "count": 5, "peak": 5, "min": 4, "max": 8, "solvable": 5, "aborted": 0}, {"m": 3, "count": 5, "peak": 50, "min": 40, "max": 60, "solvable": 5, "aborted": 0},
            {"m": 4, "count": 5, "peak": 400, "min": 300, "max": 500, "solvable": 5, "aborted": 0}]
    kind, text = ev.verdict_plant(rows)
    assert kind == "warning"
    assert "von 5 (m = 2) auf 400 Zustände (m = 4)" in text and "Faktor 8,0 bis 10,0" in text and "Alle 15 von 15" in text and "brachen" not in text
    rows[1] = dict(rows[1], aborted=2)
    assert "2 Läufe brachen an der Zustandsgrenze ab" in ev.verdict_plant(rows)[1]


@pytest.mark.parametrize("name", ["verdict_run", "verdict_trap"])
def test_verdicts_are_pure_and_return_kind_and_text(name):
    a = _analysis(200, 1000, 199, 250)
    arg = a.trap if name == "verdict_trap" else a
    first = getattr(ev, name)(arg)
    assert first == getattr(ev, name)(arg)
    assert first[0] in ("success", "info", "warning", "error") and isinstance(first[1], str)
    assert C.PLANT_B == 100                                         # der Text der 3-Partition-Messreihe nennt „zwischen 25 und 50“ (B / 4 und B / 2)
