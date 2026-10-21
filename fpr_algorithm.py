"""Kern: Rucksack-DP über die Kapazität (exakt), FPTAS durch Wert-Skalierung, die gebaute Falle und die Behälter-DP für die Härte der Zahlen.

Jede Einheit ist eine Funktion (DEMO-PLAYBOOK §1b): `capacity_dp` und `capacity_table` (exakte Tabelle), `scale_values` (die eine Rundungsregel), `profit_dp` (Tabelle über die Gewinnsumme), `fptas` (setzt nur
diese Bausteine zusammen), `trap_instance`, `bin_dp_states` und `planted_three_partition`. Gezählt werden Tabellenzellen und Zustände, nie Sekunden.

Gewichte sind ganze Zahlen ≥ 1, Werte ganze Zahlen ≥ 0, die Kapazität eine ganze Zahl ≥ 0; die Rechnung ist ganzzahlig (Brüche mit `fractions`), damit Rundungen auf jeder Plattform gleich ausfallen."""

import math
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

import fpr_constants as C
from fpr_rng import SplitMix64

_INF = 1 << 60                       # „unerreichbar“ in der Gewinn-Tabelle; kleiner als 2^63 / 2, damit INF + Gewicht nicht überläuft
_KEY_LIMIT = 1 << 62                 # Obergrenze für die Zustandskodierung der Behälter-DP


@dataclass(frozen=True)
class DpResult:
    value: int
    cells: int
    chosen: tuple[int, ...] | None   # Indizes der gewählten Pakete, nur mit want_choice=True


@dataclass(frozen=True)
class ProfitResult:
    best: int                        # größte erreichbare Summe der gerundeten Werte mit Gewicht <= Kapazität
    chosen: tuple[int, ...]          # Indizes (in den übergebenen Listen)
    cells: int


@dataclass(frozen=True)
class FptasResult:
    value: int                       # echter Wert der gewählten Menge (nicht der gerundete)
    chosen: tuple[int, ...]          # Indizes in der Eingabe
    cells: int                       # Zellen der Gewinn-Tabelle: n_fit · (Summe der gerundeten Werte + 1); 0, wenn keine Rechnung nötig war
    k: Fraction                      # Rundungsschritt K = ε · v_max / n_fit
    n_fit: int                       # Pakete, die einzeln in den Rucksack passen
    scaled_total: int                # Summe der gerundeten Werte


@dataclass(frozen=True)
class BinStates:
    steps: tuple[int, ...]           # Zustände nach jeder Zahl
    peak: int                        # größte Zustandszahl über alle Schritte (der Start zählt als 1)
    total: int                       # Summe über alle Schritte
    final: int                       # Zustände nach der letzten Zahl
    solvable: bool                   # alle Zahlen passen unter die Obergrenze
    aborted: bool                    # ein Schritt überschritt state_cap: peak ist dann nur eine untere Schranke


# --- Eingabe ------------------------------------------------------------------------------------------------------------------------------------


def to_fraction(eps) -> Fraction:
    """ε exakt als Bruch: 0.1 wird 1/10 (nicht der binäre Näherungswert)."""
    if isinstance(eps, Fraction):
        return eps
    if isinstance(eps, int):
        return Fraction(eps)
    return Fraction(eps).limit_denominator(1_000_000)


def _check(weights, values, capacity) -> tuple[list[int], list[int], int]:
    if len(weights) != len(values):
        raise ValueError("Gewichte und Werte müssen gleich viele sein")
    w = [int(x) for x in weights]
    v = [int(x) for x in values]
    capacity = int(capacity)
    if capacity < 0:
        raise ValueError("Die Kapazität darf nicht negativ sein")
    if any(x < 1 for x in w):
        raise ValueError("Gewichte müssen ganze Zahlen >= 1 sein")
    if any(x < 0 for x in v):
        raise ValueError("Werte dürfen nicht negativ sein")
    return w, v, capacity


def knapsack_cells(n: int, capacity: int) -> int:
    """Zellen der Tabelle der exakten Rechnung: n Zeilen, Kapazität + 1 Spalten."""
    return n * (capacity + 1)


def value_of(values, chosen) -> int:
    return sum(int(values[i]) for i in chosen)


def is_feasible_choice(weights, capacity: int, chosen) -> bool:
    """Jedes Paket höchstens einmal, alle Indizes gültig, Gewicht höchstens Kapazität (unabhängige Prüfung, nicht Teil der DP)."""
    chosen = list(chosen)
    if len(set(chosen)) != len(chosen) or any(not 0 <= i < len(weights) for i in chosen):
        return False
    return sum(int(weights[i]) for i in chosen) <= capacity


# --- exakte Rechnung ----------------------------------------------------------------------------------------------------------------------------


