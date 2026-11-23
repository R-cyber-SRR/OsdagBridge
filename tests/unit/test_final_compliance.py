"""Final accuracy and compliance regression tests for OsdagBridge report generation.

Covers:
1. Material quantity reporting (rebar and bracing panel count stay N.A. without fabricated estimates)
2. Longtable continuation headers across Chapter 2 (all 9 tables) and Chapter 4 (all 3 tables)
3. Centralized style consumption by report_generator preamble and chapter generators
4. Vehicle reporting: distinction between selected parameters and analyzed load cases
"""

import pytest
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_LL_IRC_CLASS_A,
)
from osdagbridge.core.boq.boq_generator import calculate_material_quantities
from osdagbridge.core.reports.chap2 import ch2_input_parameters
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap4 import ch4_analysis
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.report_generator import (
    preamble,
    ReportMetadata,
    ReportOptions,
    ReportPayload,
    ReportDataBridge,
)
from osdagbridge.core.reports.styles import (
    GEOMETRY_OPTIONS,
    OSDAG_GREEN_LATEX,
    TABCOLSEP_DEFAULT_PT,
    TABCOLSEP_COMPACT_PT,
    TABLE_STYLE,
)


def test_boq_avoids_fabricated_rebar_and_bracing_estimates():
    """Verify BOQ does not invent 120 kg/m^3 rebar or span/5 panel count."""
    inputs = {
        KEY_SPAN: "30.0",
        KEY_TS_NO_OF_GIRDERS: "4",
        "typical_section.overall_bridge_width": "12.0",
        KEY_TS_DECK_THICKNESS: "250",
        KEY_TS_GIRDER_SPACING: "3.0",
    }
    # outputs with bracing area but WITHOUT cb_spacing
    outputs = {
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": 45.0,
        "crossbracing_forces_dict": {
            "geometry": {"diagonal_length_m": 3.8}  # cb_spacing_m missing
        }
    }
    qty = calculate_material_quantities(inputs, outputs)

    # Geometry-derived concrete deck volume is preserved
    assert qty["concrete_deck_vol_total"] == "90.00"
    assert qty["concrete_deck_wt_total"] == "225.00"

    # Rebar is explicitly N.A. (no 120 kg/m^3 fabrication)
    assert qty["rebar_deck_qty"] == "N.A."
    assert qty["rebar_deck_vol_total"] == "N.A."
    assert qty["rebar_deck_wt_total"] == "N.A."

    # Bracing panel quantities are explicitly N.A. (no span/5 fallback panel count)
    assert qty["bracing_top_qty"] == "N.A."
    assert qty["bracing_bot_qty"] == "N.A."
    assert qty["bracing_diag_qty"] == "N.A."


def test_boq_uses_real_bracing_spacing_when_available():
    """Verify BOQ computes bracing quantities when real cb_spacing_m is provided."""
    inputs = {
        KEY_SPAN: "20.0",
        KEY_TS_NO_OF_GIRDERS: "3",
        KEY_TS_GIRDER_SPACING: "2.5",
    }
    outputs = {
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": 50.0,
        "crossbracing_forces_dict": {
            "geometry": {"diagonal_length_m": 3.2, "cb_spacing_m": 5.0}
        }
    }
    qty = calculate_material_quantities(inputs, outputs)
    assert qty["bracing_top_qty"] == "6"
    assert qty["bracing_diag_qty"] == "12"
    assert qty["bracing_top_vol_total"] != "N.A."


