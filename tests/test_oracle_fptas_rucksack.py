"""Orakel-Tests: andere Rechenwege als die der Demo (ORACLE-PLAYBOOK, DEMO-PLAYBOOK §12).

- Exakte Rechnung (Tabelle über die Kapazität): Brute Force auf kleinen Instanzen, die Wert-Tabelle desselben Problems (andere Achse, ohne Rundung) und scipy.optimize.milp auf größeren.
- FPTAS: die Güte-Garantie 1 - ε als harte Prüfung auf Instanzen aller drei Familien und auf der Falle; die gewählte Menge ist zulässig (unabhängige Prüfung) und ihr Wert stimmt mit den Werten überein.
- Behälter-DP: vollständiges Aufzählen aller Verteilungen auf kleinen Instanzen (Zahl der verschiedenen Lastvektoren je Schritt, Lösbarkeit).
- Geplante 3-Partition: die Zerlegung in Dreiergruppen wird unabhängig aufgezählt."""

import itertools
from fractions import Fraction

import pytest

import fpr_algorithm as A
import fpr_constants as C
import fpr_evaluation as ev
from fpr_rng import SplitMix64
from fpr_scenario import capacity_for, make_instance


def brute_force_knapsack(weights, values, capacity):
    best = 0
    for mask in range(1 << len(weights)):
        w = v = 0
        for i in range(len(weights)):
            if mask >> i & 1:
                w += weights[i]
                v += values[i]
        if w <= capacity and v > best:
            best = v
    return best


def small_instances(count, n_max, seed0=0):
    for s in range(count):
        rng = SplitMix64(seed0 + s)
        n = 1 + rng.below(n_max)
        wmax = 1 + rng.below(12)
        w = [1 + rng.below(wmax) for _ in range(n)]
        v = [rng.below(30) for _ in range(n)]                   # Werte dürfen 0 sein
        yield w, v, rng.below(sum(w) + 3)                       # Kapazität auch größer als die Summe oder 0


def test_capacity_dp_matches_brute_force():
    for w, v, cap in small_instances(300, 10):
        r = A.capacity_dp(w, v, cap, want_choice=True)
        assert r.value == brute_force_knapsack(w, v, cap), (w, v, cap)
        assert A.is_feasible_choice(w, cap, r.chosen) and A.value_of(v, r.chosen) == r.value, (w, v, cap)


def test_capacity_dp_equals_the_value_table_without_rounding():
    """Zweiter Rechenweg: die Tabelle über die Gewinnsumme mit den echten Werten (keine Rundung) liefert denselben Optimalwert."""
    for w, v, cap in small_instances(300, 14, seed0=1000):
        fit = [i for i in range(len(w)) if w[i] <= cap]
        exact = A.capacity_dp(w, v, cap).value
        if not fit:
            assert exact == 0
            continue
        r = A.profit_dp([w[i] for i in fit], [v[i] for i in fit], cap)
        assert r.best == exact, (w, v, cap)
        assert sum(v[fit[j]] for j in r.chosen) == r.best


def test_capacity_table_last_cell_equals_the_dp_value():
    for w, v, cap in small_instances(100, 8, seed0=2000):
        table = A.capacity_table(w, v, cap)
        assert table[-1][cap] == A.capacity_dp(w, v, cap).value
        assert all(row[c] <= row[c + 1] for row in table for c in range(cap))      # in der Kapazität nicht fallend


def test_capacity_dp_matches_scipy_milp_on_larger_instances():
    np = pytest.importorskip("numpy")
    optimize = pytest.importorskip("scipy.optimize")
    for family in C.FAMILIES:
        for seed in range(12):
            inst = make_instance(25, 3, family, seed)
            res = optimize.milp(
                c=-np.array(inst.values, dtype=float),
                constraints=optimize.LinearConstraint(np.array([inst.weights], dtype=float), -np.inf, inst.capacity),
                integrality=np.ones(inst.n),
                bounds=optimize.Bounds(0, 1),
            )
            assert res.success
            assert A.capacity_dp(inst.weights, inst.values, inst.capacity).value == round(-res.fun), (family, seed)


# --- FPTAS: die Garantie als harte Prüfung -------------------------------------------------------------------------------------------------------


def _check_guarantee(weights, values, capacity, eps, label):
    opt = A.capacity_dp(weights, values, capacity).value
    f = A.fptas(weights, values, capacity, eps)
    assert A.is_feasible_choice(weights, capacity, f.chosen), label
    assert A.value_of(values, f.chosen) == f.value, label
    assert f.value <= opt, label
    # Güte >= 1 - ε, in exakter Bruchrechnung (kein Gleitkomma-Spielraum)
    assert f.value >= (1 - A.to_fraction(eps)) * opt, (label, f.value, opt)
    return f.value, opt


def test_fptas_guarantee_on_random_instances_of_all_families():
    count = 0
    for family in C.FAMILIES:
        for n in (3, 8, 20):
            for seed in range(7):
                inst = make_instance(n, 2, family, 5000 + seed)
                for eps in C.EPS_OPTIONS:
                    _check_guarantee(inst.weights, inst.values, inst.capacity, eps, (family, n, seed, eps))
                    count += 1
    assert count >= 300


