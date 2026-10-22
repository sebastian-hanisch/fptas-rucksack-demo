"""Zahlen und Härte: pseudopolynomiell, FPTAS, stark NP-schwer - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Fünftes Stück der Komplexitätsklassen-Reihe: was die Größe der Zahlen kostet und was Genauigkeit kauft. Aufwand in Tabellenzellen und Zuständen, nie in Sekunden.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import fpr_constants as C
from fpr_evaluation import (
    Settings,
    analyse,
    cheaper_from,
    fmt_eps,
    fmt_factor,
    fmt_guarantee,
    fmt_int,
    fmt_k,
    fmt_median,
    fmt_quality,
    sweep_bins_fixed,
    sweep_digits,
    sweep_eps,
    sweep_families,
    sweep_plant,
    sweep_trap,
    validation_errors,
    verdict_bins_fixed,
    verdict_bins_live,
    verdict_digits,
    verdict_eps,
    verdict_families,
    verdict_plant,
    verdict_run,
    verdict_trap,
    verdict_trap_sweep,
)
from fpr_layout import dunkles_design, kopf_css
from fpr_pdf_export import build_pdf
from fpr_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from fpr_visualization import (
    build_bin_steps,
    build_bins_fixed,
    build_cells,
    build_digits,
    build_eps_cells,
    build_eps_quality,
    build_items,
    build_plant,
    build_table,
    build_trap,
)

st.set_page_config(page_title="Zahlen und Härte – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _digits():
    return sweep_digits()


@st.cache_data(show_spinner=False)
def _eps(n, family):
    return sweep_eps(n, family)


@st.cache_data(show_spinner=False)
def _families(n):
    return sweep_families(n)


@st.cache_data(show_spinner=False)
def _trap():
    return sweep_trap()


@st.cache_data(show_spinner=False)
def _bins_fixed():
    return sweep_bins_fixed()


@st.cache_data(show_spinner=False)
def _plant():
    return sweep_plant()


@st.cache_data(show_spinner=False)
def _pdf(settings):
    return build_pdf(analyse(settings))


def _md_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _packages(indices):
    return ", ".join(str(i + 1) for i in indices) if indices else "keines"


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in fpr_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔢 Zahlen und Härte: pseudopolynomiell, FPTAS, stark NP-schwer")
st.markdown(
    """
Manche NP-schwere Probleme sind nur wegen **großer Zahlen** schwer. Die Demo zeigt das an der **Fuhre packen** (Pakete mit Gewicht und Wert, begrenzte Kapazität): Die exakte Tabelle wächst mit dem **Wert** der Gewichte,
also **exponentiell in ihrer Länge**; rundet man die Werte, wird die Tabelle klein, und eine **Güte-Garantie** bleibt (**FPTAS**); und bei Problemen wie der **3-Partition** helfen kleine Zahlen nicht, weil der **Zustandsraum**
mit der Eingabe wächst (**stark NP-schwer**). Aufwand wird in **Tabellenzellen und Zuständen** gezählt, nicht in Sekunden.
Fünftes Stück der Komplexitätsklassen-Reihe; die Fall-Demos behandeln einzelne Anwendungen, hier steht eine Frage der Komplexitätstheorie im Mittelpunkt.

