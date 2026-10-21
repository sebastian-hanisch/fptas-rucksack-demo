"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; jede Voreinstellung ergibt eine geprüfte Analyse."""

import pytest

import fpr_constants as C
import fpr_evaluation as ev
import fpr_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            if spec.options is not None:
                assert preset[key] in spec.options, (name, key)
            else:
                assert spec.lo <= preset[key] <= spec.hi, (name, key)


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_defaults_of_the_specs_equal_the_constants():
    assert {k: s.default for k, s in P.SETTING_SPECS.items()} == {
        "n_slider": C.DEFAULT_N, "d_slider": C.DEFAULT_D, "seed_input": C.DEFAULT_SEED, "family_select": C.DEFAULT_FAMILY,
        "eps_select": C.DEFAULT_EPS, "bins_select": C.DEFAULT_BINS, "bmax_select": C.DEFAULT_BMAX}


def test_url_parameters_are_unique():
    params = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(set(params)) == len(params)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_gives_a_clean_analysis(name):
    a = ev.analyse(ev.Settings(**C.PRESETS[name]))
    assert ev.validation_errors(a) == []


def test_the_teaching_preset_shows_the_whole_table():
    a = ev.analyse(ev.Settings(**C.PRESETS["Lehrbeispiel (8 Pakete)"]))
    assert a.table is not None


def test_coerce_reads_and_clamps_permalink_values():
    spec = P.SETTING_SPECS["n_slider"]
    assert P._coerce(spec, "99") == C.N_MAX and P._coerce(spec, "1") == C.N_MIN and P._coerce(spec, ["12"]) == 12 and P._coerce(spec, "x") is None
    eps = P.SETTING_SPECS["eps_select"]
    assert P._coerce(eps, "0.05") == 0.05 and P._coerce(eps, "0.07") is None
    fam = P.SETTING_SPECS["family_select"]
    assert P._coerce(fam, "sub") == "sub" and P._coerce(fam, "zzz") is None