def test_fptas_guarantee_on_small_random_instances_including_zero_values():
    for w, v, cap in small_instances(300, 9, seed0=3000):
        for eps in (0.5, 0.2, 0.05):
            _check_guarantee(w, v, cap, eps, (w, v, cap, eps))


def test_fptas_is_exact_for_tiny_epsilon_on_small_integer_values():
    """Mit K <= 1 ist p' = v: dann rechnet das FPTAS ohne Rundverlust und trifft das Optimum."""
    for w, v, cap in small_instances(100, 9, seed0=4000):
        if not v or max(v) == 0:
            continue
        n_fit = sum(1 for x in w if x <= cap)
        if n_fit == 0:
            continue
        eps = Fraction(n_fit, max(v[i] for i in range(len(w)) if w[i] <= cap))     # K = ε · vmax / n = 1
        assert A.fptas(w, v, cap, eps).value == A.capacity_dp(w, v, cap).value


def test_fptas_guarantee_on_the_trap_and_the_trap_really_loses():
    for n in (10, 20, 30, 40, 50):
        for eps in C.EPS_OPTIONS:
            w, v, cap = A.trap_instance(n, eps)
            value, opt = _check_guarantee(w, v, cap, eps, ("falle", n, eps))
            assert value == C.TRAP_BIG and opt == sum(v[1:]) and opt > value, (n, eps)      # die Falle greift


def test_fptas_cells_follow_the_formula():
    for family in C.FAMILIES:
        inst = make_instance(12, 3, family, 9)
        f = A.fptas(inst.weights, inst.values, inst.capacity, 0.2)
        assert f.cells == f.n_fit * (f.scaled_total + 1)
        # K · p' <= v < K · (p' + 1) für jedes Paket: die Rundung verliert weniger als K je Paket
        k, scaled = A.scale_values([inst.values[i] for i in range(inst.n) if inst.weights[i] <= inst.capacity], 0.2, max(inst.values[i] for i in range(inst.n) if inst.weights[i] <= inst.capacity), f.n_fit)
        vals = [inst.values[i] for i in range(inst.n) if inst.weights[i] <= inst.capacity]
        assert all(k * p <= v < k * (p + 1) for p, v in zip(scaled, vals))


def test_capacity_dp_cells_equal_the_formula_on_real_runs():
    for d in (1, 2, 3, 4):
        inst = make_instance(10, d, "unc", d)
        assert A.capacity_dp(inst.weights, inst.values, inst.capacity).cells == 10 * (inst.capacity + 1) == A.knapsack_cells(10, inst.capacity)


# --- Behälter-DP: vollständiges Aufzählen -------------------------------------------------------------------------------------------------------


def enumerated_states(items, m, cap):
    """Alle Verteilungen der ersten k Zahlen auf m Behälter aufzählen (m^k Zuweisungen), nur die mit Last <= cap; Menge der sortierten Lastvektoren je k."""
    per_step = []
    for k in range(1, len(items) + 1):
        states = set()
        for assignment in itertools.product(range(m), repeat=k):
            loads = [0] * m
            for item, b in zip(items, assignment):
                loads[b] += item
            if max(loads) <= cap:
                states.add(tuple(sorted(loads)))
        per_step.append(len(states))
    return per_step