def test_chap2_all_longtables_have_continuation_headers():
    r"""Verify all 9 longtables in Chapter 2 have balanced \endfirsthead and \endhead."""
    meta = ReportMetadata("Proj", "Loc", "Des", "Client", "Comp")
    tex = ch2_input_parameters(meta, {KEY_SPAN: "20.0", KEY_TS_NO_OF_GIRDERS: "3"}, {})

    lt_begin = tex.count(r"\begin{longtable}")
    lt_end = tex.count(r"\end{longtable}")
    endfirsthead_count = tex.count(r"\endfirsthead")
    endhead_count = tex.count(r"\endhead")

    assert lt_begin == 9
    assert lt_end == 9
    assert endfirsthead_count == 9
    assert endhead_count == 9
    assert r"\caption[]{\textit{Typical Section Details (continued)}}" in tex
    assert r"\caption[]{\textit{Components Details (continued)}}" in tex
    assert r"\caption[]{\textit{Girder General Information (continued)}}" in tex
    assert r"\caption[]{\textit{Girder Section Dimensions (continued)}}" in tex
    assert r"\caption[]{\textit{Girder Restraint and Stiffener Details (continued)}}" in tex
    assert r"\caption[]{\textit{Member Properties: Cross Bracing Details (continued)}}" in tex
    assert r"\caption[]{\textit{Member Properties: End Diaphragm Details (continued)}}" in tex
    assert r"\caption[]{\textit{Shear Connector Details (continued)}}" in tex
    assert r"\caption[]{\textit{Partial Safety Factors (continued)}}" in tex


def test_chap4_all_longtables_have_continuation_headers():
    r"""Verify all 3 longtables in Chapter 4 have balanced \endfirsthead and \endhead."""
    meta = ReportMetadata("Proj", "Loc", "Des", "Client", "Comp")
    opts = ReportOptions([], False, False, False)
    payload = ReportPayload(meta, opts, {KEY_SPAN: "20.0"}, {}, [], None)
    bridge = ReportDataBridge({}, {KEY_SPAN: "20.0"}, payload)

    tex = ch4_analysis({}, {}, bridge, 20.0)

    lt_begin = tex.count(r"\begin{longtable}")
    lt_end = tex.count(r"\end{longtable}")
    endfirsthead_count = tex.count(r"\endfirsthead")
    endhead_count = tex.count(r"\endhead")

    assert lt_begin == 3
    assert lt_end == 3
    assert endfirsthead_count == 3
    assert endhead_count == 3
    assert r"\caption[]{\textit{Reactions at Supports (continued)}}" in tex
    assert r"\caption[]{\textit{Deflection Summary (Live Load \& Total Load) (continued)}}" in tex


def test_preamble_and_chap7_consume_styles_constants():
    """Verify report_generator and chap7 consume centralized styling configuration."""
    pre = preamble("Proj", "J101", "2026-11-23", "Rev 0")
    assert GEOMETRY_OPTIONS in pre
    assert f"\\definecolor{{osdagGreen}}{{HTML}}{{{OSDAG_GREEN_LATEX}}}" in pre
    assert f"\\setlength{{\\tabcolsep}}{{{TABLE_STYLE['tabcolsep']}pt}}" in pre

    ch7_tex = ch7_quantities({}, None)
    assert f"\\setlength{{\\tabcolsep}}{{{TABCOLSEP_COMPACT_PT}pt}}" in ch7_tex
    assert r"Concrete deck volume is geometry-derived" in ch7_tex


def test_vehicle_reporting_reflects_actual_analysis_state():
    """Verify vehicle reporting distinguishes selected vehicles from analyzed load cases."""
    inputs = {KEY_LL_IRC_CLASS_A: True, KEY_SPAN: "20.0"}

    # 1. Without analyzed load cases in output_dict
    tex1 = ch3_loads(inputs, {})
    assert "Parameters represent selected vehicle criteria" in tex1

    # 2. When moving load analysis was not executed
    tex2 = ch3_loads(inputs, {"analysis_summary": {"load_cases": {"SW": {}, "DD": {}}}})
    assert "moving load analysis was not executed or produced no active vehicle load cases" in tex2

    # 3. When vehicle load cases were actually analyzed
    tex3 = ch3_loads(inputs, {"analysis_summary": {"load_cases": {"SW": {}, "1.0 LL": {}}}})
    assert "Load cases analyzed: 1.0 LL" in tex3
