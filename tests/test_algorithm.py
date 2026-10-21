"""Einheiten des Kerns an Mini-Instanzen von Hand (DEMO-PLAYBOOK §1b): jede Einheit ist eine Funktion, jede hat einen Handwert."""

from fractions import Fraction

import numpy as np
import pytest

import fpr_algorithm as A


# --- Kapazitäts-DP -------------------------------------------------------------------------------------------------------------------------------


def test_capacity_dp_hand_values(mini):
    weights, values, capacity = mini
    r = A.capacity_dp(weights, values, capacity, want_choice=True)
    assert r.value == 7
    assert r.chosen == (0, 1)
    assert r.cells == 18 == A.knapsack_cells(3, 5)


def test_capacity_table_matches_the_hand_table(mini):
    weights, values, capacity = mini
    assert A.capacity_table(weights, values, capacity) == [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 3, 3, 3, 3],
        [0, 0, 3, 4, 4, 7],
        [0, 0, 3, 4, 5, 7],
    ]


def test_capacity_dp_without_choice_returns_none_for_the_choice(mini):
    weights, values, capacity = mini
    assert A.capacity_dp(weights, values, capacity).chosen is None


def test_capacity_dp_edge_cases():
    assert A.capacity_dp([], [], 5).value == 0
    assert A.capacity_dp([2], [9], 1, want_choice=True).value == 0                  # das einzige Paket passt nicht
    assert A.capacity_dp([2], [9], 1, want_choice=True).chosen == ()
    assert A.capacity_dp([2], [9], 0).value == 0                                    # Kapazität 0
    assert A.capacity_dp([2], [9], 2, want_choice=True).chosen == (0,)              # passt genau
    assert A.capacity_dp([1, 1, 1], [5, 5, 5], 3).value == 15                       # alle gleich, alle passen


def test_capacity_dp_rejects_invalid_input():
    with pytest.raises(ValueError):
        A.capacity_dp([0], [1], 5)           # Gewicht 0 ist nicht vorgesehen
    with pytest.raises(ValueError):
        A.capacity_dp([1], [-1], 5)          # negativer Wert
    with pytest.raises(ValueError):
        A.capacity_dp([1, 2], [1], 5)        # ungleich lang
    with pytest.raises(ValueError):
        A.capacity_dp([1], [1], -1)          # negative Kapazität


# --- Rundung und Gewinn-DP -----------------------------------------------------------------------------------------------------------------------


def test_to_fraction_is_exact_for_decimal_options():
    assert A.to_fraction(0.1) == Fraction(1, 10)
    assert A.to_fraction(0.05) == Fraction(1, 20)
    assert A.to_fraction(0.5) == Fraction(1, 2)


def test_scale_values_hand_values(mini_rounding):
    weights, values, capacity = mini_rounding
    k, scaled = A.scale_values(values, 0.5, 100, 3)
    assert k == Fraction(50, 3)
    assert scaled == [6, 4, 4]


def test_scale_values_rounds_down_and_is_exact_at_the_boundary():
    # K = ε · vmax / n = 1/2 · 10 / 5 = 1: p' = v
    k, scaled = A.scale_values([10, 9, 1, 0], 0.5, 10, 5)
    assert k == Fraction(1)
    assert scaled == [10, 9, 1, 0]
    # K = 1/2 · 10 / 2 = 5/2: 10 / 2,5 = 4 (exakt), 9 / 2,5 = 3,6 -> 3, 2 / 2,5 -> 0
    assert A.scale_values([10, 9, 2], 0.5, 10, 2)[1] == [4, 3, 0]


def test_profit_dp_hand_values(mini_rounding):
    weights, values, capacity = mini_rounding
    r = A.profit_dp(weights, [6, 4, 4], capacity)
    assert r.best == 8
    assert r.chosen == (1, 2)
    assert r.cells == 3 * (14 + 1) == 45


def test_profit_dp_with_all_profits_zero_chooses_nothing():
    r = A.profit_dp([1, 2], [0, 0], 5)
    assert r.best == 0 and r.chosen == ()
    assert r.cells == 2 * 1


def test_fptas_hand_values(mini_rounding):
    weights, values, capacity = mini_rounding
    r = A.fptas(weights, values, capacity, 0.5)
    assert r.chosen == (1, 2)
    assert r.value == 150
    assert r.k == Fraction(50, 3)
    assert r.cells == 45
    assert r.n_fit == 3


