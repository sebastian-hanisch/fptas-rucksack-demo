"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import fpr_constants as C
from fpr_evaluation import fmt_eps, fmt_int


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_items(inst, exact_chosen, fptas_chosen):
    """Die Pakete als Punkte (Gewicht, Wert): von beiden gewählt, nur exakt, nur FPTAS, nicht gewählt. Ohne `exact_chosen` (große Tabelle) nur die Wahl des FPTAS."""
    exact = None if exact_chosen is None else set(exact_chosen)
    fptas = set(fptas_chosen)
    groups = []
    if exact is None:
        groups = [("vom FPTAS gewählt", fptas, C.COLOR_FPTAS), ("nicht gewählt", set(range(inst.n)) - fptas, C.COLOR_OTHER)]
    else:
        groups = [("von beiden gewählt", exact & fptas, C.COLOR_FPTAS), ("nur exakt gewählt", exact - fptas, C.COLOR_EXACT),
                  ("nur vom FPTAS gewählt", fptas - exact, C.COLOR_TRAP), ("nicht gewählt", set(range(inst.n)) - exact - fptas, C.COLOR_OTHER)]
    fig = go.Figure()
    for name, members, color in groups:
        idx = sorted(members)
        if not idx:
            continue
        fig.add_trace(go.Scatter(x=[inst.weights[i] for i in idx], y=[inst.values[i] for i in idx], mode="markers", name=name, marker=dict(color=color, size=10),
                                 text=[f"Paket {i + 1}" for i in idx], hovertemplate="%{text}<br>Gewicht %{x}<br>Wert %{y}<extra></extra>"))
    fig.update_xaxes(title="Gewicht")
    fig.update_yaxes(title="Wert")
    return _base(fig, 340)


def build_cells(exact_cells: int, fptas_cells: int):
    """Tabellenzellen der exakten Rechnung gegen die des FPTAS (logarithmische Achse)."""
    fig = go.Figure(go.Bar(x=["exakte Rechnung", "FPTAS"], y=[exact_cells, fptas_cells], marker_color=[C.COLOR_EXACT, C.COLOR_FPTAS],
                           text=[fmt_int(exact_cells), fmt_int(fptas_cells)], textposition="outside", hovertemplate="%{x}: %{text} Zellen<extra></extra>"))
    fig.update_yaxes(type="log", title="Zellen der Tabelle")
    return _base(fig, 300)


def build_table(table, weights, values):
    """Die ganze Tabelle der exakten Rechnung als Bild: Zeile i = nach den ersten i Paketen, Spalte c = Kapazität c; Zahlen in den Feldern."""
    labels = ["vor dem ersten Paket"] + [f"+ Paket {i + 1} (Gewicht {weights[i]}, Wert {values[i]})" for i in range(len(weights))]
    fig = go.Figure(go.Heatmap(z=[list(r) for r in table], x=list(range(len(table[0]))), y=labels, text=[[str(v) for v in r] for r in table], texttemplate="%{text}",
                               colorscale="Teal", showscale=False, hovertemplate="%{y}<br>Kapazität %{x}: Wert %{z}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Kapazität", dtick=1)
    return _base(fig, 60 + 32 * len(labels))


def build_digits(rows, highlight_d=None):
    """Zellen über die Stellen der Gewichte (logarithmisch): exakte Tabelle gegen FPTAS je ε; die gewählten Stellen sind markiert."""
    fig = go.Figure()
    ds = [r["d"] for r in rows]
    fig.add_trace(go.Scatter(x=ds, y=[r["exact"] for r in rows], mode="lines+markers", name="exakte Tabelle n · (W + 1)", line=dict(color=C.COLOR_EXACT)))
    for color, e in zip(C.COLOR_SERIES, rows[0]["fptas"]):
        fig.add_trace(go.Scatter(x=ds, y=[r["fptas"][e] for r in rows], mode="lines+markers", name=f"FPTAS, ε = {fmt_eps(e)}", line=dict(color=color)))
    chosen = [r for r in rows if r["d"] == highlight_d]
    if chosen:
        fig.add_trace(go.Scatter(x=[highlight_d], y=[chosen[0]["exact"]], mode="markers", name="gewählte Stellen", marker=dict(symbol="diamond-open", size=16, color=C.COLOR_GUARANTEE, line=dict(width=2))))
    fig.update_xaxes(title="Stellen der Gewichte", dtick=1)
    fig.update_yaxes(type="log", title="Zellen der Tabelle (Median)")
    return _base(fig)


def build_eps_quality(rows, highlight_eps=None):
    """Güte über ε: kleinste und mittlere Güte der festen Instanzen gegen die Garantie 1 - ε; das gewählte ε ist markiert."""
    xs = [fmt_eps(r["eps"]) for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[1 - r["eps"] for r in rows], mode="lines+markers", name="Garantie 1 − ε", line=dict(color=C.COLOR_GUARANTEE, dash="dash")))
    fig.add_trace(go.Scatter(x=xs, y=[float(r["min"]) for r in rows], mode="lines+markers", name="kleinste gemessene Güte", line=dict(color=C.COLOR_FPTAS)))
    fig.add_trace(go.Scatter(x=xs, y=[float(r["median"]) for r in rows], mode="lines+markers", name="mittlere (Median) Güte", line=dict(color=C.COLOR_EXACT)))
    chosen = [r for r in rows if r["eps"] == highlight_eps]
    if chosen:
        fig.add_trace(go.Scatter(x=[fmt_eps(highlight_eps)], y=[float(chosen[0]["min"])], mode="markers", name="gewähltes ε", marker=dict(symbol="diamond-open", size=16, color=C.COLOR_TRAP, line=dict(width=2))))
    fig.update_xaxes(title="ε", type="category")
    fig.update_yaxes(title="Güte = Wert / Optimum", range=[0.4, 1.03])
    return _base(fig)