Weiter unten: die Experimente **🔬 Wie wächst die Tabelle mit den Stellen?**, **🔬 Was kostet Genauigkeit?**, **🔬 Die Falle** und **🔬 Schwach gegen stark NP-schwer**,
dann **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("Drei Begriffe", expanded=True):
    st.markdown(
        """
1. **Pseudopolynomiell.** Die Tabelle der exakten Rechnung hat n · (W + 1) Zellen (n Pakete, Kapazität W): polynomial im **Wert** von W, aber W hat bei d Stellen etwa 10^d. Für die **Länge** der Eingabe (die Stellen) ist das exponentiell.
2. **FPTAS.** Rundet man die Werte auf Vielfache eines Schritts K = ε · (größter Wert) / n, wird die Tabelle klein (sie hängt nur noch von n und 1 / ε ab), und das Ergebnis ist garantiert mindestens (1 − ε) mal das Optimum. Die Garantie ist ein Schlimmster-Fall-Satz.
3. **Stark NP-schwer.** Bei manchen Problemen bleibt die Härte, auch wenn alle Zahlen klein sind (zum Beispiel 3-Partition: 3m Zahlen in m Gruppen mit gleicher Summe). Dort gibt es unter P ≠ NP weder ein pseudopolynomielles Verfahren noch (für Optimierungsprobleme mit polynomial beschränktem Zielwert) ein FPTAS.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Fuhre packen**")
    n = st.slider("Pakete n", *bounds("n_slider"), key="n_slider", help="Pakete mit Gewicht und Wert. Auch die Falle und die Güte-Messreihe verwenden diese Zahl.")
    d = st.slider("Stellen der Gewichte", *bounds("d_slider"), key="d_slider", help="Gewichte gleichverteilt in 1 bis 10^Stellen. Jede Stelle mehr macht die exakte Tabelle etwa zehnmal größer.")
    seed = st.number_input("Zufalls-Seed der Pakete", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Pakete generieren", width="stretch", on_click=randomize_seed)
    family = st.selectbox("Familie der Pakete", list(C.FAMILIES), format_func=C.FAMILIES.get, key="family_select",
                          help="Unkorreliert: Wert unabhängig vom Gewicht. Stark korreliert: Wert = Gewicht + ein Zehntel des größten Gewichts. Teilsumme: Wert = Gewicht.")
    eps = st.select_slider("Genauigkeit ε des FPTAS", options=list(C.EPS_OPTIONS), format_func=fmt_eps, key="eps_select",
                           help="Garantiert wird mindestens (1 − ε) mal das Optimum. Kleineres ε heißt feinere Rundung und größere Tabelle.")
    st.markdown("**Verteilung auf Behälter (Experiment 3)**")
    bins = st.select_slider("Behälter m", options=list(C.BINS_OPTIONS), key="bins_select", help=f"{C.BIN_NUMBERS_N} Zahlen werden möglichst gleichmäßig auf m Behälter verteilt.")
    bmax = st.select_slider("Zahlen bis B", options=list(C.BMAX_OPTIONS), key="bmax_select", help="Die Zahlen sind gleichverteilt in 1 bis B.")

sync_query_params({"n_slider": int(n), "d_slider": int(d), "seed_input": int(seed), "family_select": family, "eps_select": float(eps), "bins_select": int(bins), "bmax_select": int(bmax)})

settings = Settings(n=int(n), d=int(d), seed=int(seed), family=family, eps=float(eps), bins=int(bins), bmax=int(bmax))
a = _analysis(settings)
inst = a.instance
for message in validation_errors(a):
    st.error(message)

# --- Eine Instanz --------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Eine Instanz, zwei Rechnungen")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Optimum (exakt)", fmt_int(a.exact.value), help="Größter Gesamtwert, der in die Kapazität passt.")
c2.metric("Wert des FPTAS", fmt_int(a.fptas.value), help="Echter Gesamtwert der Menge, die das FPTAS nach dem Runden wählt.")
c3.metric("Güte des FPTAS", fmt_quality(a.quality), help=f"Wert des FPTAS geteilt durch das Optimum. Garantiert sind bei ε = {fmt_eps(settings.eps)} mindestens {fmt_guarantee(settings.eps)}.")
c4.metric("Kapazität W", fmt_int(inst.capacity), help="40 % der Gewichtssumme.")
c5, c6, c7 = st.columns(3)
c5.metric("Zellen der exakten Tabelle", fmt_int(a.exact.cells), help="n · (W + 1).")
c6.metric("Zellen der FPTAS-Tabelle", fmt_int(a.fptas.cells), help="n · (Summe der gerundeten Werte + 1).")
c7.metric("Rundungsschritt K", fmt_k(a.fptas.k), help="ε · (größter Wert) / n: alle Werte werden auf Vielfache von K abgerundet.")
vkind, vtext = verdict_run(a)
getattr(st, vkind)(vtext)
g1, g2 = st.columns([3, 2])
with g1:
    st.plotly_chart(build_items(inst, a.exact.chosen, a.fptas.chosen), width="stretch", key="items_fig")
    if a.exact.chosen is None:
        st.caption(f"Die gewählte Menge der exakten Rechnung zeigt die App nur bis {fmt_int(C.CHOICE_LIMIT)} Tabellenzellen (dafür muss die ganze Tabelle im Speicher liegen); der Wert ist trotzdem exakt.")
with g2:
    st.plotly_chart(build_cells(a.exact.cells, a.fptas.cells), width="stretch", key="cells_fig")
if a.exact.chosen is not None:
    st.markdown(f"**Gewählt (exakt):** Pakete {_packages(a.exact.chosen)}.  **Gewählt (FPTAS):** Pakete {_packages(a.fptas.chosen)}.")
else:
    st.markdown(f"**Gewählt (FPTAS):** Pakete {_packages(a.fptas.chosen)}.")
if a.table is not None:
    with st.expander("Die ganze Tabelle der exakten Rechnung", expanded=True):
        st.plotly_chart(build_table(a.table, inst.weights, inst.values), width="stretch", key="table_fig")
        st.caption("Jedes Feld: bester Wert bei dieser Kapazität, wenn nur die Pakete bis zu dieser Zeile zur Wahl stehen. Das Optimum steht unten rechts.")
if st.button("📄 PDF erstellen"):
    st.session_state["pdf_for"] = settings
if st.session_state.get("pdf_for") == settings:
    st.download_button("⬇️ PDF herunterladen", data=_pdf(settings), file_name="zahlen-und-haerte.pdf", mime="application/pdf")

st.markdown("## ❓ Kernfrage: Was kostet die Größe der Zahlen, und was kauft man mit Genauigkeit?")
st.markdown(
    "Die Experimente trennen drei Dinge: wie die exakte Tabelle mit den **Stellen** wächst (pseudopolynomiell), was das **Runden** an Tabelle spart und an Güte kostet (FPTAS), und warum bei der "
    "**Verteilung auf Behälter** kleine Zahlen nicht retten, wenn die Behälterzahl mitwächst (stark NP-schwer)."
)

st.markdown("---")

# --- Experimente --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie wächst die Tabelle mit den Stellen?")
st.caption(f"{len(C.E1_SEEDS)} feste Instanzen je Stellenzahl ({C.E1_N} Pakete, unkorreliert, Kapazität 40 % der Gewichtssumme), Median. Die Zellenzahl ist die Tabellengröße, n · (W + 1) bzw. n · (P + 1), aus der Formel und nicht im Lauf gezählt. "
           f"Ab 7 Stellen wird die exakte Tabelle in der App nicht mehr gerechnet, nur gezählt. Die gestrichelte Linie markiert die gewählten Stellen.")
digits_rows = _digits()
st.plotly_chart(build_digits(digits_rows, highlight_d=settings.d), width="stretch", key="digits_chart")
st.markdown(_md_table(
    ["Stellen", "Zellen exakt (Median)"] + [f"Zellen FPTAS, ε = {fmt_eps(e)}" for e in digits_rows[0]["fptas"]],
    [[r["d"], fmt_median(r["exact"])] + [fmt_median(r["fptas"][e]) for e in r["fptas"]] for r in digits_rows],
))
vkind, vtext = verdict_digits(digits_rows)
getattr(st, vkind)(vtext)

st.markdown("---")

st.subheader("🔬 Experiment: Was kostet Genauigkeit?")
st.caption(f"{len(C.SWEEP_SEEDS)} feste Instanzen mit {settings.n} Paketen (Regler) der Familie „{C.FAMILIES[settings.family]}“ (Regler), Gewichte bis {fmt_int(10 ** C.E2_DIGITS)}; je ε die exakte Rechnung als Maßstab. "
           f"Die Linie „Garantie“ ist das, was der Satz zusagt; die Messpunkte sind das, was auf diesen Instanzen herauskam.")
eps_rows = _eps(settings.n, settings.family)
h1, h2 = st.columns(2)
with h1:
    st.plotly_chart(build_eps_quality(eps_rows, highlight_eps=settings.eps), width="stretch", key="eps_quality_chart")
with h2:
    st.plotly_chart(build_eps_cells(eps_rows), width="stretch", key="eps_cells_chart")
st.markdown(_md_table(
    ["ε", "garantiert", "kleinste Güte", "mittlere Güte (Median)", "exakt optimal", "Zellen FPTAS (Median)", "Zellen exakt (Median)"],
    [[fmt_eps(r["eps"]), fmt_guarantee(r["eps"]), fmt_quality(r["min"]), fmt_quality(r["median"]), f"{r['exact_hits']} von {r['count']}", fmt_median(r["cells_fptas"]), fmt_median(r["cells_exact"])] for r in eps_rows],
))
vkind, vtext = verdict_eps(eps_rows)
getattr(st, vkind)(vtext)
fam_rows = _families(settings.n)
st.markdown("**Die drei Familien im Vergleich** (kleinste Güte über die festen Instanzen)")
st.markdown(_md_table(
    ["Familie"] + [f"ε = {fmt_eps(e)}: kleinste / mittlere Güte" for e in C.E2_EPS_FAMILIES],
    [[C.FAMILIES[f]] + [f"{fmt_quality(r['min'])} / {fmt_quality(r['median'])}" for e in C.E2_EPS_FAMILIES for r in fam_rows if r["family"] == f and r["eps"] == e] for f in C.FAMILIES],
))
vkind, vtext = verdict_families(fam_rows)
getattr(st, vkind)(vtext)

st.markdown("---")

st.subheader("🔬 Experiment: Die Falle")
st.caption(
    "Zufällige Instanzen bleiben weit über der Garantie. Hier ist eine **gebaute** Instanz, die sie ausreizt: ein großes Paket gegen n − 1 kleine, deren gerundete Werte zusammen knapp weniger zählen, "
    "deren echte Werte zusammen aber mehr sind. Das FPTAS wählt das große Paket. Die Falle hängt nur von n und ε (Regler) ab."
)
t = a.trap
vkind, vtext = verdict_trap(t)
getattr(st, vkind)(vtext)
trap_rows = _trap()
st.plotly_chart(build_trap(trap_rows, highlight=t), width="stretch", key="trap_chart")
vkind, vtext = verdict_trap_sweep(trap_rows)
getattr(st, vkind)(vtext)

st.markdown("---")

st.subheader("🔬 Experiment: Schwach gegen stark NP-schwer")
st.caption(
    f"**Behälter-DP:** {C.BIN_NUMBERS_N} Zahlen sollen so auf m Behälter verteilt werden, dass kein Behälter mehr als ⌈Summe / m⌉ trägt. Ein **Zustand** ist der sortierte Lastvektor der m Behälter; "
    "die Rechnung zählt die verschiedenen Zustände nach jeder Zahl. Bei fester Behälterzahl ist das polynomial in den Zahlen (schwach NP-schwer, etwa Partition mit m = 2), bei wachsender Behälterzahl nicht "
    "(3-Partition, stark NP-schwer)."
)
vkind, vtext = verdict_bins_live(a.bins, settings.bins, settings.bmax)
getattr(st, vkind)(vtext)
if a.bins.states.steps:
    st.plotly_chart(build_bin_steps(a.bins.states), width="stretch", key="bin_steps_chart")
    st.caption(f"Zahlen dieser Verteilung (Zufalls-Seed, Behälter und B aus den Reglern): {', '.join(str(x) for x in a.bins.items)}.")
st.markdown("**Bei fester Behälterzahl: die Zahlen wachsen**")
st.caption(f"Je Behälterzahl und B {len(C.BIN_FIXED_SEEDS)} feste Verteilungen, Median der Zustandsspitze, beide Achsen logarithmisch (eine Gerade ist ein Potenzgesetz). Rund 20 Sekunden.")
if st.button("▶️ Messreihe feste Behälterzahl rechnen"):
    st.session_state["fixed_on"] = True
if st.session_state.get("fixed_on"):
    with st.spinner("Rechne die Zustandsräume (3 Behälterzahlen, 4 Zahlenbereiche, 5 Verteilungen) …"):
        fixed_rows = _bins_fixed()
    st.plotly_chart(build_bins_fixed(fixed_rows), width="stretch", key="bins_fixed_chart")
    st.markdown(_md_table(
        ["Behälter m"] + [f"B = {b}" for b in C.BIN_FIXED_B],
        [[m] + [fmt_median(r["peak"]) for b in C.BIN_FIXED_B for r in fixed_rows if r["m"] == m and r["b"] == b] for m in C.BIN_FIXED_M],
    ))
    vkind, vtext = verdict_bins_fixed(fixed_rows)
    getattr(st, vkind)(vtext)
st.markdown("**Bei festen Zahlen: die Behälterzahl wächst (3-Partition)**")
st.caption(f"Geplante 3-Partition-Instanzen mit B = {C.PLANT_B}: 3m Zahlen, jede zwischen 25 und 50, die sich in m Dreiergruppen mit Summe {C.PLANT_B} zerlegen lassen. {len(C.PLANT_SEEDS)} feste Instanzen je m. Rund 10 Sekunden.")
if st.button("▶️ Messreihe 3-Partition rechnen"):
    st.session_state["plant_on"] = True
if st.session_state.get("plant_on"):
    with st.spinner("Rechne die Zustandsräume der 3-Partition (m = 2 bis 7) …"):
        plant_rows = _plant()
    st.plotly_chart(build_plant(plant_rows), width="stretch", key="plant_chart")
    st.markdown(_md_table(
        ["Behälter m", "Zahlen", "Zustände (Median der Spitze)", "kleinster", "größter"],
        [[r["m"], 3 * r["m"], fmt_median(r["peak"]), fmt_int(r["min"]), fmt_int(r["max"])] for r in plant_rows],
    ))
    vkind, vtext = verdict_plant(plant_rows)
    getattr(st, vkind)(vtext)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Zellen sind keine Laufzeit** | Eine Zelle kostet je nach Verfahren verschieden viel; gezählt wird die Größe der Tabellen, nicht die Rechenzeit. | – |
| **Die Garantie beschreibt typische Instanzen** | Sie ist eine Schlimmster-Fall-Aussage. Auf den Zufallsinstanzen liegt die Güte weit darüber; erst die gebaute Falle kommt ihr näher. | – |
| **Zufällige Instanzen zeigen die Härte** | Tun sie nicht: eine einfache Suche löste in einer Probe (nicht Teil dieser Demo, keine Zahl) zufällig gezogene 3-Partition-Instanzen fast sofort. Stark NP-schwer ist eine Aussage über den schlimmsten Fall. Gezeigt wird deshalb der Zustandsraum, nicht die Rechenzeit einer Suche. | – |
| **Die Behälter-DP ist das beste Verfahren** | Sie ist die einfachste Tabelle ohne Dominanzregeln; bessere Verfahren verkleinern den Zustandsraum, ändern aber nichts an seiner Gestalt (Exponent mit m). | `cutting-stock-dp-demo` |
| **„Stark NP-schwer ⇒ kein FPTAS“ ist bewiesen** | Es gilt unter der Annahme P ≠ NP, und die Demo beweist es nicht: sie zeigt nur den Zustandsraum. Der Satz folgt aus dem Standardargument von Garey und Johnson (1978). | – |
| **Wert-Skalierung ist die beste Rundung** | Es gibt schnellere FPTAS-Varianten für den Rucksack; die Demo baut die einfachste, damit jede Zelle der Tabelle erklärbar bleibt. | `dynamic-programming-demo`, `branch-bound-demo` |
| **Ein Rucksack steht für alle Zahlenprobleme** | Die Aussagen über Tabellen und Rundung gelten für diese Rucksack-Instanzen und diese Größen (bis 50 Pakete, Gewichte bis 10^6); die Härte-Begriffe sind allgemein, die Messwerte nicht. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(r"**Exakte Tabelle.** Mit Gewichten $w_i$, Werten $v_i$ und Kapazität $W$ ist $f(i, c)$ der beste Wert mit den ersten $i$ Paketen bei Kapazität $c$:")
    st.latex(r"f(i, c) = \max\big( f(i-1, c),\; f(i-1, c - w_i) + v_i \big), \qquad f(0, c) = 0")
    st.markdown(r"Die Tabelle hat $n \cdot (W + 1)$ Zellen. $W$ hat $d$ Stellen, also $W \approx 10^d$: **linear im Wert, exponentiell in der Länge** $d$ der Eingabe (pseudopolynomiell).")
    st.markdown(r"**Rundung.** Mit $v_{\max}$ dem größten Wert eines Pakets, das einzeln passt, und $n$ der Zahl dieser Pakete:")
    st.latex(r"K = \frac{\varepsilon \, v_{\max}}{n}, \qquad p_i = \Big\lfloor \frac{v_i}{K} \Big\rfloor, \qquad g(i, q) = \min \Big\{ \textstyle\sum_{j \in S} w_j \;:\; S \subseteq \{1..i\},\ \sum_{j \in S} p_j = q \Big\}")
    st.markdown(r"Die Tabelle $g$ hat $n \cdot (P + 1)$ Zellen mit $P = \sum_i p_i \le n \cdot n / \varepsilon$, also höchstens $n^3 / \varepsilon$ Zellen, unabhängig von der Größe der Gewichte.")
    st.markdown(r"**Güte.** Sei $S^\ast$ die optimale Menge und $S_A$ die Wahl des FPTAS. Wegen $v_i < K (p_i + 1)$ gilt $K p_i > v_i - K$ und damit:")
    st.latex(r"v(S_A) \;\ge\; K \sum_{i \in S_A} p_i \;\ge\; K \sum_{i \in S^\ast} p_i \;\ge\; \sum_{i \in S^\ast} (v_i - K) \;\ge\; \mathrm{OPT} - nK = \mathrm{OPT} - \varepsilon \, v_{\max} \;\ge\; (1 - \varepsilon)\, \mathrm{OPT}")
    st.markdown(r"**Behälter-DP.** Ein Zustand ist der sortierte Lastvektor der $m$ Behälter, jede Last höchstens $T$. Die Zahl der Zustände ist höchstens die Zahl der Multimengen der Größe $m$ aus $\{0, \dots, T\}$:")
    st.latex(r"\binom{T + m}{m} \;\approx\; \frac{T^m}{m!}")
    st.markdown(
        r"""
Für **feste** $m$ ist das polynomial in $T$ (den Zahlen), für wachsendes $m$ (3-Partition: $m = n / 3$) nicht.

| Annahme | Bedeutung | Wer setzt an |
|---|---|---|
| Gewichte ganze Zahlen ≥ 1 | die Tabelle über die Kapazität ist definiert | – |
| Pakete, die einzeln nicht passen, entfallen | $n$ in $K$ zählt nur die passenden Pakete | – |
| Rundung nach unten | $p_i = \lfloor v_i / K \rfloor$: nie mehr als der echte Wert | – |
| Gleichstände | die Wahl der Menge bei gleicher gerundeter Summe ist deterministisch (die erste gefundene) | – |
| Zustände sortiert | Behälter sind austauschbar: gleiche Lasten sind derselbe Zustand | – |

**Folgestücke.** Stück 6 der Reihe (Approximation und Nichtapproximierbarkeit) fragt, wo eine Garantie nicht zu haben ist, Stück 7 (parametrisierte Komplexität) und Stück 8 (Zufall) zeigen weitere Auswege.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
