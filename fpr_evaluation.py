"""Kennzahlen, Messreihen und Verdikte (alle Verdikte sind reine Funktionen (Art, Text), DEMO-PLAYBOOK §12)."""

import math
from dataclasses import dataclass
from fractions import Fraction
from statistics import median

import fpr_algorithm as A
import fpr_constants as C
from fpr_rng import SplitMix64
from fpr_scenario import Instance, make_instance


@dataclass(frozen=True, kw_only=True)
class Settings:
    n: int = C.DEFAULT_N
    d: int = C.DEFAULT_D
    seed: int = C.DEFAULT_SEED
    family: str = C.DEFAULT_FAMILY
    eps: float = C.DEFAULT_EPS
    bins: int = C.DEFAULT_BINS
    bmax: int = C.DEFAULT_BMAX


@dataclass(frozen=True)
class TrapResult:
    n: int
    eps: float
    fptas_value: int
    opt_value: int
    small_value: int                 # kleinster Wert eines kleinen Pakets (Anzeige)


@dataclass(frozen=True)
class BinResult:
    items: tuple[int, ...]
    cap: int
    states: A.BinStates


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    instance: Instance
    exact: A.DpResult
    fptas: A.FptasResult
    table: tuple | None              # die ganze Tabelle nur bei kleinen Instanzen
    trap: TrapResult
    bins: BinResult

    @property
    def quality(self) -> Fraction:
        """Güte = Wert des FPTAS / Optimum (1, wenn das Optimum 0 ist)."""
        return Fraction(self.fptas.value, self.exact.value) if self.exact.value else Fraction(1)


# --- Zahlen im deutschen Format ------------------------------------------------------------------------------------------------------------------