def capacity_dp(weights, values, capacity, want_choice: bool = False) -> DpResult:
    """0/1-Rucksack, Tabelle über die Kapazität c = 0..W: f(i, c) = max(f(i-1, c), f(i-1, c - w_i) + v_i). Zellen n · (W + 1).

    Ohne `want_choice` wird nur eine Zeile gehalten (Speicher W + 1); mit `want_choice` zusätzlich die Wahrheitstafel „Paket i wurde bei Kapazität c genommen“ (n · (W + 1) Felder)."""
    w, v, capacity = _check(weights, values, capacity)
    n = len(w)
    dp = np.zeros(capacity + 1, dtype=np.int64)
    take = np.zeros((n, capacity + 1), dtype=bool) if want_choice else None
    for i, (wi, vi) in enumerate(zip(w, v)):
        if wi > capacity:
            continue
        cand = dp[:-wi] + vi
        if take is not None:
            take[i, wi:] = cand > dp[wi:]
        dp[wi:] = np.maximum(dp[wi:], cand)
    chosen = None
    if take is not None:
        c, picked = capacity, []
        for i in range(n - 1, -1, -1):
            if take[i, c]:
                picked.append(i)
                c -= w[i]
        chosen = tuple(sorted(picked))
    return DpResult(int(dp[capacity]), knapsack_cells(n, capacity), chosen)


def capacity_table(weights, values, capacity) -> list[list[int]]:
    """Die ganze Tabelle (Zeile 0 = vor dem ersten Paket) für kleine Instanzen zum Zeichnen und für die Handprobe."""
    w, v, capacity = _check(weights, values, capacity)
    rows = [[0] * (capacity + 1)]
    for wi, vi in zip(w, v):
        prev = rows[-1]
        rows.append([max(prev[c], prev[c - wi] + vi) if c >= wi else prev[c] for c in range(capacity + 1)])
    return rows


# --- FPTAS ----------------------------------------------------------------------------------------------------------------------------------------