def build_eps_cells(rows):
    """Zellen über ε: FPTAS (wächst mit 1 / ε) gegen die feste exakte Tabelle."""
    xs = [fmt_eps(r["eps"]) for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["cells_fptas"] for r in rows], name="FPTAS", marker_color=C.COLOR_FPTAS))
    fig.add_trace(go.Scatter(x=xs, y=[r["cells_exact"] for r in rows], mode="lines+markers", name="exakte Rechnung", line=dict(color=C.COLOR_EXACT)))
    fig.update_xaxes(title="ε", type="category")
    fig.update_yaxes(type="log", title="Zellen (Median)")
    return _base(fig)


def build_trap(rows, highlight=None):
    """Güte der Falle über ε für mehrere Größen, gegen die Garantie 1 - ε; `highlight` (TrapResult) markiert die Falle mit den gewählten Reglern."""
    eps_values = sorted({r["eps"] for r in rows}, reverse=True)
    xs = [fmt_eps(e) for e in eps_values]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[1 - e for e in eps_values], mode="lines+markers", name="Garantie 1 − ε", line=dict(color=C.COLOR_GUARANTEE, dash="dash")))
    for color, n in zip(C.COLOR_SERIES[1:], sorted({r["n"] for r in rows})):
        by = {r["eps"]: float(r["quality"]) for r in rows if r["n"] == n}
        fig.add_trace(go.Scatter(x=xs, y=[by[e] for e in eps_values], mode="lines+markers", name=f"Falle mit {n} Paketen", line=dict(color=color)))
    if highlight is not None:
        fig.add_trace(go.Scatter(x=[fmt_eps(highlight.eps)], y=[highlight.fptas_value / highlight.opt_value], mode="markers", name=f"gewählt: {highlight.n} Pakete",
                                 marker=dict(symbol="diamond-open", size=16, color=C.COLOR_TRAP, line=dict(width=2))))
    fig.update_xaxes(title="ε", type="category")
    fig.update_yaxes(title="Güte = Wert / Optimum", range=[0.4, 1.03])
    return _base(fig)


def build_bin_steps(states):
    """Zustände nach jeder Zahl (Behälter-DP, eine Verteilung)."""
    fig = go.Figure(go.Bar(x=list(range(1, len(states.steps) + 1)), y=list(states.steps), marker_color=C.COLOR_EXACT, hovertemplate="nach Zahl %{x}: %{y} Zustände<extra></extra>"))
    fig.update_xaxes(title="Zahl Nr.")
    fig.update_yaxes(title="Zustände")
    return _base(fig, 280)


def build_bins_fixed(rows):
    """Zustandsspitze über B bei fester Behälterzahl, beide Achsen logarithmisch: eine Gerade ist ein Potenzgesetz (polynomial)."""
    fig = go.Figure()
    for color, m in zip(C.COLOR_SERIES, sorted({r["m"] for r in rows})):
        rs = [r for r in rows if r["m"] == m]
        fig.add_trace(go.Scatter(x=[r["b"] for r in rs], y=[r["peak"] for r in rs], mode="lines+markers", name=f"{m} Behälter", line=dict(color=color)))
    fig.update_xaxes(type="log", title="Zahlen bis B")
    fig.update_yaxes(type="log", title="Zustände (Median der Spitze)")
    return _base(fig)


def build_plant(rows):
    """Zustandsspitze über die Behälterzahl bei festen Zahlen (logarithmische y-Achse): eine Gerade ist exponentielles Wachstum; Band = kleinster bis größter Wert der geplanten Instanzen."""
    ms = [r["m"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ms + ms[::-1], y=[r["max"] for r in rows] + [r["min"] for r in rows][::-1], fill="toself", fillcolor="rgba(76,120,168,0.18)", line=dict(width=0),
                             hoverinfo="skip", name="kleinster bis größter Wert"))
    fig.add_trace(go.Scatter(x=ms, y=[r["peak"] for r in rows], mode="lines+markers", name="Median der Spitze", line=dict(color=C.COLOR_EXACT)))
    fig.update_xaxes(title="Behälterzahl m (3-Partition, 3m Zahlen, B = 100)", dtick=1)
    fig.update_yaxes(type="log", title="Zustände")
    return _base(fig)
