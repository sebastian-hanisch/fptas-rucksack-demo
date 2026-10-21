# Zahlen und Härte: pseudopolynomiell, FPTAS, stark NP-schwer – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-fptas-rucksack-demo.streamlit.app/)** -->

Fünftes Stück der **Komplexitätsklassen-Reihe** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Stück 1 ([zuordnung-vs-rundreise-demo](https://github.com/sebastian-hanisch/zuordnung-vs-rundreise-demo)) hat gezeigt, wo die Grenze zwischen leicht und schwer verläuft, Stück 3 ([reduktionskette-demo](https://github.com/sebastian-hanisch/reduktionskette-demo)) und Stück 4 ([sat-phasenuebergang-demo](https://github.com/sebastian-hanisch/sat-phasenuebergang-demo)), wie Härte weitergegeben wird und wo sie sich versteckt. Dieses Stück fragt: **Wenn ein Problem nur wegen großer Zahlen schwer ist, was kostet die Größe der Zahlen, und was kauft man mit Genauigkeit?** Vehikel ist die **Fuhre packen** (Pakete mit Gewicht und Wert, begrenzte Kapazität; wie in [dynamic-programming-demo](https://github.com/sebastian-hanisch/dynamic-programming-demo)); für die Härte kommt die **Verteilung auf Behälter** hinzu. Anders als die Fall-Demos zeigt sie **eine Frage der Komplexitätstheorie** an einem wachsenden Beispiel.

## Warum dieses Problem

Drei Begriffe, ein Beispiel: **pseudopolynomiell** (die Tabelle der exakten Rechnung hat n · (W + 1) Zellen, polynomial im *Wert* der Kapazität W, aber W hat bei d Stellen etwa 10^d: exponentiell in der *Länge* der Eingabe), **FPTAS** (rundet man die Werte, hängt die Tabelle nur noch von n und 1 / ε ab, und die Güte ist garantiert mindestens 1 − ε) und **stark NP-schwer** (Probleme wie 3-Partition bleiben schwer, wenn alle Zahlen klein sind; dort fehlt ein pseudopolynomielles Verfahren, und ein FPTAS gibt es unter P ≠ NP nicht). Die Demo zählt Tabellenzellen und Zustände, nie Sekunden, und trennt dabei, was Zufallsinstanzen zeigen (die Garantie ist weit unterschritten) und was nicht (die Härte).

## Modell

- **Rucksack.** Pakete mit ganzzahligem Gewicht in 1 bis 10^d und Wert; Kapazität 40 % der Gewichtssumme. Drei Familien: unkorreliert (Wert 1 bis 1.000), stark korreliert (Wert = Gewicht + ein Zehntel des größten Gewichts), Teilsumme (Wert = Gewicht). Eigener SplitMix64-Generator, deshalb auf jeder Plattform dieselben Instanzen.
- **Exakte Rechnung.** Tabelle über die Kapazität, f(i, c) = max(f(i − 1, c), f(i − 1, c − w_i) + v_i); Zellen n · (W + 1). Ohne gewählte Menge hält die App nur eine Zeile im Speicher.
- **FPTAS** (Wert-Skalierung, Ibarra und Kim): Rundungsschritt K = ε · v_max / n (nur Pakete, die einzeln passen), gerundete Werte ⌊v / K⌋ (ganzzahlig gerechnet), Tabelle über die Gewinnsumme (kleinstes Gewicht je Summe), die gewählte Menge mit ihren echten Werten bewerten. Verlust höchstens n · K = ε · v_max ≤ ε · OPT.
- **Die Falle.** Ein großes Paket (Wert 1.000.000, Gewicht n − 1) gegen n − 1 kleine Pakete (Gewicht 1), deren gerundete Werte zusammen genau eine Einheit weniger zählen als das große, deren echte Werte zusammen aber mehr sind: das FPTAS wählt das große Paket, das Optimum alle kleinen.
- **Behälter-DP.** Ein Zustand ist der sortierte Lastvektor der m Behälter (jede Last höchstens eine Obergrenze); gezählt werden die verschiedenen Zustände nach jeder Zahl. Bei fester Behälterzahl höchstens C(T + m, m), polynomial in den Zahlen; wächst m mit der Eingabe (3-Partition: m = n / 3), nicht.
- Mathematik und Annahmentabelle: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| Kapazitäts-DP (numpy), ganze Tabelle für kleine Instanzen, Rundungsregel, Gewinn-DP, FPTAS, Falle, Behälter-DP, geplante 3-Partition | `fpr_algorithm.py` | eigene Einheiten: `capacity_dp`, `capacity_table`, `scale_values`, `profit_dp`, `fptas` (komponiert nur diese), `trap_instance`, `bin_dp_states`, `planted_three_partition` |
| Instanzfamilien | `fpr_scenario.py` | drei Familien, Kapazität 40 % der Gewichtssumme |
| SplitMix64 | `fpr_rng.py` | **wörtliche Kopie** von reduktionskette-demo/red_scenario.py (Commit ba24648); Regressionstest: die ersten Werte der Konvention |
| Messreihen, Prüfung vor der Anzeige, Verdikte | `fpr_evaluation.py` | alle Verdikte als reine Funktionen |

Experimente in der App: **Wie wächst die Tabelle mit den Stellen?**, **Was kostet Genauigkeit?**, **Die Falle**, **Schwach gegen stark NP-schwer**; die beiden Messreihen mit Behältern laufen auf Knopfdruck (rund 20 und 10 Sekunden), die übrigen sofort.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Messreihen: 40 feste Instanzen je Zelle (`SWEEP_SEEDS`), Stellen-Messreihe 5, Behälter-Messreihen 5 feste Instanzen; die Zahlen der Presets sind Einzelinstanzen und als solche ausgewiesen.

| Frage | Befund |
|---|---|
| **Wie wächst die exakte Tabelle mit den Stellen?** | 30 Pakete, unkorreliert, Median über 5 feste Instanzen: bei 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 Stellen 2.040 / 18.630 / 184.920 / 1.654.920 / 17.510.040 / 183.110.040 / 1.575.110.040 / 17.737.357.410 / 170.632.667.430 Zellen: im Mittel das 9,8-Fache je Stelle, **linear im Wert der Gewichte, exponentiell in ihrer Länge**. Die Zellenformel n · (W + 1) ist an echten Läufen bestätigt (alle fünf Instanzen bis 4 Stellen, je eine bei 5 und 6 Stellen); bei 7 bis 9 Stellen wird nur gezählt (`test_claim_cells_grow_by_a_factor_of_ten_per_digit_while_the_fptas_table_stays`, `test_claim_the_cell_formula_holds_on_real_runs_up_to_six_digits`). |
| **Was spart das FPTAS?** | Seine Tabelle hängt nicht von den Gewichten ab: bei ε = 0,2 konstant 74.580 Zellen, bei ε = 0,05 konstant 299.580 (dieselben Pakete, nur die Gewichte werden länger). Sie ist **ab 3 Stellen (ε = 0,2) bzw. 4 Stellen (ε = 0,05) kleiner** als die exakte. Bei Gewichten bis 10^6 (Preset, Einzelinstanz) 67.590 gegen 190.843.470 Zellen. |
| **Wie gut ist das FPTAS auf Zufallsinstanzen?** | 30 Pakete, unkorreliert, Gewichte bis 1.000, 40 feste Instanzen: bei ε = 0,5 / 0,3 / 0,2 / 0,1 / 0,05 / 0,02 / 0,01 war die kleinste gemessene Güte 99,8 / 99,9 / 99,9 / 99,9 / 99,9 / 100 / 100 % (garantiert 50 / 70 / 80 / 90 / 95 / 98 / 99 %), der Median überall 100 %, exakt optimal in 33 / 37 / 36 / 38 / 39 / 40 / 40 von 40 Läufen. **Die Garantie hielt in allen 280 Läufen und ist auf Zufallsinstanzen weit unterschritten** (`test_claim_quality_over_epsilon`). |
| **Lohnt sich das FPTAS?** | **Nur bei großen Zahlen und grobem ε.** Bei Gewichten bis 1.000 haben die exakte Tabelle im Median 179.310 und die FPTAS-Tabelle bei ε = 0,5 / 0,3 / 0,2 / 0,1 / 0,05 / 0,02 / 0,01 28.095 / 47.025 / 70.875 / 142.110 / 284.505 / 711.960 / 1.424.355 Zellen: **ab ε = 0,1 kleiner, bei 0,05 und feiner größer** (`test_claim_the_fptas_pays_off_only_for_coarse_epsilon_at_three_digits`). |
| **Familien** | Kleinste / mittlere Güte bei ε = 0,5 / 0,2 / 0,1: unkorreliert 99,8 / 100 %, 99,9 / 100 %, 99,9 / 100 %; stark korreliert 99,8 / 99,9 %, 99,8 / 99,9 %, 99,9 / 100 %; Teilsumme 99,6 / 99,8 %, 99,8 / 99,9 %, 99,9 / 99,9 % (`test_claim_families`). Die kleinste Güte überhaupt (Teilsumme, ε = 0,5) ist 99,6 %. |
| **Die Falle** | Das FPTAS wählt immer das große Paket (Wert 1.000.000); die Güte bei ε = 0,5 / 0,3 / 0,2 / 0,1 / 0,05 / 0,02 / 0,01 ist für n = 10: 71,4 / 81,3 / 86,2 / 92,5 / 96,1 / 98,4 / 99,2 %, n = 30: 68,1 / 78,1 / 84,2 / 91,4 / 95,5 / 98,1 / 99,0 %, n = 50: 67,5 / 77,8 / 83,8 / 91,2 / 95,4 / 98,1 / 99,0 %. **Der größte Verlust ist 32,5 % (n = 50, ε = 0,5, erlaubt 50 %): die Garantie hält, die Falle kommt ihr aber nicht ganz nahe.** Beispiel n = 30, ε = 0,2: FPTAS 1.000.000, Optimum 1.186.639 (`test_claim_trap_quality`, `test_claim_trap_values_for_30_packages`). |
| **Behälter-DP, feste Behälterzahl** | 30 Zahlen aus 1 bis B, Obergrenze ⌈Summe / m⌉, Median der Zustandsspitze über 5 feste Verteilungen bei B = 10 / 20 / 40 / 80: m = 2: 43 / 80 / 159 / 310; m = 3: 462 / 1.483 / 5.720 / 21.883; m = 4: 2.727 / 15.496 / 115.980 / 810.333. Von B = 10 auf 80 im Mittel das 1,9- / 3,6- / 6,7-Fache je Verdopplung von B (m = 2 / 3 / 4): **polynomial in den Zahlen, Exponent etwas unter m − 1** (`test_claim_state_space_with_a_fixed_number_of_bins`). |
| **Behälter-DP, wachsende Behälterzahl (3-Partition)** | Geplante Instanzen mit B = 100 (3m Zahlen zwischen 25 und 50, alle lösbar), Median / kleinster / größter Wert der Zustandsspitze über 5 feste Instanzen für m = 2 / 3 / 4 / 5 / 6 / 7: 5 (5 bis 8) / 49 (31 bis 52) / 390 (192 bis 684) / 5.624 (2.310 bis 8.217) / 46.182 (16.161 bis 190.771) / 802.653 (282.709 bis 1.314.516). **Bei festen, kleinen Zahlen wächst der Zustandsraum je Behälter im Median um das 8,0- bis 17,4-Fache**: die Dimension wächst mit der Eingabe, nicht die Größe der Zahlen (`test_claim_state_space_of_planted_three_partition`). |
| **Presets (Einzelinstanzen)** | Optimum / FPTAS / Güte / Zellen exakt / Zellen FPTAS: Standardfall 10.631 / 10.631 / 100 % / 199.470 / 67.590; Lehrbeispiel (8 Pakete) 2.257 / 2.257 / 100 % / 136 / 872 (hier ist die exakte Tabelle kleiner); Viele Stellen 11.211 / 11.211 / 100 % / 190.843.470 / 67.590; Grobes ε 10.631 / 10.631 / 100 % / 199.470 / 26.820; Feines ε 10.631 / 10.631 / 100 % / 199.470 / 1.359.150 (hier ist das FPTAS teurer); Teilsumme 6.648 / 6.642 / 99,9 % / 199.470 / 75.810; Stark korreliert 8.348 / 8.342 / 99,9 % / 199.470 / 81.210 (`test_claim_presets_are_single_instances_with_these_values`). |
| **Rechengrenze** | n = 50 mit Gewichten bis 10^6 (Zufalls-Seed 35): exakte Tabelle 541.066.000 Zellen (Optimum 19.709), FPTAS-Tabelle bei ε = 0,2 330.750 Zellen (`test_claim_the_maximum_instance`). |
| **Verteilungs-Presets** | Standardverteilung (30 Zahlen aus 1 bis 20, Summe 321, 3 Behälter, Obergrenze 107): lösbar, höchstens 1.316 Zustände (15.673 über alle Schritte); Lehrbeispiel (2 Behälter, 1 bis 10): 39 (`test_claim_presets_of_the_bins_section`). |

**Ein Gegenbefund, der nicht in der App steht, aber den Aufbau bestimmt hat:** In einer Vormessung (Scratch, nicht Teil dieser Demo, deshalb ohne Zahlen) löste eine einfache Suche zufällig gezogene 3-Partition-Instanzen fast sofort, auch größere und auch unlösbare. Zufällige Instanzen zeigen die starke NP-Schwere also nicht; die Demo zeigt deshalb den Zustandsraum und sagt das ausdrücklich.

## Ehrliche Grenzen

- **Zellen und Zustände sind keine Laufzeit.** Gezählt wird die Größe der Tabellen, nicht die Rechenzeit; die exakte Tabelle in numpy ist je Zelle viel billiger als ein Zustand der Behälter-DP in Python.
- **Die Garantie beschreibt den schlimmsten Fall.** Auf Zufallsinstanzen liegt die Güte in dieser Demo weit darüber (kleinste gemessene Güte 99,6 %); die gebaute Falle drückt sie bis auf 67,5 %, bleibt aber über der Garantie von 50 %. Eine Instanz, die die Garantie ganz ausschöpft, wurde nicht gebaut.
- **Zufällige Instanzen zeigen die Härte nicht** (siehe Gegenbefund). Stark NP-schwer ist eine Aussage über den schlimmsten Fall; die Demo zeigt die Gestalt des Zustandsraums (Exponent mit der Behälterzahl), keinen Beweis.
- **„Stark NP-schwer ⇒ kein FPTAS“** gilt unter der Annahme P ≠ NP; der Satz folgt aus dem Standardargument von Garey und Johnson (1978), dessen Wortlaut hier **nicht eingesehen** wurde. Die Demo beweist ihn nicht.
- **Die Behälter-DP ist die einfachste Tabelle** ohne Dominanzregeln; bessere Verfahren verkleinern den Zustandsraum, ändern aber nicht seine Gestalt (Exponent mit m). Der Exponent „etwas unter m − 1“ ist gemessen (m = 2, 3, 4), keine Herleitung.
- **Die Zahl der Zustände ist an den Obergrenzen (nach ⌈Summe / m⌉) gemessen**, für die 3-Partition an B = 100 mit m bis 7; größere m sprengen die Zustandsgrenze (1,5 Millionen je Schritt) und wären nicht live nachvollziehbar.
- **Ein Rucksack steht nicht für alle Zahlenprobleme.** Die Messwerte gelten für diese Instanzen und Größen (bis 50 Pakete, Gewichte bis 10^6); die Begriffe sind allgemein, die Zahlen nicht.
- **Beim kleinen Lehrbeispiel ist das FPTAS teurer** als die exakte Rechnung (872 gegen 136 Zellen): es lohnt erst bei großen Zahlen.

## Befunde und Korrekturen gegenüber dem Plan

- **H4 nur eingeschränkt bestätigt:** „Das FPTAS lohnt sich gegenüber der exakten Rechnung“ gilt erst ab drei Stellen (ε = 0,2) bzw. vier (ε = 0,05); bei Gewichten bis 1.000 ist die exakte Tabelle ab ε = 0,05 billiger.
- **H7 widerlegt (im Plan bereits vermerkt):** „Zufällige 3-Partition-Instanzen zeigen die Härte in der Suche“ stimmt nicht; sie sind für eine einfache Suche leicht. Deshalb der Zustandsraum.
- **Die Falle wurde im Bau umgebaut:** Die erste Fassung (alle kleinen Pakete mit demselben Wert) griff bei 17 von 322 Kombinationen aus n = 5 bis 50 und den sieben ε nicht (die Summe der kleinen Werte blieb knapp unter dem großen Paket). Die Fassung mit gestaffelten kleinen Werten (die gerundeten Werte ergeben genau P_A − 1) greift auf allen Reglerwerten (`tests/test_algorithm.py::test_trap_bites_on_the_whole_slider_range`). Die Güten weichen deshalb von der Vormessung ab (damals 69 % bei n = 30, ε = 0,5; jetzt 68,1 %).
- **Plan-Experimente 1 und 4 zusammengelegt:** Die Messreihe über die Stellen zeigt exakte und FPTAS-Tabelle in einem Bild und liefert die Kreuzung „ab wie vielen Stellen billiger“.
- **Andere Seeds, andere Zahlen als in der Vormessung:** Die Vormessung (andere Seeds, 40 Instanzen) hatte bei ε = 0,5 36 von 40 exakt optimale Läufe, diese Demo 33 von 40; die Aussagen blieben gleich.
- **Median wird nie stillschweigend gerundet** (`fmt_median`), die Güte wird **abgerundet** (`fmt_quality`): nur ein exaktes Optimum steht als „100 %“ da.

## Verifikation

- **Kern:** jede Einheit gegen Handrechnung an Mini-Instanzen (`tests/conftest.py`, `tests/test_algorithm.py`): Tabelle Zeile für Zeile, Rundung von Hand (K = 50 / 3, gerundete Werte 6, 4, 4), die Falle für n = 4, die Behälter-DP für drei Mini-Verteilungen (Zustände je Schritt von Hand), Randfälle (Kapazität 0, n = 1, alle Werte 0, nichts passt, ε ≥ 1).
- **Orakel** (`tests/test_oracle_fptas_rucksack.py`): exakte Rechnung gegen Brute Force (300 Instanzen mit Werten 0, Kapazität 0 und größer als die Summe), gegen die Wert-Tabelle desselben Problems ohne Rundung (zweite Achse, 300 Instanzen) und gegen `scipy.optimize.milp` (36 Instanzen; im CI ohne scipy übersprungen); **die Güte-Garantie 1 − ε als harte Prüfung in exakter Bruchrechnung** auf 441 Instanzen aller Familien und Größen, 900 kleinen Zufallsinstanzen und der Falle über alle Reglerwerte; die gewählte Menge ist zulässig und ihr Wert stimmt (unabhängiger Prüfer); die Behälter-DP gegen vollständiges Aufzählen (Zustände je Schritt, Lösbarkeit); geplante 3-Partition-Instanzen gegen eine unabhängige Dreiergruppen-Suche. Der **große Lauf im Scratch-Ordner** und die Mutationsprüfung stehen im nächsten Abschnitt.
- **Kopie** (`tests/test_copies.py`): wortgleich mit dem Original, solange es im Portfolio-Ordner liegt, dazu die bekannten ersten Werte der SplitMix64-Konvention.
- **Prüfung vor der Anzeige:** `validation_errors` prüft beide gewählten Mengen, die Güte-Garantie, die Zellenformel, die ganze Tabelle, bei n ≤ 12 den Optimalwert gegen Brute Force, die Falle und die Behälter-DP (`tests/test_evaluation.py`, jede Meldung ausgelöst).
- **Verdikte** als reine Funktionen, jede Zahl im Text und jede Schwelle an handgesetzten Werten (`tests/test_verdicts.py`); **Claims:** jede Zahl dieser README (`tests/test_claims.py`).
- **Presets:** vollständig, gültige Werte, erstes Preset gleich Standard, jedes Preset ergibt eine geprüfte Analyse (`tests/test_presets.py`); Randfälle der Regler (`tests/test_edge_cases.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button einschließlich der beiden Messreihen, jeder Regler am Minimum und Maximum), Permalink mit Begrenzung und unlesbaren Werten, Layout (ein geänderter Regler hebt die Markierung des alten Presets auf, er kann nur ein anderes Preset treffen), Footer.
- **Browser:** Standardansicht, Lehrbeispiel mit ganzer Tabelle, beide Behälter-Messreihen per Klick; keine Konsolenmeldung.

## Mutationsprüfung und großer Lauf

- **Großer Lauf im Scratch-Ordner (nicht im Repo):** 1.500 Rucksack-Instanzen (bis 14 Pakete) gegen Brute Force, 2.520 FPTAS-Läufe auf allen drei Familien, Größen bis 50 Pakete und 1 bis 4 Stellen gegen die exakte Rechnung (Garantie, Zulässigkeit, Wert), 1.276 Läufe der Falle (n = 3 bis 60, elf ε, zwei große Werte), 150 Behälter-Verteilungen gegen vollständiges Aufzählen, 300 geplante 3-Partition-Instanzen: **0 Abweichungen**.
- **Mutationsprüfung** (`tools/mutate_demo.py`, über `fpr_algorithm.py` und `fpr_evaluation.py`, die das Werkzeug über die Orakel-Tests erreicht; Darstellung, PDF, Presets, Szenario-Familien und Oberfläche mutiert es nicht, sie sind durch Rauch-, Verdikt-, Claims- und Orakel-Tests abgesichert; die wörtliche Kopie `fpr_rng.py` ausgenommen, ihre Tests liegen in Stück 3): **321 Stellen, 316 gesichert** (gefangen, als äquivalent festgehalten oder durch wortgleiche Zeilen in Nachbar-Demos gesichert), 4 offen: Mutanten in der Schleife der Instanzerzeugung, die nicht terminieren (Zeitüberschreitung, zählt nicht). Die Schwachstellen des ersten Laufs (Grenzen der Eingabeprüfung, der Zustandskodierung, der Bewertung gleicher Gewinnsummen, der Prüfungen vor der Anzeige) wurden mit Grenztests geschlossen; 12 Stellen sind äquivalent (zum Beispiel die Größe der „unerreichbar“-Konstante, die Basis der Zustandskodierung, die Zahl 50 als größte zulässige Zahl bei ungeradem B, die im Rahmen liegt, aber nie auftritt) und in `tests/mutation_state.json` festgehalten. Dabei zeigte sich die Lehre aus Stück 3 und 4 wieder: die Orakel-Tests müssen **alle** Kernmodule erreichen, auch die Auswertung, sonst mutiert das Werkzeug sie nicht.


## Einordnung und Quellen (anhand der Quellen geprüft)

FPTAS für den Rucksack durch Wert-Skalierung: Ibarra und Kim, *Fast approximation algorithms for the knapsack and sum of subset problems*, Journal of the ACM 22 (1975), S. 463 bis 468. Starke und schwache NP-Vollständigkeit: Garey und Johnson, *“Strong” NP-completeness results: motivation, examples, and implications*, Journal of the ACM 25 (1978), S. 499 bis 508 (Titel und Seiten geprüft; der Satz, dass ein stark NP-schweres Problem unter P ≠ NP kein FPTAS hat, ist über das Standardargument bekannt, sein Wortlaut dort nicht eingesehen). 3-Partition als stark NP-vollständiges Problem mit Zahlen zwischen einem Viertel und der Hälfte der Gruppensumme: Standardwissen (Garey und Johnson 1979), hier nicht nachgeschlagen. Schnellere FPTAS-Varianten für den Rucksack gibt es; die Demo baut die einfachste und beschreibt die anderen nicht.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: eine Instanz mit zwei Rechnungen, vier Experimente, Annahmentabelle, Formeln |
| `fpr_algorithm.py` | Kern: Kapazitäts-DP, Rundung, Gewinn-DP, FPTAS, Falle, Behälter-DP, geplante 3-Partition |
| `fpr_constants.py` | Regler-Grenzen, Rechengrenzen, Messreihen-Parameter, Farben, Presets |
| `fpr_evaluation.py` | Analyse, Messreihen, Prüfung vor der Anzeige, Verdikte, Zahlenformate |
| `fpr_layout.py` | Fester Kopf (Stylesheet) |
| `fpr_pdf_export.py` | PDF-Bericht (fpdf2) |
| `fpr_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `fpr_rng.py` | wörtliche Kopie: SplitMix64 aus Stück 3 |
| `fpr_scenario.py` | Instanzfamilien der Fuhre |
| `fpr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Mini-Instanzen, Orakel, Kopie, Auswertung, Verdikte, Claims, Presets, Randfälle, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Dominanzlisten (Nemhauser–Ullmann) für den Rucksack und für die Behälter-DP:** ein anderes Verfahren; hier steht die einfachste Tabelle, damit jede Zelle erklärbar bleibt.
- **Eine Suche auf Zufalls-3-Partition als Härtebeweis:** gemessen leicht (siehe Gegenbefund), deshalb nicht gezeigt.
- **Schnellere FPTAS-Varianten:** nur als Einordnung genannt, nicht nachgebaut.
- **PTAS für die Lastverteilung (Minimierung der größten Last):** ein eigenes Thema (Stück 6 der Reihe fragt nach Garantien und ihren Grenzen).
- **Zahlen über 50 Pakete und 6 Stellen live:** darüber wäre die exakte Tabelle in der App zu groß; bei 7 bis 9 Stellen wird nur gezählt.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
