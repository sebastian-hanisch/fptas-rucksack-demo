"""Randfälle auf App-Ebene: jede Reglerkombination an den Grenzen liefert eine geprüfte Analyse (keine Fehlermeldung der Prüfungen vor der Anzeige)."""

import pytest

import fpr_algorithm as A
import fpr_constants as C
import fpr_evaluation as ev


@pytest.mark.parametrize("family", list(C.FAMILIES))
@pytest.mark.parametrize("n, d", [(C.N_MIN, C.D_MIN), (C.N_MIN, C.D_MAX), (C.N_MAX, C.D_MIN), (12, 4)])
def test_extremes_of_the_instance_sliders_are_clean(family, n, d):
    a = ev.analyse(ev.Settings(n=n, d=d, family=family))
    assert ev.validation_errors(a) == []
    assert a.exact.value > 0 and a.fptas.value <= a.exact.value


@pytest.mark.parametrize("eps", [C.EPS_OPTIONS[0], C.EPS_OPTIONS[-1]])
def test_extremes_of_epsilon_keep_the_guarantee(eps):
    a = ev.analyse(ev.Settings(eps=eps))
    assert ev.validation_errors(a) == []
    assert a.quality >= 1 - A.to_fraction(eps)


@pytest.mark.parametrize("bins", C.BINS_OPTIONS)
@pytest.mark.parametrize("bmax", C.BMAX_OPTIONS)
def test_every_bin_setting_is_decided_below_the_state_cap(bins, bmax):
    a = ev.analyse(ev.Settings(bins=bins, bmax=bmax))
    assert not a.bins.states.aborted and ev.validation_errors(a) == []


def test_the_maximum_instance_is_clean():
    a = ev.analyse(ev.Settings(n=C.N_MAX, d=C.D_MAX))
    assert a.exact.chosen is None and ev.validation_errors(a) == []
    assert a.exact.cells > 100_000_000                                    # die Rechengrenze am Reglermaximum ist spürbar groß, aber gerechnet


@pytest.mark.parametrize("seed", [0, C.SEED_MAX])
def test_seed_bounds(seed):
    assert ev.validation_errors(ev.analyse(ev.Settings(seed=seed))) == []
