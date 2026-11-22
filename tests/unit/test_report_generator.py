import pytest
from osdagbridge.core.reports.report_utils import (
    _tex,
    _render_value,
    get_girder_entries,
    _fig_or_placeholder,
    _fig_embed,
)
from osdagbridge.core.reports.chap1 import ch1_project_info
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.chap8 import ch8_design_log
from osdagbridge.core.reports.report_generator import ReportMetadata
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GD_MEMBER_ID,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_ZONE_FACTOR,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
)


def test_tex_escaping():
    """Verify LaTeX character escaping and glyph replacements."""
    assert _tex("A & B % C $ D # E _ F ~ G ^ H { I }") == (
        r"A \& B \% C \$ D \# E \_\allowbreak{} F \textasciitilde{} G \^{} H \{ I \}"
    )
    # Glyph normalisation: '∠' -> 'L', 'ⅹ' -> 'x', '×' -> 'x'
    assert _tex("∠ 100 ⅹ 100 × 10") == "L 100 x 100 x 10"
    assert _tex(None) == ""
    assert _tex("") == ""


def test_render_value():
    """Verify _render_value formatting and missing key handling."""
    data = {"span": "30.0", "empty": ""}
    assert _render_value(data, "span", " m") == "30.0 m"
    assert _render_value(data, "empty", " m") == ""
    assert _render_value(data, "non_existent", " m") == ""


def test_get_girder_entries():
    """Verify dynamic girder entry retrieval."""
    input_dict = {
        KEY_TS_NO_OF_GIRDERS: "3",
        f"{KEY_MP_GD_SELECT_GIRDER}.G1": "Girder 1",
        f"{KEY_MP_GD_MEMBER_ID}.G1.M1": "G1M1",
        f"{KEY_MP_GD_SELECT_GIRDER}.G2": "Girder 2",
        f"{KEY_MP_GD_MEMBER_ID}.G2.M1": "G2M1",
        f"{KEY_MP_GD_SELECT_GIRDER}.G3": "Girder 3",
        f"{KEY_MP_GD_MEMBER_ID}.G3.M1": "G3M1",
    }
    entries = get_girder_entries(input_dict)
    assert len(entries) == 3
    assert entries[0] == ("Girder 1", "G1M1")
    assert entries[1] == ("Girder 2", "G2M1")
    assert entries[2] == ("Girder 3", "G3M1")

    # When no girders
    assert get_girder_entries({}) == []


def test_figure_helpers():
    """Verify figure embedding and placeholder generation."""
    ph = _fig_or_placeholder(None, "Test Caption")
    assert "[ PLACEHOLDER: Test Caption ]" in ph

    fig = _fig_or_placeholder("images/test.png", "Test Caption")
    assert r"\includegraphics[width=0.9\textwidth]{images/test.png}" in fig
    assert "Test Caption" in fig

    ph_emb = _fig_embed(None, "Embed Caption")
    assert "[ PLACEHOLDER: Embed Caption ]" in ph_emb

    fig_emb = _fig_embed("images/test_emb.png", "Embed Caption")
    assert r"\includegraphics[width=\textwidth]{images/test_emb.png}" in fig_emb


def test_latex_group_balance_chap7():
    """Verify \\begingroup and \\endgroup are balanced in chap7."""
    tex = ch7_quantities({})
    assert tex.count(r"\begingroup") == tex.count(r"\endgroup")
    assert tex.count(r"\begingroup") == 1


def test_latex_group_balance_chap8():
    """Verify \\begingroup and \\endgroup are balanced in chap8."""
    tex = ch8_design_log([], {"design_mode": "Optimized"})
    assert tex.count(r"\begingroup") == tex.count(r"\endgroup")
    assert tex.count(r"\begingroup") == 2


def test_footway_load_display_automatic():
    """Verify footway load displays computed value in automatic IRC 6 mode."""
    inp = {
        KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6",
    }
    tex = ch3_loads(inp)
    assert "Footpath Live Load (if applicable)" in tex
    # IRC 6 Clause 206.1 default footway load is 500 kg/m2 = 4.905 or 5.0 kN/m2
    assert "kN/m² (IRC 6 Cl. 206.1)" in tex


def test_footway_load_display_manual():
    """Verify footway load displays manual pressure value when specified."""
    inp = {
        KEY_LL_FOOTPATH_PRESSURE_MODE: "Manual",
        KEY_LL_FOOTPATH_PRESSURE_VALUE: "4.5",
    }
    tex = ch3_loads(inp)
    assert "Footpath Live Load (if applicable)" in tex
    assert "4.5 kN/m²" in tex


def test_footway_load_display_missing():
    """Verify footway load displays N/A when no mode or value specified."""
    inp = {}
    tex = ch3_loads(inp)
    assert "Footpath Live Load (if applicable)" in tex
    assert "N/A" in tex


def test_seismic_force_display_from_output_dict():
    """Verify seismic forces display values when supplied in output_dict."""
    inp = {}
    out = {
        "seismic_force_longitudinal": 125.456,
        "seismic_force_transverse": 150.789,
    }
    tex = ch3_loads(inp, out)
    assert "Horizontal Seismic Force (longitudinal)" in tex
    assert "125.46 kN" in tex
    assert "Horizontal Seismic Force (transverse)" in tex
    assert "150.79 kN" in tex


def test_seismic_force_display_derived_from_irc6():
    """Verify seismic forces derive from IRC 6 when inputs are present."""
    inp = {
        KEY_SL_SEISMIC_ZONE: "Zone III",
        KEY_SL_DEAD_LOAD_MODE: "Custom",
        KEY_SL_DEAD_LOAD_VALUE: "1000",
        KEY_SL_LIVE_LOAD_MODE: "Custom",
        KEY_SL_LIVE_LOAD_VALUE: "500",
        "soil_type": "Type I – Rocky or Hard",
    }
    tex = ch3_loads(inp, {})
    assert "Horizontal Seismic Force (longitudinal)" in tex
    assert "Horizontal Seismic Force (transverse)" in tex
    # Values should be computed and non-empty
    assert "kN" in tex


def test_seismic_force_display_missing():
    """Verify seismic forces display empty when data is missing."""
    inp = {}
    tex = ch3_loads(inp)
    assert "Horizontal Seismic Force (longitudinal)" in tex
    assert "Horizontal Seismic Force (transverse)" in tex
    # Neither should have "None kN" or arbitrary numbers
    assert r"\textnormal{Horizontal Seismic Force (longitudinal)} &  \\[6pt]" in tex
    assert r"\textnormal{Horizontal Seismic Force (transverse)} &  \\[6pt]" in tex


def test_chap1_project_info():
    """Verify Chapter 1 generates valid project information."""
    meta = ReportMetadata(
        project_name="Bridge A",
        project_location="Mumbai",
        designer="Engineer A",
        client="State PWD",
        company="Design Org",
        reviewer="Reviewer B",
    )
    tex = ch1_project_info(meta)
    assert r"\chapter{Project Information}" in tex
    assert "Bridge A" in tex
    assert "Mumbai" in tex
    assert "Engineer A" in tex
    assert "Reviewer B" in tex