def test_fptas_ignores_items_that_do_not_fit_but_reports_original_indices():
    # Paket 0 passt nicht (Gewicht 9 > 4); die Indizes der Antwort beziehen sich auf die Eingabe
    r = A.fptas([9, 2, 2], [1000, 80, 70], 4, 0.5)
    assert r.chosen == (1, 2) and r.value == 150
    assert r.n_fit == 2


def test_fptas_edge_cases():
    assert A.fptas([], [], 5, 0.5).value == 0
    assert A.fptas([9], [5], 4, 0.5).value == 0 and A.fptas([9], [5], 4, 0.5).chosen == ()    # nichts passt
    assert A.fptas([3], [5], 4, 0.5).chosen == (0,)                                           # n = 1
    assert A.fptas([1, 1], [0, 0], 4, 0.5).value == 0                                         # alle Werte 0
    r = A.fptas([1, 1, 1], [7, 7, 7], 2, 0.5)                                                 # alle gleich
    assert r.value == 14 and len(r.chosen) == 2


def test_fptas_with_epsilon_at_least_one_is_still_feasible():
    r = A.fptas([3, 2, 2], [100, 80, 70], 4, 1.0)
    assert sum([3, 2, 2][i] for i in r.chosen) <= 4
    assert r.value == sum([100, 80, 70][i] for i in r.chosen)


# --- die gebaute Falle ---------------------------------------------------------------------------------------------------------------------------


def test_trap_instance_hand_values():
    """n = 4, ε = 1/2, großer Wert 1000: K = 125, P_A = ⌊n / ε⌋ = 8, j = ⌊(8 - 1) / 3⌋ = 2, r = 7 - 3 · 2 = 1.
    Kleine Werte: ein Paket mit gerundetem Wert 3 (⌈4 · 125⌉ - 1 = 499), zwei mit 2 (⌈3 · 125⌉ - 1 = 374); gerundete Summe 7 < 8."""
    weights, values, capacity = A.trap_instance(4, 0.5, big=1000)
    assert weights == [3, 1, 1, 1] and values == [1000, 499, 374, 374] and capacity == 3
    opt = A.capacity_dp(weights, values, capacity)
    assert opt.value == 1247                                    # alle drei kleinen Pakete
    f = A.fptas(weights, values, capacity, 0.5)
    assert f.value == 1000 and f.chosen == (0,)                 # das FPTAS nimmt das große Paket
    assert f.cells == 4 * (8 + 3 + 2 + 2 + 1) == 64
    assert f.value / opt.value == pytest.approx(1000 / 1247)


def test_trap_bites_on_the_whole_slider_range():
    import fpr_constants as C
    for n in range(C.N_MIN, C.N_MAX + 1):
        for eps in C.EPS_OPTIONS:
            w, v, cap = A.trap_instance(n, eps)
            opt = A.capacity_dp(w, v, cap).value
            f = A.fptas(w, v, cap, eps).value
            assert f == C.TRAP_BIG and opt > f, (n, eps)


def test_trap_rejects_fewer_than_three_items():
    with pytest.raises(ValueError):
        A.trap_instance(2, 0.5)


# --- Behälter-DP ---------------------------------------------------------------------------------------------------------------------------------


def test_bin_dp_unsolvable_hand_case():
    """Zahlen 3, 3, 2 auf 2 Behälter mit Obergrenze 4: Schritt 1: (0, 3); Schritt 2: (3, 3); Schritt 3: 3 + 2 > 4, keine Zustände. Spitze 1, nicht lösbar."""
    r = A.bin_dp_states([3, 3, 2], 2, 4)
    assert r.steps == (1, 1, 0) and r.peak == 1 and r.final == 0 and not r.solvable and not r.aborted
    assert r.total == 2


def test_bin_dp_two_bins_hand_case():
    """Vier Zweier auf 2 Behälter mit Obergrenze 4: Zustände (0, 2) / (0, 4) und (2, 2) / (2, 4) / (4, 4): Schritte 1, 2, 1, 1."""
    r = A.bin_dp_states([2, 2, 2, 2], 2, 4)
    assert r.steps == (1, 2, 1, 1) and r.peak == 2 and r.final == 1 and r.solvable
    assert r.total == 5