def scale_values(values, eps, vmax: int, n: int) -> tuple[Fraction, list[int]]:
    """Die eine Rundungsregel: K = ε · v_max / n, gerundeter Wert p'_i = ⌊v_i / K⌋ (ganzzahlig gerechnet). Bei v_max = 0 ist K = 0 und alles 0."""
    e = to_fraction(eps)
    if vmax <= 0:
        return Fraction(0), [0] * len(values)
    k = e * vmax / n
    scaled = [(int(v) * n * e.denominator) // (e.numerator * vmax) for v in values]
    return k, scaled


def profit_dp(weights, scaled, capacity) -> ProfitResult:
    """Tabelle über die Gewinnsumme q = 0..P (P = Summe der gerundeten Werte): g(i, q) = kleinstes Gewicht, mit dem Pakete 1..i die Summe q erreichen. Zellen n · (P + 1)."""
    n = len(weights)
    p_total = int(sum(scaled))
    minw = np.full(p_total + 1, _INF, dtype=np.int64)
    minw[0] = 0
    take = np.zeros((n, p_total + 1), dtype=bool)
    for i in range(n):
        pi, wi = int(scaled[i]), int(weights[i])
        if pi == 0:
            continue
        shifted = np.full(p_total + 1, _INF, dtype=np.int64)
        shifted[pi:] = minw[:-pi] + wi
        better = shifted < minw
        take[i] = better
        minw = np.where(better, shifted, minw)
    best = int(np.flatnonzero(minw <= capacity).max())
    q, picked = best, []
    for i in range(n - 1, -1, -1):
        if take[i, q]:
            picked.append(i)
            q -= int(scaled[i])
    return ProfitResult(best, tuple(sorted(picked)), n * (p_total + 1))


def fptas(weights, values, capacity, eps) -> FptasResult:
    """Wert-Skalierung nach Ibarra und Kim: nur Pakete, die einzeln passen; K = ε · v_max / n_fit; Werte runden; Gewinn-DP; die gewählte Menge mit ihren echten Werten bewerten.

    Verlust höchstens n_fit · K = ε · v_max <= ε · OPT (v_max ist der Wert eines Pakets, das passt, also höchstens OPT): die Güte ist mindestens 1 - ε."""
    w, v, capacity = _check(weights, values, capacity)
    fit = [i for i in range(len(w)) if w[i] <= capacity]
    vmax = max((v[i] for i in fit), default=0)
    if not fit or vmax == 0:
        return FptasResult(0, (), 0, Fraction(0), len(fit), 0)
    k, scaled = scale_values([v[i] for i in fit], eps, vmax, len(fit))
    res = profit_dp([w[i] for i in fit], scaled, capacity)
    chosen = tuple(fit[j] for j in res.chosen)
    return FptasResult(value_of(v, chosen), chosen, res.cells, k, len(fit), int(sum(scaled)))


def trap_instance(n: int, eps, big: int = C.TRAP_BIG) -> tuple[list[int], list[int], int]:
    """Die Falle für das FPTAS: ein großes Paket A (Gewicht n - 1, Wert `big`) gegen n - 1 kleine Pakete (Gewicht 1), Kapazität n - 1.

    A hat nach dem Runden P_A = ⌊n / ε⌋ Einheiten. Die kleinen Pakete bekommen gerundete Werte, die zusammen genau P_A - 1 ergeben (j = ⌊(P_A - 1) / (n - 1)⌋ für alle, j + 1 für die ersten r = P_A - 1 - (n - 1) · j):
    das FPTAS sieht sie als knapp schlechter als A. Jedes kleine Paket bekommt den größten ganzzahligen Wert mit seinem gerundeten Wert, ⌈(p' + 1) · K⌉ - 1: zusammen sind sie in Wahrheit mehr wert als A.
    Das FPTAS wählt A, das Optimum alle kleinen Pakete."""
    if n < 3:
        raise ValueError("Die Falle braucht mindestens drei Pakete")
    e = to_fraction(eps)
    k = e * big / n
    p_a = (big * n * e.denominator) // (e.numerator * big)      # gerundeter Wert von A: ⌊n / ε⌋
    j = (p_a - 1) // (n - 1)
    r = p_a - 1 - (n - 1) * j
    small = [math.ceil((j + 2) * k) - 1] * r + [math.ceil((j + 1) * k) - 1] * (n - 1 - r)
    return [n - 1] + [1] * (n - 1), [big] + small, n - 1


# --- Behälter-DP: die Härte der Zahlen -----------------------------------------------------------------------------------------------------


def bin_dp_states(items, m: int, cap: int, state_cap: int = C.BIN_STATE_CAP) -> BinStates:
    """Passen die Zahlen auf m Behälter mit Obergrenze `cap`? Zustand = sortierter Lastvektor der m Behälter; je Zahl entstehen die Zustände, in denen sie in einen Behälter gelegt wurde.

    Gezählt werden die verschiedenen Zustände nach jeder Zahl. Bei fester Behälterzahl ist ihre Zahl höchstens (cap + 1)^m (polynomial in den Zahlen); wächst m mit der Eingabe (3-Partition: m = n / 3),
    wächst die Zahl der Zustände auch bei kleinen Zahlen exponentiell. Überschreitet ein Schritt `state_cap`, bricht die Rechnung ab (`aborted`, `peak` ist dann nur eine untere Schranke)."""
    items = [int(x) for x in items]
    if m < 1 or cap < 0 or any(x < 1 for x in items):
        raise ValueError("m >= 1, Obergrenze >= 0 und Zahlen >= 1 erwartet")
    base = cap + 1
    if base ** m >= _KEY_LIMIT:
        raise ValueError("Die Zustandskodierung passt nicht in 63 Bit")
    powers = np.array([base ** j for j in range(m)], dtype=np.int64)
    keys = np.zeros(1, dtype=np.int64)
    steps: list[int] = []
    aborted = False
    for x in items:
        if len(keys) == 0:
            steps.append(0)
            continue
        loads = np.empty((len(keys), m), dtype=np.int64)
        rem = keys.copy()
        for j in range(m):
            loads[:, j] = rem % base
            rem //= base
        parts = []
        for j in range(m):
            mask = loads[:, j] + x <= cap
            if j > 0:
                mask &= loads[:, j] != loads[:, j - 1]          # zwei Behälter mit gleicher Last: derselbe Zustand
            if not mask.any():
                continue
            cand = loads[mask]
            cand[:, j] += x
            cand.sort(axis=1)
            parts.append(cand @ powers)
        keys = np.unique(np.concatenate(parts)) if parts else np.zeros(0, dtype=np.int64)
        steps.append(len(keys))
        if len(keys) > state_cap:
            aborted = True
            break
    final = 0 if aborted else (len(keys) if items else 1)
    return BinStates(tuple(steps), max([1] + steps), sum(steps), final, (not aborted) and final > 0, aborted)


def planted_three_partition(m: int, big_b: int, seed: int) -> list[int]:
    """3m Zahlen mit Summe m · B und B / 4 < x < B / 2, die sich in m Dreiergruppen mit Summe B zerlegen lassen (die Zerlegung wird gezogen und danach gemischt)."""
    lo, hi = big_b // 4 + 1, (big_b - 1) // 2
    if m < 1 or hi < lo or not 3 * lo <= big_b <= 3 * hi:
        raise ValueError("Für diese Summe gibt es keine zulässigen Zahlen")
    rng = SplitMix64(seed)
    items: list[int] = []
    while len(items) < 3 * m:
        a = lo + rng.below(hi - lo + 1)
        b = lo + rng.below(hi - lo + 1)
        c = big_b - a - b
        if lo <= c <= hi:
            items += [a, b, c]
    mix = SplitMix64(seed + 7)
    for i in range(len(items) - 1, 0, -1):
        j = mix.below(i + 1)
        items[i], items[j] = items[j], items[i]
    return items


def is_three_partition_instance(items, big_b: int) -> bool:
    """Form einer 3-Partition-Instanz: 3m Zahlen, Summe m · B, jede echt zwischen B / 4 und B / 2."""
    items = list(items)
    if not items or len(items) % 3 or sum(items) != len(items) // 3 * big_b:
        return False
    return all(4 * x > big_b and 2 * x < big_b for x in items)
