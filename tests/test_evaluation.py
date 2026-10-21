"""Auswertung: Einzelanalyse, Prüfungen vor der Anzeige (jede Fehlermeldung hat einen Test) und die Messreihen an kleinen Konfigurationen."""

from dataclasses import replace
from fractions import Fraction
from statistics import median

import fpr_algorithm as A
import fpr_constants as C
import fpr_evaluation as ev
from fpr_scenario import make_instance


def test_default_analysis_is_consistent():
    a = ev.analyse(ev.Settings())
    assert not ev.validation_errors(a)
    inst = a.instance
    assert inst == make_instance(C.DEFAULT_N, C.DEFAULT_D, C.DEFAULT_FAMILY, C.DEFAULT_SEED)
    assert a.exact.value == A.capacity_dp(inst.weights, inst.values, inst.capacity).value
    assert a.exact.chosen is not None and a.table is None                    # 30 Pakete, Gewichte bis 1000: Tabelle zu groß zum Zeichnen
    assert a.quality == Fraction(a.fptas.value, a.exact.value)
    assert a.trap == ev.analyse_trap(C.DEFAULT_N, C.DEFAULT_EPS)
    assert a.bins == ev.analyse_bins(C.DEFAULT_BINS, C.DEFAULT_BMAX, C.DEFAULT_SEED)


def test_small_instance_has_the_full_table_and_a_large_one_has_no_choice():
    small = ev.analyse(ev.Settings(n=8, d=1, seed=3))
    assert small.table is not None and small.table[-1][small.instance.capacity] == small.exact.value
    assert len(small.table) == 9
    big = ev.analyse(ev.Settings(n=20, d=6))
    assert big.exact.cells > C.CHOICE_LIMIT and big.exact.chosen is None and big.exact.value > 0


def test_quality_is_one_when_the_optimum_is_zero():
    inst = make_instance(5, 1, "unc", 1)
    a = ev.Analysis(ev.Settings(), inst, A.DpResult(0, 1, None), A.FptasResult(0, (), 0, Fraction(0), 0, 0), None, ev.analyse_trap(5, 0.5), ev.analyse_bins(2, 10, 1))
    assert a.quality == 1


def test_brute_force_value_hand_case(mini):
    weights, values, capacity = mini
    assert ev.brute_force_value(weights, values, capacity) == 7