def test_bin_dp_three_bins_hand_case():
    """Sechs Zweier auf 3 Behälter mit Obergrenze 4. Schritt 1: (0, 0, 2); 2: (0, 0, 4), (0, 2, 2); 3: (0, 2, 4), (2, 2, 2); 4: (2, 2, 4), (0, 4, 4); 5: (2, 4, 4); 6: (4, 4, 4): Schritte 1, 2, 2, 2, 1, 1."""
    r = A.bin_dp_states([2] * 6, 3, 4)
    assert r.steps == (1, 2, 2, 2, 1, 1) and r.peak == 2 and r.final == 1 and r.solvable


def test_bin_dp_aborts_above_the_state_cap():
    r = A.bin_dp_states([1] * 12, 4, 6, state_cap=3)
    assert r.aborted and r.peak > 3 and not r.solvable


def test_bin_dp_rejects_unsafe_state_encoding():
    with pytest.raises(ValueError):
        A.bin_dp_states([1], 10, 10 ** 6)      # (cap + 1)^m passt nicht in 63 Bit


def test_bin_dp_edge_cases():
    r = A.bin_dp_states([], 3, 5)
    assert r.peak == 1 and r.final == 1 and r.solvable and r.steps == ()
    assert not A.bin_dp_states([6], 2, 5).solvable        # eine Zahl größer als die Obergrenze
    assert A.bin_dp_states([5], 1, 5).solvable            # ein Behälter, passt genau


# --- geplante 3-Partition-Instanzen --------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("m", [2, 3, 5])
def test_planted_three_partition_is_valid_and_solvable(m):
    items = A.planted_three_partition(m, 100, 40 + m)
    assert len(items) == 3 * m and sum(items) == m * 100
    assert all(25 < x < 50 for x in items)                                  # B / 4 < x < B / 2
    assert A.bin_dp_states(items, m, 100).solvable


def test_planted_three_partition_is_deterministic_and_shuffled():
    assert A.planted_three_partition(4, 100, 7) == A.planted_three_partition(4, 100, 7)
    assert A.planted_three_partition(4, 100, 7) != A.planted_three_partition(4, 100, 8)
    items = A.planted_three_partition(6, 100, 9)
    assert items != sorted(items)


def test_check_three_partition_instance():
    assert A.is_three_partition_instance([30, 30, 40, 32, 33, 35], 100)
    assert not A.is_three_partition_instance([30, 30, 40, 32, 33], 100)            # keine 3m Zahlen
    assert not A.is_three_partition_instance([30, 30, 41, 32, 33, 35], 100)        # Summe stimmt nicht
    assert not A.is_three_partition_instance([25, 35, 40, 32, 33, 35], 100)        # 25 ist nicht echt größer als B / 4
    assert not A.is_three_partition_instance([50, 20, 30, 32, 33, 35], 100)        # 50 ist nicht echt kleiner als B / 2


# --- Hilfen ------------------------------------------------------------------------------------------------------------------------------------


def test_is_feasible_choice_and_value_of():
    assert A.value_of([3, 4, 5], (0, 2)) == 8
    assert A.is_feasible_choice([2, 3, 4], 5, (0, 1))
    assert not A.is_feasible_choice([2, 3, 4], 5, (1, 2))
    assert not A.is_feasible_choice([2, 3, 4], 5, (0, 0))      # ein Paket nur einmal


def test_numpy_integers_are_accepted():
    weights = list(np.array([2, 3, 4]))
    assert A.capacity_dp(weights, list(np.array([3, 4, 5])), 5).value == 7


# --- Lücken aus der Mutationsprüfung ------------------------------------------------------------------------------------------------------


def test_check_rejects_zero_weights_directly():
    with pytest.raises(ValueError):
        A._check([0], [1], 5)


def test_capacity_dp_choice_leaves_out_items_without_gain():
    """Ein Paket mit Wert 0 bringt bei Gleichstand nichts und wird nicht gewählt."""
    assert A.capacity_dp([1, 1], [0, 5], 2, want_choice=True).chosen == (1,)