def fmt_int(n: int) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner (1.720.350)."""
    return f"{n:,}".replace(",", ".")


def fmt_num(x: float, digits: int = 1) -> str:
    """Dezimalzahl mit Komma (22,7)."""
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_median(x) -> str:
    """Median als ganze Zahl, wenn er eine ist, sonst mit einer Nachkommastelle und Komma (52,5; nie stillschweigend gerundet)."""
    return fmt_int(int(x)) if x == int(x) else fmt_num(float(x), 1)


def fmt_percent(x: float) -> str:
    """Prozentzahl ohne Nachkommastelle, wenn sie ganz ist, sonst mit einer und Komma (2,5; nie stillschweigend gerundet)."""
    return fmt_int(int(x)) if x == int(x) else fmt_num(x, 1)


def fmt_quality(q: Fraction) -> str:
    """Güte als Prozentzahl, auf eine Nachkommastelle ABGERUNDET: nur ein exaktes Optimum steht als „100 %“ da (99,96 % wird „99,9 %“)."""
    if q == 1:
        return "100 %"
    return fmt_num(math.floor(q * 1000) / 10, 1) + " %"


def fmt_loss(q: Fraction) -> str:
    """Verlust 1 - Güte in Prozent, auf eine Nachkommastelle AUFGERUNDET: Güte (abgerundet) und Verlust ergeben zusammen genau 100 %."""
    return fmt_num(math.ceil((1 - q) * 1000) / 10, 1) + " %"


def fmt_eps(eps: float) -> str:
    """ε mit Komma (0,2; 0,05)."""
    return f"{eps:g}".replace(".", ",")


def fmt_guarantee(eps: float) -> str:
    """Garantierter Mindestanteil 1 - ε in Prozent (80 %, 95 %)."""
    return fmt_percent(round(100 * (1 - A.to_fraction(eps)), 4)) + " %"


def fmt_k(k: Fraction) -> str:
    """Rundungsschritt K: ab 1.000 ganzzahlig mit Punkt, sonst vier gültige Stellen mit Komma (0,1667; 16,67)."""
    x = float(k)
    return fmt_int(round(x)) if x >= 1000 else f"{x:.4g}".replace(".", ",")


def fmt_factor(x: float) -> str:
    """Faktor mit Komma, auf eine Nachkommastelle, ab 100 ganzzahlig (7,0; 1.352)."""
    return fmt_int(round(x)) if x >= 100 else fmt_num(x, 1)


# --- Einzelanalyse -------------------------------------------------------------------------------------------------------------------------------


def bin_numbers(seed: int, bmax: int, count: int = C.BIN_NUMBERS_N) -> list[int]:
    """Zahlen der Verteilung (Experiment 3): gleichverteilt in 1 bis B."""
    rng = SplitMix64(seed)
    return [1 + rng.below(bmax) for _ in range(count)]


def analyse_bins(bins: int, bmax: int, seed: int) -> BinResult:
    """Die Zahlen möglichst gleichmäßig auf `bins` Behälter verteilen: Obergrenze ⌈Summe / m⌉ (kleinste mögliche größte Last)."""
    items = bin_numbers(seed, bmax)
    cap = -(-sum(items) // bins)
    return BinResult(tuple(items), cap, A.bin_dp_states(items, bins, cap))


def analyse_trap(n: int, eps: float) -> TrapResult:
    w, v, cap = A.trap_instance(n, eps)
    return TrapResult(n, eps, A.fptas(w, v, cap, eps).value, A.capacity_dp(w, v, cap).value, min(v[1:]))


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.n, settings.d, settings.family, settings.seed)
    cells = A.knapsack_cells(inst.n, inst.capacity)
    exact = A.capacity_dp(inst.weights, inst.values, inst.capacity, want_choice=cells <= C.CHOICE_LIMIT)
    table = None
    if (inst.n + 1) * (inst.capacity + 1) <= C.TABLE_LIMIT:
        table = tuple(tuple(row) for row in A.capacity_table(inst.weights, inst.values, inst.capacity))
    return Analysis(settings, inst, exact, A.fptas(inst.weights, inst.values, inst.capacity, settings.eps), table,
                    analyse_trap(settings.n, settings.eps), analyse_bins(settings.bins, settings.bmax, settings.seed))


def brute_force_value(weights, values, capacity) -> int:
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


def validation_errors(a: Analysis) -> list[str]:
    """Ergebnis vor der Anzeige prüfen (DEMO-PLAYBOOK §1d): zulässige Mengen, Güte-Garantie, bei kleinen Instanzen die Brute-Force-Probe."""
    errors = []
    inst, s = a.instance, a.settings
    if a.exact.chosen is not None and (not A.is_feasible_choice(inst.weights, inst.capacity, a.exact.chosen) or A.value_of(inst.values, a.exact.chosen) != a.exact.value):
        errors.append("Die gewählte Menge der exakten Rechnung ist unzulässig oder passt nicht zum Wert.")
    if not A.is_feasible_choice(inst.weights, inst.capacity, a.fptas.chosen) or A.value_of(inst.values, a.fptas.chosen) != a.fptas.value:
        errors.append("Die gewählte Menge des FPTAS ist unzulässig oder passt nicht zum Wert.")
    if a.fptas.value > a.exact.value:
        errors.append("Das FPTAS meldet mehr als das Optimum.")
    if a.fptas.value < (1 - A.to_fraction(s.eps)) * a.exact.value:
        errors.append("Die Güte-Garantie des FPTAS ist verletzt.")
    if a.exact.cells != A.knapsack_cells(inst.n, inst.capacity):
        errors.append("Die Zellenzahl der exakten Rechnung passt nicht zur Formel n · (W + 1).")
    if a.table is not None and a.table[-1][inst.capacity] != a.exact.value:
        errors.append("Die ganze Tabelle widerspricht dem Optimalwert.")
    if inst.n <= 12 and brute_force_value(inst.weights, inst.values, inst.capacity) != a.exact.value:
        errors.append("Der Optimalwert widerspricht der Brute-Force-Probe.")
    t = a.trap
    if t.fptas_value < (1 - A.to_fraction(t.eps)) * t.opt_value or t.fptas_value > t.opt_value:
        errors.append("Die Falle verletzt die Güte-Garantie oder meldet mehr als das Optimum.")
    st = a.bins.states
    if not st.aborted and st.solvable != (st.final > 0):
        errors.append("Die Behälter-DP meldet Lösbarkeit, die nicht zur Endzustandszahl passt.")
    return errors


# --- Messreihen ----------------------------------------------------------------------------------------------------------------------------------


def sweep_digits(n: int = C.E1_N, seeds=C.E1_SEEDS, digits=C.E1_DIGITS, eps_list=C.E1_EPS) -> list[dict]:
    """Zellen über die Stellen der Gewichte (Familie „unkorreliert“): exakte Tabelle nach der Formel n · (W + 1) (die Tests prüfen sie an echten Läufen), FPTAS jeweils gerechnet."""
    rows = []
    for d in digits:
        exact, fptas = [], {e: [] for e in eps_list}
        for seed in seeds:
            inst = make_instance(n, d, "unc", seed)
            exact.append(A.knapsack_cells(n, inst.capacity))
            for e in eps_list:
                fptas[e].append(A.fptas(inst.weights, inst.values, inst.capacity, e).cells)
        rows.append({"d": d, "count": len(seeds), "exact": median(exact), "fptas": {e: median(c) for e, c in fptas.items()}})
    return rows


def cheaper_from(rows: list[dict], eps: float) -> int | None:
    """Kleinste Stellenzahl, ab der die FPTAS-Tabelle (im Median) kleiner ist als die exakte, und zwar für diese und alle größeren; None, wenn es sie in der Messreihe nie gibt."""
    cheaper = [r["fptas"][eps] < r["exact"] for r in rows]
    for i, r in enumerate(rows):
        if all(cheaper[i:]):
            return r["d"]
    return None


def sweep_eps(n: int, family: str, seeds=C.SWEEP_SEEDS, digits: int = C.E2_DIGITS, eps_list=C.EPS_OPTIONS) -> list[dict]:
    """Güte über ε (feste Instanzen, Gewichte bis 10^digits): kleinste und mittlere Güte, Zahl exakt optimaler Läufe, Verletzungen der Garantie, Zellen exakt gegen FPTAS (Median)."""
    instances = [make_instance(n, digits, family, s) for s in seeds]
    exact = [A.capacity_dp(i.weights, i.values, i.capacity) for i in instances]
    rows = []
    for e in eps_list:
        quality, cells, hits, violations = [], [], 0, 0
        for inst, opt in zip(instances, exact):
            f = A.fptas(inst.weights, inst.values, inst.capacity, e)
            q = Fraction(f.value, opt.value) if opt.value else Fraction(1)
            quality.append(q)
            cells.append(f.cells)
            hits += f.value == opt.value
            violations += q < 1 - A.to_fraction(e)
        rows.append({"eps": e, "count": len(instances), "min": min(quality), "median": median(quality), "exact_hits": hits, "violations": violations,
                     "cells_fptas": median(cells), "cells_exact": median(x.cells for x in exact)})
    return rows


def sweep_families(n: int, eps_list=C.E2_EPS_FAMILIES, seeds=C.SWEEP_SEEDS, digits: int = C.E2_DIGITS) -> list[dict]:
    """Kleinste und mittlere Güte je Familie und ε."""
    rows = []
    for family in C.FAMILIES:
        for r in sweep_eps(n, family, seeds, digits, eps_list):
            rows.append({"family": family, "eps": r["eps"], "min": r["min"], "median": r["median"], "violations": r["violations"], "count": r["count"]})
    return rows


def sweep_trap(sizes=C.TRAP_N, eps_list=C.EPS_OPTIONS) -> list[dict]:
    rows = []
    for n in sizes:
        for e in eps_list:
            t = analyse_trap(n, e)
            rows.append({"n": n, "eps": e, "quality": Fraction(t.fptas_value, t.opt_value), "fptas_value": t.fptas_value, "opt_value": t.opt_value})
    return rows


def sweep_bins_fixed(counts=C.BIN_FIXED_M, bounds=C.BIN_FIXED_B, seeds=C.BIN_FIXED_SEEDS) -> list[dict]:
    """Zustandsspitze der Behälter-DP bei FESTER Behälterzahl m und wachsendem Zahlenbereich B (30 Zahlen aus 1 bis B, Obergrenze ⌈Summe / m⌉)."""
    rows = []
    for m in counts:
        for b in bounds:
            peaks = [analyse_bins(m, b, s).states.peak for s in seeds]
            rows.append({"m": m, "b": b, "count": len(seeds), "peak": median(peaks), "max": max(peaks)})
    return rows


def sweep_plant(counts=C.PLANT_M, seeds=C.PLANT_SEEDS, big_b: int = C.PLANT_B) -> list[dict]:
    """Zustandsspitze bei FESTEN Zahlen (B = 100, jede zwischen 25 und 50) und wachsender Behälterzahl m (3-Partition, n = 3m); geplante Instanzen, alle lösbar."""
    rows = []
    for m in counts:
        peaks, solvable, aborted = [], 0, 0
        for s in seeds:
            st = A.bin_dp_states(A.planted_three_partition(m, big_b, s), m, big_b)
            peaks.append(st.peak)
            solvable += st.solvable
            aborted += st.aborted
        rows.append({"m": m, "count": len(seeds), "peak": median(peaks), "min": min(peaks), "max": max(peaks), "solvable": solvable, "aborted": aborted})
    return rows


# --- Verdikte (reine Funktionen: (Art, Text)) ------------------------------------------------------------------------------------------------------


def verdict_run(a: Analysis) -> tuple[str, str]:
    f, e, s = a.fptas, a.exact, a.settings
    if e.value == 0:
        return "info", "Kein Paket bringt einen Wert: Optimum und FPTAS sind 0."
    head = (f"Das FPTAS findet {fmt_int(f.value)} von {fmt_int(e.value)} ({fmt_quality(a.quality)} des Optimums; bei ε = {fmt_eps(s.eps)} garantiert sind mindestens {fmt_guarantee(s.eps)}), "
            f"mit {fmt_int(f.cells)} statt {fmt_int(e.cells)} Zellen.")
    if f.cells < e.cells:
        return "success", head + f" Die Tabelle ist um den Faktor {fmt_factor(e.cells / f.cells)} kleiner."
    return "info", head + " Bei diesen Gewichten ist die exakte Rechnung billiger: das FPTAS lohnt sich erst bei großen Zahlen (Experiment 1)."


def verdict_trap(t: TrapResult) -> tuple[str, str]:
    q = Fraction(t.fptas_value, t.opt_value)
    return "warning", (
        f"Die Falle ({t.n} Pakete, ε = {fmt_eps(t.eps)}): Das FPTAS wählt das eine große Paket (Wert {fmt_int(t.fptas_value)}), das Optimum nimmt die {t.n - 1} kleinen Pakete (Wert {fmt_int(t.opt_value)}). "
        f"Die Güte ist {fmt_quality(q)}, garantiert waren mindestens {fmt_guarantee(t.eps)}: die Garantie hält, der Verlust von {fmt_loss(q)} liegt unter den erlaubten {fmt_percent(100 * t.eps)} %."
    )


def _growth_per_step(first: float, last: float, steps: int) -> float:
    return (last / first) ** (1 / steps)


def verdict_digits(rows: list[dict]) -> tuple[str, str]:
    first, last = rows[0], rows[-1]
    per_digit = _growth_per_step(first["exact"], last["exact"], last["d"] - first["d"])
    parts = [
        f"Von {first['d']} Stelle ({fmt_median(first['exact'])} Zellen) bis {last['d']} Stellen ({fmt_median(last['exact'])} Zellen) wächst die exakte Tabelle im Mittel um den Faktor {fmt_factor(per_digit)} je Stelle: "
        "linear im Wert der Gewichte, exponentiell in ihrer Länge."
    ]
    for e in first["fptas"]:
        lo = min(r["fptas"][e] for r in rows)
        hi = max(r["fptas"][e] for r in rows)
        cheaper = cheaper_from(rows, e)
        where = "in der Messreihe nie" if cheaper is None else f"ab {cheaper} {'Stelle' if cheaper == 1 else 'Stellen'}"
        span = f"bei {fmt_median(lo)} Zellen" if lo == hi else f"zwischen {fmt_median(lo)} und {fmt_median(hi)} Zellen"
        parts.append(f"Die FPTAS-Tabelle bleibt bei ε = {fmt_eps(e)} {span} und ist {where} billiger als die exakte.")
    return "info", " ".join(parts)


def verdict_eps(rows: list[dict]) -> tuple[str, str]:
    total = sum(r["count"] for r in rows)
    bad = sum(r["violations"] for r in rows)
    if bad:
        return "error", f"Die Güte-Garantie wurde in {bad} von {total} Läufen verletzt: das darf nicht sein."
    worst = min(rows, key=lambda r: r["min"])
    coarse = rows[0]
    return "success", (
        f"In allen {total} Läufen war die Güte mindestens 1 − ε. Die kleinste gemessene Güte war {fmt_quality(worst['min'])} (bei ε = {fmt_eps(worst['eps'])}, garantiert {fmt_guarantee(worst['eps'])}); "
        f"bei ε = {fmt_eps(coarse['eps'])} lag sie im Median bei {fmt_quality(coarse['median'])} statt der garantierten {fmt_guarantee(coarse['eps'])}, und {coarse['exact_hits']} von {coarse['count']} Läufen waren exakt optimal. "
        "Die Garantie ist eine Aussage über den schlimmsten Fall, nicht über typische Instanzen."
    )


def verdict_trap_sweep(rows: list[dict]) -> tuple[str, str]:
    worst = min(rows, key=lambda r: r["quality"])
    best = max(rows, key=lambda r: r["quality"])
    return "warning", (
        f"Die gebaute Falle drückt die Güte bis auf {fmt_quality(worst['quality'])} (n = {worst['n']}, ε = {fmt_eps(worst['eps'])}, garantiert {fmt_guarantee(worst['eps'])}); "
        f"bei ε = {fmt_eps(best['eps'])} und n = {best['n']} bleibt sie bei {fmt_quality(best['quality'])}. Die Garantie hält immer; die Falle kostet deutlich mehr Güte als die Zufallsinstanzen aus Experiment 2, bleibt aber über der Garantie."
    )


def verdict_bins_live(b: BinResult, bins: int, bmax: int) -> tuple[str, str]:
    st = b.states
    if st.aborted:
        return "warning", f"Abbruch: ein Schritt überschritt {fmt_int(C.BIN_STATE_CAP)} Zustände (mindestens {fmt_int(st.peak)} Zustände), die Verteilung wird nicht entschieden."
    answer = "Es gibt eine Verteilung" if st.solvable else "Es gibt keine Verteilung"
    return "info", (
        f"{answer} der {len(b.items)} Zahlen (1 bis {bmax}, Summe {fmt_int(sum(b.items))}) auf {bins} Behälter mit höchstens {fmt_int(b.cap)} je Behälter. "
        f"Die Rechnung hielt höchstens {fmt_int(st.peak)} Zustände gleichzeitig, insgesamt {fmt_int(st.total)} über alle Schritte."
    )


def verdict_bins_fixed(rows: list[dict]) -> tuple[str, str]:
    by_m: dict[int, list[dict]] = {}
    for r in rows:
        by_m.setdefault(r["m"], []).append(r)
    parts = []
    for m, rs in by_m.items():
        lo, hi = rs[0], rs[-1]
        steps = math.log2(hi["b"] / lo["b"])
        parts.append(f"m = {m}: von B = {lo['b']} auf {hi['b']} wächst die Spitze von {fmt_median(lo['peak'])} auf {fmt_median(hi['peak'])} Zustände, im Mittel um den Faktor {fmt_factor(_growth_per_step(lo['peak'], hi['peak'], steps))} je Verdopplung von B")
    return "info", "Bei fester Behälterzahl wächst der Zustandsraum nur polynomial mit den Zahlen: " + "; ".join(parts) + ". Je mehr Behälter, desto steiler der Exponent (grob m − 1)."


def verdict_plant(rows: list[dict]) -> tuple[str, str]:
    lo, hi = rows[0], rows[-1]
    factors = [b["peak"] / a["peak"] for a, b in zip(rows, rows[1:])]
    solvable = sum(r["solvable"] for r in rows)
    total = sum(r["count"] for r in rows)
    aborted = sum(r["aborted"] for r in rows)
    note = f" {aborted} Läufe brachen an der Zustandsgrenze ab." if aborted else ""
    return "warning", (
        f"Bei festen Zahlen (B = {C.PLANT_B}, jede zwischen 25 und 50) wächst der Zustandsraum mit der Behälterzahl von {fmt_median(lo['peak'])} (m = {lo['m']}) auf {fmt_median(hi['peak'])} Zustände (m = {hi['m']}), "
        f"je Behälter mehr im Median um den Faktor {fmt_factor(min(factors))} bis {fmt_factor(max(factors))}. Die Zahlen werden dabei nicht größer: die Dimension des Zustandsraums wächst mit der Eingabe. "
        f"Alle {solvable} von {total} geplanten Instanzen waren lösbar.{note}"
    )


def verdict_families(rows: list[dict]) -> tuple[str, str]:
    bad = sum(r["violations"] for r in rows)
    if bad:
        return "error", f"Die Güte-Garantie wurde in {bad} Läufen verletzt: das darf nicht sein."
    worst = min(rows, key=lambda r: r["min"])
    return "info", (
        f"Die kleinste gemessene Güte über alle Familien war {fmt_quality(worst['min'])} ({C.FAMILIES[worst['family']]}, ε = {fmt_eps(worst['eps'])}, garantiert {fmt_guarantee(worst['eps'])}). "
        "Auf zufälligen Instanzen liegt die Güte weit über der Garantie."
    )
