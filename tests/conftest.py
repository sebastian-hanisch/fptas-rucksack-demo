"""Gemeinsame Fixtures: Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """Drei Pakete (Gewicht, Wert) = (2, 3), (3, 4), (4, 5), Kapazität 5.

    Handrechnung der Kapazitäts-DP: Zeilen 0 bis 5 nach jedem Paket.
    Start:         0 0 0 0 0 0
    nach (2, 3):   0 0 3 3 3 3
    nach (3, 4):   0 0 3 4 4 7      (Kapazität 5: Paket 1 und 2, Gewicht 5, Wert 7)
    nach (4, 5):   0 0 3 4 5 7      (Kapazität 4: das dritte Paket allein, Wert 5; Kapazität 5 bleibt 7)
    Optimum 7 mit den Paketen 0 und 1; Zellen n · (W + 1) = 3 · 6 = 18."""
    return [2, 3, 4], [3, 4, 5], 5


@pytest.fixture
def mini_rounding():
    """Drei Pakete (3, 100), (2, 80), (2, 70), Kapazität 4, ε = 1/2.

    Optimum: Paket 1 und 2 (Gewicht 4, Wert 150) gegen Paket 0 allein (Wert 100).
    FPTAS: größter Wert 100, n = 3, K = ε · 100 / 3 = 50 / 3 (≈ 16,67); gerundete Werte p' = ⌊v / K⌋ = ⌊3 v / 50⌋ = 6, 4 (80 · 3 / 50 = 4,8), 4 (70 · 3 / 50 = 4,2).
    Größte erreichbare Gewinnsumme mit Gewicht ≤ 4: Paket 1 + 2 = 8 (Paket 0 allein: 6): das FPTAS wählt {1, 2}, Wert 150, exakt optimal.
    Gewinnsumme insgesamt 14, Zellen n · (P + 1) = 3 · 15 = 45."""
    return [3, 2, 2], [100, 80, 70], 4