def test_fptas_without_any_valuable_item_runs_no_table():
    r = A.fptas([1, 1], [0, 0], 4, 0.5)
    assert r.cells == 0 and r.k == 0 and r.scaled_total == 0 and r.n_fit == 2


def test_scale_values_with_zero_maximum():
    assert A.scale_values([0, 0], 0.5, 0, 2) == (Fraction(0), [0, 0])


def test_profit_dp_tie_rule_takes_the_first_found_set():
    """Zwei gleiche Pakete, Platz für eines: bei gleicher gerundeter Summe gewinnt das erste (die Regel steht in der Annahmentabelle der App)."""
    assert A.profit_dp([1, 1], [1, 1], 1).chosen == (0,)


def test_is_feasible_choice_rejects_invalid_indices():
    assert not A.is_feasible_choice([2, 3], 5, (2,))           # Index = Länge
    assert not A.is_feasible_choice([2, 3], 5, (-1,))          # negativer Index


def test_three_partition_bounds_are_strict():
    assert not A.is_three_partition_instance([50, 30, 30, 30, 30, 30], 100)     # 50 = B / 2: nicht echt kleiner
    assert not A.is_three_partition_instance([25, 35, 35, 35, 35, 35], 100)     # 25 = B / 4: nicht echt größer


def test_bin_dp_encoding_limit_is_exactly_two_to_the_62():
    A.bin_dp_states([1], 2, 2 ** 31 - 2)                        # (cap + 1)^2 liegt knapp unter 2^62: erlaubt
    with pytest.raises(ValueError):
        A.bin_dp_states([1], 2, 2 ** 31)                        # knapp darüber: abgelehnt


def test_planted_three_partition_accepts_the_smallest_and_odd_sums():
    assert A.planted_three_partition(1, 3, 1) == [1, 1, 1] and A.is_three_partition_instance([1, 1, 1], 3)      # B = 3 · (B / 3)
    items = A.planted_three_partition(2, 12, 5)
    assert items == [4, 4, 4, 4, 4, 4]                                                                          # nur (4, 4, 4) summiert zu 12 mit Zahlen in [4, 5]
    assert A.planted_three_partition(1, 100, 3) and len(A.planted_three_partition(1, 100, 3)) == 3             # m = 1 ist erlaubt
    with pytest.raises(ValueError):
        A.planted_three_partition(0, 100, 1)                    # m = 0 nicht
    with pytest.raises(ValueError):
        A.planted_three_partition(2, 5, 1)                      # zu kleine Summe: keine zulässigen Zahlen
    for seed in range(50):                                      # B ungerade: jede Instanz ist gültig
        assert A.is_three_partition_instance(A.planted_three_partition(3, 101, seed), 101)


def test_trap_with_exact_division_has_no_remainder_group():
    """ε = 4/7, n = 4, großer Wert 700: K = 100, P_A = 7, j = ⌊6 / 3⌋ = 2, r = 0: alle drei kleinen Pakete mit gerundetem Wert 2 (Wert ⌈3 · 100⌉ - 1 = 299)."""
    weights, values, capacity = A.trap_instance(4, Fraction(4, 7), big=700)
    assert (weights, values, capacity) == ([3, 1, 1, 1], [700, 299, 299, 299], 3)
    assert A.fptas(weights, values, capacity, Fraction(4, 7)).chosen == (0,) and A.capacity_dp(weights, values, capacity).value == 897


def test_bin_dp_validates_its_arguments():
    with pytest.raises(ValueError):
        A.bin_dp_states([1], 0, 5)              # keine Behälter
    with pytest.raises(ValueError):
        A.bin_dp_states([1], 1, -1)             # negative Obergrenze
    with pytest.raises(ValueError):
        A.bin_dp_states([0], 1, 5)              # Zahl 0
    r = A.bin_dp_states([], 2, 0)               # Obergrenze 0 ist erlaubt (nichts zu verteilen)
    assert r.solvable and r.peak == 1
    assert not A.bin_dp_states([1], 1, 0).solvable      # Obergrenze 0: nichts passt, aber kein Fehler


def test_bin_dp_encoding_limit_at_exactly_two_to_the_62():
    with pytest.raises(ValueError):
        A.bin_dp_states([1], 2, 2 ** 31 - 1)    # (cap + 1)^2 = 2^62 genau: abgelehnt
