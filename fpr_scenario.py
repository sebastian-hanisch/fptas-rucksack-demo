"""Szenario: Pakete mit Gewicht und Wert für die Fuhre (Rucksack), mit eigenem Zufallsgenerator (SplitMix64, wörtliche Kopie in fpr_rng.py), damit alle Instanzen auf jeder Plattform gleich sind.

Drei Instanzfamilien: „unkorreliert“ (Wert unabhängig vom Gewicht), „stark korreliert“ (Wert = Gewicht + ein Zehntel des größten Gewichts) und „Teilsumme“ (Wert = Gewicht). Kapazität: 40 % der Gewichtssumme."""

from dataclasses import dataclass

import fpr_constants as C
from fpr_rng import SplitMix64


@dataclass(frozen=True)
class Instance:
    weights: tuple[int, ...]
    values: tuple[int, ...]
    capacity: int

    @property
    def n(self) -> int:
        return len(self.weights)


def capacity_for(weights) -> int:
    """40 % der Gewichtssumme, abgerundet, mindestens 1."""
    return max(1, (C.CAPACITY_SHARE * sum(weights)).__floor__())


def make_instance(n: int, digits: int, family: str, seed: int) -> Instance:
    """Deterministisch aus (n, Stellen, Familie, Zufalls-Seed): Gewichte gleichverteilt in 1 bis 10^Stellen."""
    if family not in C.FAMILIES:
        raise ValueError(f"unbekannte Familie: {family}")
    rng = SplitMix64(seed)
    wmax = 10 ** digits
    weights = [1 + rng.below(wmax) for _ in range(n)]
    if family == "unc":
        values = [1 + rng.below(C.VALUE_MAX) for _ in range(n)]
    elif family == "cor":
        values = [w + wmax // C.CORR_DIVISOR for w in weights]
    else:
        values = list(weights)
    return Instance(tuple(weights), tuple(values), capacity_for(weights))
