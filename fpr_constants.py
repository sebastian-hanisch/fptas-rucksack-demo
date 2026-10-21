"""Konstanten: Regler-Grenzen, Rechengrenzen, Messreihen-Parameter, Farben und Presets.

Rechengrenze am Regler-Maximum (DEMO-PLAYBOOK §1c): n = 50 Pakete mit Gewichten bis 10^6 ergeben eine Kapazität von rund 10 Mio. und eine Tabelle von rund 500 Mio. Zellen; numpy rechnet das in wenigen
Sekunden, die App speichert dabei nur eine Zeile (nicht die ganze Tabelle). Die Menge der gewählten Pakete wird nur bis CHOICE_LIMIT Zellen rekonstruiert (dafür braucht es die ganze Tabelle)."""

from fractions import Fraction

N_MIN, N_MAX, DEFAULT_N = 5, 50, 30
D_MIN, D_MAX, DEFAULT_D = 1, 6, 3          # Stellen der Gewichte: Gewichte gleichverteilt in 1 bis 10^d
SEED_MAX, DEFAULT_SEED = 999999, 35
FAMILIES = {"unc": "unkorreliert", "cor": "stark korreliert", "sub": "Teilsumme (Wert = Gewicht)"}
DEFAULT_FAMILY = "unc"
EPS_OPTIONS = (0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01)
DEFAULT_EPS = 0.2
BINS_OPTIONS = (2, 3, 4)                   # Behälter der Verteilung (Experiment 3, live): m = 4 mit Zahlen bis 40 braucht rund 1 Sekunde
DEFAULT_BINS = 3
BMAX_OPTIONS = (10, 20, 40)                # Zahlen der Verteilung gleichverteilt in 1 bis B
DEFAULT_BMAX = 20

CAPACITY_SHARE = Fraction(2, 5)            # Kapazität = 40 % der Gewichtssumme (abgerundet, mindestens 1)
VALUE_MAX = 1000                           # Werte der Familie „unkorreliert“: 1 bis 1000
CORR_DIVISOR = 10                          # „stark korreliert“: Wert = Gewicht + (größtes Gewicht) // 10
TABLE_LIMIT = 3000                         # so viele Felder zeichnet die App höchstens als Tabelle (kleine Instanzen)
CHOICE_LIMIT = 3_000_000                   # bis zu so vielen Zellen rekonstruiert die App die gewählte Menge der exakten DP
BIN_NUMBERS_N = 30                         # Anzahl der Zahlen der Verteilung (Experiment 3, live)
BIN_STATE_CAP = 1_500_000                  # Obergrenze für die Zustände eines Schrittes der Behälter-DP: danach Abbruch (untere Schranke)

# Messreihen (alle Instanzen aus dem eigenen Generator: auf jeder Plattform dieselben)
SWEEP_SEEDS = tuple(range(100000, 100040))  # 40 feste Instanzen je Zelle: nie ein einzelner Seed als Befund
E1_DIGITS = tuple(range(1, 10))            # Stellen: Zellen der exakten DP nach der Formel (n · (W + 1), an echten Läufen bis 6 Stellen geprüft), FPTAS immer gerechnet
E1_EPS = (0.2, 0.05)
E1_SEEDS = tuple(range(300, 305))
E1_N = 30
E2_DIGITS = 3                              # Gewichte der Güte-Messreihe: 1 bis 1000
E2_EPS_FAMILIES = (0.5, 0.2, 0.1)         # ε der Familien-Tabelle
TRAP_N = (10, 30, 50)                      # Größen der Fallen-Messreihe
TRAP_BIG = 1_000_000                       # Wert des großen Pakets der Falle
BIN_FIXED_M = (2, 3, 4)
BIN_FIXED_B = (10, 20, 40, 80)
BIN_FIXED_SEEDS = tuple(range(900, 905))
PLANT_B = 100
PLANT_M = (2, 3, 4, 5, 6, 7)
PLANT_SEEDS = tuple(range(40, 45))

COLOR_EXACT = "#4c78a8"
COLOR_FPTAS = "#2F6B65"
COLOR_GUARANTEE = "#C0392B"
COLOR_TRAP = "#B8860B"
COLOR_CHOSEN = "#2F6B65"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_SERIES = ("#2F6B65", "#4c78a8", "#B8860B", "#C0392B")

PRESETS = {
    "Standardfall (Voreinstellung)": {"n": DEFAULT_N, "d": DEFAULT_D, "seed": DEFAULT_SEED, "family": "unc", "eps": DEFAULT_EPS, "bins": DEFAULT_BINS, "bmax": DEFAULT_BMAX},
    "Lehrbeispiel (8 Pakete)": {"n": 8, "d": 1, "seed": 3, "family": "unc", "eps": 0.3, "bins": 2, "bmax": 10},
    "Viele Stellen (Gewichte bis 10^6)": {"n": DEFAULT_N, "d": 6, "seed": DEFAULT_SEED, "family": "unc", "eps": DEFAULT_EPS, "bins": DEFAULT_BINS, "bmax": DEFAULT_BMAX},
    "Grobes ε (0,5)": {"n": DEFAULT_N, "d": DEFAULT_D, "seed": DEFAULT_SEED, "family": "unc", "eps": 0.5, "bins": DEFAULT_BINS, "bmax": DEFAULT_BMAX},
    "Feines ε (0,01)": {"n": DEFAULT_N, "d": DEFAULT_D, "seed": DEFAULT_SEED, "family": "unc", "eps": 0.01, "bins": DEFAULT_BINS, "bmax": DEFAULT_BMAX},
    "Teilsumme (Wert = Gewicht)": {"n": DEFAULT_N, "d": DEFAULT_D, "seed": DEFAULT_SEED, "family": "sub", "eps": DEFAULT_EPS, "bins": DEFAULT_BINS, "bmax": DEFAULT_BMAX},
    "Stark korreliert": {"n": DEFAULT_N, "d": DEFAULT_D, "seed": DEFAULT_SEED, "family": "cor", "eps": DEFAULT_EPS, "bins": DEFAULT_BINS, "bmax": DEFAULT_BMAX},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "30 Pakete, Gewichte bis 1.000, ε = 0,2: exakte Rechnung und FPTAS nebeneinander.",
    "Lehrbeispiel (8 Pakete)": "8 Pakete mit Gewichten bis 10: die ganze Tabelle der exakten Rechnung ist als Bild zu lesen.",
    "Viele Stellen (Gewichte bis 10^6)": "Sechs Stellen: die exakte Tabelle hat Millionen von Zellen, das FPTAS bleibt klein.",
    "Grobes ε (0,5)": "Die Garantie ist nur 50 % des Optimums; wie nah kommt das FPTAS tatsächlich?",
    "Feines ε (0,01)": "Fast exakt, dafür eine große Tabelle: das FPTAS kann teurer werden als die exakte Rechnung.",
    "Teilsumme (Wert = Gewicht)": "Der Wert eines Pakets ist sein Gewicht: Füllen ohne Preisunterschiede, die härtere Instanzfamilie.",
    "Stark korreliert": "Der Wert liegt knapp über dem Gewicht: viele Pakete sehen gleich gut aus.",
}