def test_bin_numbers_and_cap():
    items = ev.bin_numbers(5, 20)
    assert len(items) == C.BIN_NUMBERS_N and all(1 <= x <= 20 for x in items) and items == ev.bin_numbers(5, 20) != ev.bin_numbers(6, 20)
    r = ev.analyse_bins(3, 20, 5)
    assert r.cap == -(-sum(r.items) // 3) and r.states == A.bin_dp_states(list(r.items), 3, r.cap)


# --- Prüfungen vor der Anzeige: jede Meldung wird ausgelöst ---------------------------------------------------------------------------------------


def _base():
    return ev.analyse(ev.Settings(n=8, d=1, seed=3))


def test_validation_is_clean_for_untouched_results():
    assert ev.validation_errors(_base()) == []


def test_validation_flags_an_infeasible_exact_choice():
    a = _base()
    wrong = replace(a, exact=replace(a.exact, chosen=tuple(range(a.instance.n))))
    assert any("exakten Rechnung ist unzulässig" in e for e in ev.validation_errors(wrong))


def test_validation_flags_a_fptas_choice_that_does_not_match_its_value():
    a = _base()
    wrong = replace(a, fptas=replace(a.fptas, value=a.fptas.value - 1))
    assert any("Menge des FPTAS ist unzulässig oder passt nicht zum Wert" in e for e in ev.validation_errors(wrong))


def test_validation_flags_a_fptas_above_the_optimum_and_a_violated_guarantee():
    a = _base()
    above = replace(a, exact=replace(a.exact, value=a.fptas.value - 1))
    assert any("mehr als das Optimum" in e for e in ev.validation_errors(above))
    below = replace(a, exact=replace(a.exact, value=a.fptas.value * 10))
    assert any("Güte-Garantie des FPTAS ist verletzt" in e for e in ev.validation_errors(below))


def test_validation_flags_a_wrong_cell_count_and_a_wrong_table():
    a = _base()
    assert any("Zellenzahl" in e for e in ev.validation_errors(replace(a, exact=replace(a.exact, cells=a.exact.cells + 1))))
    bad_table = tuple(tuple(row) for row in a.table[:-1]) + (tuple(0 for _ in a.table[-1]),)
    assert any("ganze Tabelle widerspricht" in e for e in ev.validation_errors(replace(a, table=bad_table)))


def test_validation_flags_a_wrong_brute_force_value():
    a = _base()
    wrong = replace(a, exact=replace(a.exact, value=a.exact.value + 1, chosen=None), table=None)
    assert any("Brute-Force-Probe" in e for e in ev.validation_errors(wrong))


def test_validation_flags_a_broken_trap_and_an_inconsistent_bin_result():
    a = _base()
    bad_trap = replace(a, trap=replace(a.trap, fptas_value=a.trap.opt_value + 1))
    assert any("Falle verletzt" in e for e in ev.validation_errors(bad_trap))
    worse = replace(a, trap=replace(a.trap, fptas_value=1))
    assert any("Falle verletzt" in e for e in ev.validation_errors(worse))
    st = a.bins.states
    bad_bins = replace(a, bins=replace(a.bins, states=replace(st, solvable=not st.solvable)))
    assert any("Lösbarkeit" in e for e in ev.validation_errors(bad_bins))


# --- Messreihen ---------------------------------------------------------------------------------------------------------------------------


def test_sweep_digits_uses_the_formula_and_real_fptas_runs():
    rows = ev.sweep_digits(n=6, seeds=(1, 2, 3), digits=(1, 2, 3), eps_list=(0.5, 0.2))
    assert [r["d"] for r in rows] == [1, 2, 3] and all(r["count"] == 3 for r in rows)
    for r in rows:
        insts = [make_instance(6, r["d"], "unc", s) for s in (1, 2, 3)]
        assert r["exact"] == median(A.knapsack_cells(6, i.capacity) for i in insts)
        for e in (0.5, 0.2):
            assert r["fptas"][e] == median(A.fptas(i.weights, i.values, i.capacity, e).cells for i in insts)
    assert rows[0]["exact"] < rows[1]["exact"] < rows[2]["exact"]


def test_cheaper_from_on_real_rows_finds_a_crossing():
    rows = ev.sweep_digits(n=10, seeds=(1, 2), digits=(1, 2, 3, 4, 5), eps_list=(0.5,))
    d = ev.cheaper_from(rows, 0.5)
    assert d is not None and all(r["fptas"][0.5] < r["exact"] for r in rows if r["d"] >= d)


def test_sweep_eps_on_a_small_configuration():
    seeds = (11, 12, 13, 14)
    rows = ev.sweep_eps(8, "unc", seeds=seeds, digits=2, eps_list=(0.5, 0.1))
    assert [r["eps"] for r in rows] == [0.5, 0.1]
    insts = [make_instance(8, 2, "unc", s) for s in seeds]
    opts = [A.capacity_dp(i.weights, i.values, i.capacity) for i in insts]
    for r in rows:
        qs = [Fraction(A.fptas(i.weights, i.values, i.capacity, r["eps"]).value, o.value) for i, o in zip(insts, opts)]
        assert r["count"] == 4 and r["min"] == min(qs) and r["median"] == median(qs) and r["violations"] == 0
        assert r["exact_hits"] == sum(q == 1 for q in qs)
        assert r["cells_exact"] == median(o.cells for o in opts)
        assert 1 - A.to_fraction(r["eps"]) <= r["min"] <= r["median"] <= 1


def test_sweep_eps_counts_violations_against_the_guarantee(monkeypatch):
    """Ein kaputtes FPTAS (nimmt nichts) verletzt die Garantie: die Messreihe zählt es."""
    monkeypatch.setattr(ev.A, "fptas", lambda w, v, c, e: A.FptasResult(0, (), 0, Fraction(0), 0, 0))
    rows = ev.sweep_eps(6, "unc", seeds=(1, 2), digits=1, eps_list=(0.5,))
    assert rows[0]["violations"] == 2 and rows[0]["exact_hits"] == 0


def test_sweep_families_has_one_row_per_family_and_eps():
    rows = ev.sweep_families(8, eps_list=(0.5, 0.2), seeds=(1, 2, 3), digits=2)
    assert [(r["family"], r["eps"]) for r in rows] == [(f, e) for f in C.FAMILIES for e in (0.5, 0.2)]
    assert all(r["count"] == 3 and r["violations"] == 0 and r["min"] <= r["median"] <= 1 for r in rows)


def test_sweep_trap_matches_the_single_analysis():
    rows = ev.sweep_trap(sizes=(10, 20), eps_list=(0.5, 0.1))
    assert [(r["n"], r["eps"]) for r in rows] == [(10, 0.5), (10, 0.1), (20, 0.5), (20, 0.1)]
    for r in rows:
        t = ev.analyse_trap(r["n"], r["eps"])
        assert r["quality"] == Fraction(t.fptas_value, t.opt_value) < 1 and r["fptas_value"] == t.fptas_value and r["opt_value"] == t.opt_value


def test_sweep_bins_fixed_matches_direct_runs():
    rows = ev.sweep_bins_fixed(counts=(2, 3), bounds=(10, 20), seeds=(1, 2, 3))
    assert [(r["m"], r["b"]) for r in rows] == [(2, 10), (2, 20), (3, 10), (3, 20)]
    for r in rows:
        peaks = [ev.analyse_bins(r["m"], r["b"], s).states.peak for s in (1, 2, 3)]
        assert r["peak"] == median(peaks) and r["max"] == max(peaks) and r["count"] == 3


def test_sweep_plant_matches_direct_runs_and_all_instances_are_solvable():
    rows = ev.sweep_plant(counts=(2, 3, 4), seeds=(40, 41, 42))
    for r in rows:
        runs = [A.bin_dp_states(A.planted_three_partition(r["m"], 100, s), r["m"], 100) for s in (40, 41, 42)]
        assert r["peak"] == median(x.peak for x in runs) and r["min"] == min(x.peak for x in runs) and r["max"] == max(x.peak for x in runs)
        assert r["solvable"] == 3 and r["aborted"] == 0
    assert rows[0]["peak"] < rows[1]["peak"] < rows[2]["peak"]


# --- Lücken aus der Mutationsprüfung: Grenzen, an denen die Auswertung umschaltet ---------------------------------------------------------------


def test_choice_limit_is_inclusive(monkeypatch):
    cells = ev.analyse(ev.Settings(n=8, d=1, seed=3)).exact.cells
    monkeypatch.setattr(C, "CHOICE_LIMIT", cells)
    assert ev.analyse(ev.Settings(n=8, d=1, seed=3)).exact.chosen is not None
    monkeypatch.setattr(C, "CHOICE_LIMIT", cells - 1)
    assert ev.analyse(ev.Settings(n=8, d=1, seed=3)).exact.chosen is None


def test_table_limit_is_inclusive_and_counts_n_plus_one_rows(monkeypatch):
    a = ev.analyse(ev.Settings(n=8, d=1, seed=3))
    fields = (a.instance.n + 1) * (a.instance.capacity + 1)                 # 9 Zeilen (inklusive Start) mal Kapazität + 1 Spalten
    monkeypatch.setattr(C, "TABLE_LIMIT", fields)
    assert ev.analyse(ev.Settings(n=8, d=1, seed=3)).table is not None
    monkeypatch.setattr(C, "TABLE_LIMIT", fields - 1)
    assert ev.analyse(ev.Settings(n=8, d=1, seed=3)).table is None


def test_brute_force_uses_the_last_item():
    assert ev.brute_force_value([1, 1], [1, 5], 1) == 5
    assert ev.brute_force_value([1, 1, 1], [1, 1, 9], 1) == 9
    assert ev.brute_force_value([1, 1], [5, 5], 2) == 10                    # nur die Auswahl aller Pakete (letzte Maske) ist optimal


def test_fmt_k_switches_to_thousands_exactly_at_1000():
    assert ev.fmt_k(Fraction(1000)) == "1.000" and ev.fmt_k(Fraction(999)) == "999"


def test_fmt_loss_of_a_total_loss():
    assert ev.fmt_loss(Fraction(0)) == "100,0 %"


def test_sweep_eps_counts_only_strict_violations(monkeypatch):
    """Güte genau 1 - ε ist erlaubt (Garantie „mindestens“)."""
    monkeypatch.setattr(ev.A, "capacity_dp", lambda w, v, c, want_choice=False: A.DpResult(10, 1, None))
    monkeypatch.setattr(ev.A, "fptas", lambda w, v, c, e: A.FptasResult(5, (), 1, Fraction(0), 1, 1))
    rows = ev.sweep_eps(5, "unc", seeds=(1,), digits=1, eps_list=(0.5,))
    assert rows[0]["violations"] == 0 and rows[0]["min"] == Fraction(1, 2)
    monkeypatch.setattr(ev.A, "fptas", lambda w, v, c, e: A.FptasResult(4, (), 1, Fraction(0), 1, 1))
    assert ev.sweep_eps(5, "unc", seeds=(1,), digits=1, eps_list=(0.5,))[0]["violations"] == 1


def test_validation_flags_each_exact_choice_problem_separately():
    a = _base()
    over = tuple(range(a.instance.n))
    infeasible_same_value = replace(a, exact=replace(a.exact, chosen=over, value=A.value_of(a.instance.values, over)))
    assert any("exakten Rechnung ist unzulässig" in e for e in ev.validation_errors(infeasible_same_value))
    feasible_wrong_value = replace(a, exact=replace(a.exact, chosen=(), value=a.exact.value))
    assert any("exakten Rechnung ist unzulässig" in e for e in ev.validation_errors(feasible_wrong_value))


def test_validation_allows_a_quality_of_exactly_one_minus_epsilon():
    a = ev.analyse(ev.Settings(n=8, d=1, seed=3, eps=0.5))
    tight = replace(a, exact=replace(a.exact, value=2 * a.fptas.value, chosen=None, cells=a.exact.cells), table=None)
    assert not any("Güte-Garantie" in e for e in ev.validation_errors(tight))


def test_brute_force_probe_runs_up_to_twelve_items_and_not_beyond():
    for n, expected in ((12, True), (13, False)):
        a = ev.analyse(ev.Settings(n=n, d=1, seed=3))
        wrong = replace(a, exact=replace(a.exact, value=a.exact.value + 1, chosen=None), table=None)
        assert any("Brute-Force-Probe" in e for e in ev.validation_errors(wrong)) is expected, n


def test_validation_trap_boundaries_are_allowed():
    a = _base()
    exactly_guaranteed = replace(a, trap=ev.TrapResult(10, 0.5, 500, 1000, 100))
    assert not any("Falle" in e for e in ev.validation_errors(exactly_guaranteed))
    no_loss = replace(a, trap=ev.TrapResult(10, 0.5, 1000, 1000, 100))
    assert not any("Falle" in e for e in ev.validation_errors(no_loss))


def test_validation_accepts_an_unsolvable_bin_result_with_no_final_state():
    a = _base()
    st = A.BinStates((1, 0), 1, 1, 0, False, False)
    assert not any("Lösbarkeit" in e for e in ev.validation_errors(replace(a, bins=replace(a.bins, states=st))))