def test_bin_dp_matches_full_enumeration():
    for s in range(40):
        rng = SplitMix64(7000 + s)
        m = 2 + rng.below(2)
        n = 3 + rng.below(4 if m == 3 else 6)
        items = [1 + rng.below(6) for _ in range(n)]
        cap = max(max(items), -(-sum(items) // m)) + rng.below(3)
        r = A.bin_dp_states(items, m, cap)
        expected = enumerated_states(items, m, cap)
        assert list(r.steps) == expected, (items, m, cap)
        assert r.final == expected[-1] and r.solvable == (expected[-1] > 0)
        assert r.peak == max([1] + expected) and r.total == sum(expected)


def triples_with_sum(items, big_b):
    """Gibt es eine Zerlegung in Dreiergruppen mit Summe B? (unabhängiges Aufzählen für m <= 3)"""
    idx = list(range(len(items)))
    def rec(rest):
        if not rest:
            return True
        first, others = rest[0], rest[1:]
        for pair in itertools.combinations(others, 2):
            if items[first] + items[pair[0]] + items[pair[1]] == big_b:
                if rec([i for i in others if i not in pair]):
                    return True
        return False
    return rec(idx)


@pytest.mark.parametrize("m", [2, 3])
def test_planted_instances_have_a_triple_decomposition(m):
    for seed in range(40, 60):
        items = A.planted_three_partition(m, 100, seed)
        assert A.is_three_partition_instance(items, 100)
        assert triples_with_sum(items, 100), (m, seed, items)
        assert A.bin_dp_states(items, m, 100).solvable


def test_bin_dp_unsolvable_agrees_with_triple_search_on_random_perturbations():
    for seed in range(60):
        items = A.planted_three_partition(3, 100, 100 + seed)
        items[0] += 1
        items[1] -= 1                                           # Summe bleibt, die Zerlegung ist (meist) weg
        assert A.bin_dp_states(items, 3, 100).solvable == triples_with_sum(items, 100), (seed, items)


# --- Szenario -----------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("family", list(C.FAMILIES))
@pytest.mark.parametrize("digits", [1, 3, 6])
def test_instances_follow_their_family_rules(family, digits):
    inst = make_instance(40, digits, family, 11)
    assert inst.n == 40 and len(inst.values) == 40
    assert all(1 <= w <= 10 ** digits for w in inst.weights)
    assert inst.capacity == capacity_for(inst.weights) == max(1, sum(inst.weights) * 2 // 5)
    if family == "sub":
        assert inst.values == inst.weights
    elif family == "cor":
        assert all(v == w + 10 ** digits // 10 for w, v in zip(inst.weights, inst.values))
    else:
        assert all(1 <= v <= C.VALUE_MAX for v in inst.values)


def test_instances_are_deterministic_and_differ_by_seed():
    assert make_instance(10, 3, "unc", 5) == make_instance(10, 3, "unc", 5)
    assert make_instance(10, 3, "unc", 5) != make_instance(10, 3, "unc", 6)


def test_unknown_family_is_rejected():
    with pytest.raises(ValueError):
        make_instance(5, 3, "xyz", 1)


# --- Auswertung: dieselben Aussagen über die Messreihen und Verdikte der App, gegen unabhängige Rechnung -------------------------------------


def test_analysis_matches_brute_force_and_the_guarantee():
    for family in C.FAMILIES:
        for seed in range(12):
            a = ev.analyse(ev.Settings(n=9, d=1, seed=seed, family=family, eps=0.5, bins=2, bmax=10))
            inst = a.instance
            assert a.exact.value == brute_force_knapsack(inst.weights, inst.values, inst.capacity), (family, seed)
            assert a.fptas.value >= (1 - Fraction(1, 2)) * a.exact.value and ev.validation_errors(a) == []
            assert a.quality == (Fraction(a.fptas.value, a.exact.value) if a.exact.value else 1)


def test_sweeps_match_independent_recomputation():
    seeds = (3, 4, 5, 6)
    for row in ev.sweep_eps(7, "cor", seeds=seeds, digits=1, eps_list=(0.5, 0.2)):
        qs = []
        for s in seeds:
            inst = make_instance(7, 1, "cor", s)
            opt = brute_force_knapsack(inst.weights, inst.values, inst.capacity)
            qs.append(Fraction(A.fptas(inst.weights, inst.values, inst.capacity, row["eps"]).value, opt))
        assert row["min"] == min(qs) and row["violations"] == sum(q < 1 - A.to_fraction(row["eps"]) for q in qs)
    for row in ev.sweep_trap(sizes=(6, 9), eps_list=(0.5, 0.2)):
        w, v, cap = A.trap_instance(row["n"], row["eps"])
        assert row["opt_value"] == sum(v[1:]) == brute_force_knapsack(w, v, cap)               # alle kleinen Pakete (Gewicht 1 je Paket) passen genau
    rows = ev.sweep_plant(counts=(2, 3), seeds=(40, 41))
    assert all(r["solvable"] == 2 for r in rows)
    fixed = ev.sweep_bins_fixed(counts=(2,), bounds=(10,), seeds=(1, 2))
    items = ev.bin_numbers(1, 10)
    assert fixed[0]["max"] >= fixed[0]["peak"] and len(items) == C.BIN_NUMBERS_N


def test_verdicts_on_real_measurements_never_report_an_error_for_a_correct_core():
    digits = ev.sweep_digits(n=8, seeds=(1, 2), digits=(1, 2, 3, 4), eps_list=(0.5,))
    eps_rows = ev.sweep_eps(8, "unc", seeds=(1, 2, 3), digits=2, eps_list=(0.5, 0.1))
    fam_rows = ev.sweep_families(8, eps_list=(0.5,), seeds=(1, 2, 3), digits=2)
    kinds = [ev.verdict_digits(digits)[0], ev.verdict_eps(eps_rows)[0], ev.verdict_families(fam_rows)[0],
             ev.verdict_trap_sweep(ev.sweep_trap(sizes=(6,), eps_list=(0.5,)))[0], ev.verdict_trap(ev.analyse_trap(8, 0.2))[0]]
    assert "error" not in kinds
    a = ev.analyse(ev.Settings(n=8, d=1, seed=3))
    assert ev.verdict_run(a)[0] in ("success", "info") and ev.verdict_bins_live(a.bins, a.settings.bins, a.settings.bmax)[0] == "info"
    assert ev.verdict_bins_fixed(ev.sweep_bins_fixed(counts=(2,), bounds=(10, 20), seeds=(1,)))[0] == "info"
    assert ev.verdict_plant(ev.sweep_plant(counts=(2, 3), seeds=(40,)))[0] == "warning"
