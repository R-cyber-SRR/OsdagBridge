"""Automated regression and unit tests for Phase 3 visualizations and styling.

Tests:
- Utilization ratio extraction functions (Girders, Deck, Cross Bracing, End Diaphragms)
- Passing vs failing check status detection
- Missing / incomplete data handling (no crashes, graceful empty returns)
- Material quantity extraction from BOQ data
- Chart generation functions and PNG image validity
- Temporary image asset handling and directory cleanup
- Report Chapter 5 and Chapter 7 figure embedding integration
"""

import os
import tempfile
import pytest

from osdagbridge.core.reports.styles import (
    PAGE_SIZE,
    MARGIN_INCHES,
    OSDAG_GREEN_HEX,
    PASS_GREEN_HEX,
    FAIL_RED_HEX,
    COLORS,
    TABLE_STYLE,
    FONT_SIZES,
)
from osdagbridge.core.reports.visualizations import (
    extract_girder_utilization_ratios,
    extract_deck_utilization_ratios,
    extract_cross_bracing_utilization_ratios,
    extract_end_diaphragm_utilization_ratios,
    extract_material_quantities,
    create_girder_ur_chart,
    create_deck_ur_chart,
    create_cross_bracing_ur_chart,
    create_end_diaphragm_ur_chart,
    create_boq_steel_tonnage_chart,
    create_boq_materials_chart,
    generate_all_report_visualizations,
)
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.report_generator import ReportDataBridge, ReportPayload, ReportMetadata, ReportOptions
from osdagbridge.core.utils.common import (
    KEY_DD_M_ULS_SAG,
    KEY_DD_MU_BOT,
    KEY_DD_M_ULS_HOG,
    KEY_DD_MU_TOP,
    KEY_DD_PUNCH_VED,
    KEY_DD_VRD_C_MPA,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_WK_LIMIT,
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


# =============================================================================
# 1. Centralized Styles Tests
# =============================================================================

def test_styles_configuration():
    """Verify centralized style constants and color definitions."""
    assert MARGIN_INCHES == 1.0
    assert PAGE_SIZE == "a4paper"
    assert OSDAG_GREEN_HEX == "#91B014"
    assert PASS_GREEN_HEX == "#2E7D32"
    assert FAIL_RED_HEX == "#D32F2F"
    assert "brand" in COLORS
    assert "threshold" in COLORS
    assert TABLE_STYLE["tabcolsep"] == 5.0
    assert TABLE_STYLE["arraystretch"] == 1.15
    assert FONT_SIZES["title"] > FONT_SIZES["axis_label"]


# =============================================================================
# 2. Utilization Ratio Extraction Tests
# =============================================================================

def test_extract_girder_ur_passing_and_failing():
    """Verify girder UR extraction correctly captures checks and pass/fail states."""
    output_dict = {
        "design_results": {
            "per_girder": {
                "G1": {
                    "checks": [
                        {"name": "Moment Capacity Check", "dcr": 0.82, "status": "PASS"},
                        {"name": "Shear Capacity Check", "dcr": 0.45, "status": "PASS"},
                        {"name": "Deflection Check", "dcr": 1.15, "status": "FAIL"},
                    ]
                },
                "G2": {
                    "checks": [
                        {"name": "Moment Capacity Check", "dcr": 0.78, "status": "PASS"},
                        {"name": "Shear Capacity Check", "dcr": 0.42, "status": "PASS"},
                    ]
                },
                "EB1": {  # Edge beam pseudo girder should be skipped
                    "checks": [{"name": "Moment Capacity Check", "dcr": 0.50, "status": "PASS"}]
                }
            }
        }
    }
    items = extract_girder_utilization_ratios(output_dict)
    assert len(items) == 5
    assert all("EB1" not in item["name"] for item in items)

    # Check status assignment
    failing = [it for it in items if it["status"] == "FAIL"]
    assert len(failing) == 1
    assert failing[0]["ur"] == 1.15
    assert "Deflection" in failing[0]["check"]

    passing = [it for it in items if it["status"] == "PASS"]
    assert len(passing) == 4


def test_extract_girder_ur_fallback_max_dcr():
    """Verify girder UR extraction falls back to max_dcr when checks list is absent."""
    output_dict = {
        "design_results": {
            "per_girder": {
                "G1": {"max_dcr": 0.88},
                "G2": {"max_dcr": 1.05},
            }
        }
    }
    items = extract_girder_utilization_ratios(output_dict)
    assert len(items) == 2
    assert items[0]["ur"] == 0.88 and items[0]["status"] == "PASS"
    assert items[1]["ur"] == 1.05 and items[1]["status"] == "FAIL"


def test_extract_girder_ur_missing_data():
    """Verify girder UR extraction returns empty list on missing data."""
    assert extract_girder_utilization_ratios({}) == []
    assert extract_girder_utilization_ratios(None) == []
    assert extract_girder_utilization_ratios({"design_results": {}}) == []


def test_extract_deck_ur_checks():
    """Verify deck UR extraction calculates demand/capacity ratios accurately."""
    output_dict = {
        "deck_report_values": {
            KEY_DD_M_ULS_SAG: 120.0,
            KEY_DD_MU_BOT: 150.0,      # 120 / 150 = 0.80 -> PASS
            KEY_DD_M_ULS_HOG: 160.0,
            KEY_DD_MU_TOP: 140.0,      # 160 / 140 = 1.143 -> FAIL
            KEY_DD_PUNCH_VED: 0.65,
            KEY_DD_VRD_C_MPA: 0.80,    # 0.65 / 0.80 = 0.8125 -> PASS
            KEY_DD_SHEAR_VED: 110.0,
            KEY_DD_SHEAR_VRDC: 130.0,  # 110 / 130 = 0.846 -> PASS
            "governing_wk": 0.18,
            KEY_DD_WK_LIMIT: 0.20,     # 0.18 / 0.20 = 0.90 -> PASS
        }
    }
    items = extract_deck_utilization_ratios(output_dict)
    assert len(items) == 5

    name_map = {it["name"]: it for it in items}
    assert name_map["Midspan Flexure"]["ur"] == 0.80
    assert name_map["Midspan Flexure"]["status"] == "PASS"
    assert name_map["Support Flexure"]["ur"] == 1.143
    assert name_map["Support Flexure"]["status"] == "FAIL"
    assert name_map["Crack Width"]["ur"] == 0.90


def test_extract_deck_ur_missing_data():
    """Verify deck UR extraction handles empty inputs gracefully."""
    assert extract_deck_utilization_ratios({}) == []
    assert extract_deck_utilization_ratios(None) == []


def test_extract_cross_bracing_ur_from_production_result_keys():
    """Extract actual Osdag engine keys, including the legacy UR key."""
    output_dict = {
        "crossbracing_design_results": {
            "G1-G2": {
                "diagonal": {
                    "compression": {"Member.efficiency": "0.72"},
                    "tension": {"Optimum.UR": "0.55"},
                },
                "chord": {
                    "compression": {"Member.efficiency": 0.64},
                }
            }
        }
    }
    items = extract_cross_bracing_utilization_ratios(output_dict)
    assert len(items) == 3
    assert all(it["status"] == "PASS" for it in items)
    assert any(it["ur"] == 0.72 for it in items)


def test_extract_end_diaphragm_ur_from_production_result_keys():
    """Extract actual Osdag engine keys for end-diaphragm members."""
    output_dict = {
        "end_diaphragm_design_results": {
            "Support-1": {
                "bracing": {
                    "compression": {"Member.efficiency": 0.85},
                    "tension": {"Optimum.UR": 1.08},
                }
            }
        }
    }
    items = extract_end_diaphragm_utilization_ratios(output_dict)
    assert len(items) == 2
    assert any(it["ur"] == 0.85 and it["status"] == "PASS" for it in items)
    assert any(it["ur"] == 1.08 and it["status"] == "FAIL" for it in items)


@pytest.mark.parametrize(
    ("extractor", "result_key"),
    [
        (extract_cross_bracing_utilization_ratios, "crossbracing_design_results"),
        (extract_end_diaphragm_utilization_ratios, "end_diaphragm_design_results"),
    ],
)
def test_transverse_member_ur_ignores_missing_or_malformed_production_values(extractor, result_key):
    """Missing, malformed, and negative values must not become invented URs."""
    output_dict = {
        result_key: {
            "G1-G2": {
                "diagonal": {
                    "compression": {"Member.efficiency": "not-a-number"},
                    "tension": {"Optimum.UR": -0.2},
                    "other": {},
                },
            },
        },
    }
    assert extractor(output_dict) == []


# =============================================================================
# 3. Material Quantity Extraction Tests
# =============================================================================

def test_extract_material_quantities_valid():
    """Verify material quantities extraction with valid BOQ inputs."""
    boq = {
        "steel_girders_wt_total": "39.25",
        "bracing_top_wt_total": "1.20",
        "bracing_bot_wt_total": "1.20",
        "bracing_diag_wt_total": "2.10",
        "shear_studs_wt_total": "0.45",
        "concrete_deck_vol_total": "75.00",
        "rebar_deck_wt_total": "9.00",
    }
    data = extract_material_quantities(boq)
    assert data["steel_breakdown"]["Plate Girders"] == 39.25
    assert data["steel_breakdown"]["Cross Bracing"] == 4.50  # 1.2 + 1.2 + 2.1
    assert data["steel_breakdown"]["Shear Studs"] == 0.45
    assert data["concrete_volume_m3"] == 75.00
    assert data["rebar_weight_mt"] == 9.00


def test_extract_material_quantities_empty():
    """Verify material quantities extraction handles empty inputs safely."""
    data = extract_material_quantities({})
    assert data["steel_breakdown"] == {}
    assert data["concrete_volume_m3"] is None
    assert data["rebar_weight_mt"] is None


# =============================================================================
# 4. Chart Generation & Image Validity Tests
# =============================================================================

def test_chart_generators_png_validity():
    """Verify all 6 chart generators return valid PNG byte streams."""
    sample_output = {
        "design_results": {
            "per_girder": {
                "G1": {"checks": [{"name": "Moment", "dcr": 0.85, "status": "PASS"}]}
            }
        },
        "deck_report_values": {
            KEY_DD_M_ULS_SAG: 100.0,
            KEY_DD_MU_BOT: 120.0,
        },
        "crossbracing_design_results": {
            "P1": {"diag": {"compression": {"efficiency": 0.65}}}
        },
        "end_diaphragm_design_results": {
            "ED1": {"beam": {"compression": {"efficiency": 0.75}}}
        }
    }
    sample_boq = {
        "steel_girders_wt_total": "35.50",
        "bracing_top_wt_total": "2.50",
        "concrete_deck_vol_total": "60.00",
        "rebar_deck_wt_total": "7.50",
    }

    # Verify each generator returns PNG bytes
    for gen_func, args in [
        (create_girder_ur_chart, (sample_output,)),
        (create_deck_ur_chart, (sample_output,)),
        (create_cross_bracing_ur_chart, (sample_output,)),
        (create_end_diaphragm_ur_chart, (sample_output,)),
        (create_boq_steel_tonnage_chart, (sample_boq,)),
        (create_boq_materials_chart, (sample_boq,)),
    ]:
        png_data = gen_func(*args)
        assert isinstance(png_data, bytes)
        assert png_data.startswith(PNG_MAGIC), f"{gen_func.__name__} did not return valid PNG"


def test_chart_generators_empty_data_fallback():
    """Verify chart generators produce valid banner PNGs when data is missing."""
    for gen_func in [
        create_girder_ur_chart,
        create_deck_ur_chart,
        create_cross_bracing_ur_chart,
        create_end_diaphragm_ur_chart,
        create_boq_steel_tonnage_chart,
        create_boq_materials_chart,
    ]:
        png_data = gen_func({})
        assert isinstance(png_data, bytes)
        assert png_data.startswith(PNG_MAGIC)


def test_generate_all_visualizations_saves_to_dir():
    """Verify generate_all_report_visualizations saves non-empty PNG files to target dir."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        charts = generate_all_report_visualizations(
            output_dict={},
            input_dict={},
            boq_quantities={},
            output_dir=tmp_dir,
        )
        assert len(charts) == 6
        for name, path in charts.items():
            assert os.path.exists(path), f"File {path} not created"
            assert os.path.getsize(path) > 1000, f"File {path} is suspiciously small"


def test_generate_all_visualizations_continues_after_one_chart_failure(monkeypatch):
    """One rendering error must not suppress unrelated report charts."""
    import osdagbridge.core.reports.visualizations as visualizations

    def _raise(*args, **kwargs):
        raise RuntimeError("intentional chart failure")

    monkeypatch.setattr(visualizations, "create_girder_ur_chart", _raise)
    charts = visualizations.generate_all_report_visualizations({}, {}, {})

    assert "chart_ur_girders" not in charts
    assert set(charts) == {
        "chart_ur_deck",
        "chart_ur_cross_bracing",
        "chart_ur_end_diaphragm",
        "chart_boq_steel_tonnage",
        "chart_boq_materials",
    }
    assert all(image.startswith(PNG_MAGIC) for image in charts.values())


# =============================================================================
# 5. Chapter Integration Tests
# =============================================================================

def test_chapter5_figure_integration_with_paths():
    """Verify Chapter 5 embeds figure environments when fig_paths are provided."""
    fig_paths = {
        "chart_ur_girders": "images/chart_ur_girders.png",
        "chart_ur_deck": "images/chart_ur_deck.png",
        "chart_ur_cross_bracing": "images/chart_ur_cross_bracing.png",
        "chart_ur_end_diaphragm": "images/chart_ur_end_diaphragm.png",
    }
    _meta = ReportMetadata("Test Bridge", "City", "Engineer", "Client", "Company")
    _opts = ReportOptions(sections=[], include_figures=False, include_toc=False, include_pdf=False)
    bridge = ReportDataBridge({}, {}, ReportPayload(
        metadata=_meta,
        options=_opts,
        inputs={},
        analysis_summary={},
        design_checks=[],
        figures=None,
    ))

    tex = ch5_design_checks({}, bridge, fig_paths=fig_paths)
    assert r"\subsection{Component Utilization Ratio Visualizations}" in tex
    assert r"\includegraphics[width=0.88\textwidth]{images/chart_ur_girders.png}" in tex
    assert r"\label{fig:ur-girders}" in tex
    assert r"\includegraphics[width=0.88\textwidth]{images/chart_ur_deck.png}" in tex
    assert r"\label{fig:ur-deck}" in tex
    assert r"\includegraphics[width=0.88\textwidth]{images/chart_ur_cross_bracing.png}" in tex
    assert r"\label{fig:ur-cross-bracing}" in tex
    assert r"\includegraphics[width=0.88\textwidth]{images/chart_ur_end_diaphragm.png}" in tex
    assert r"\label{fig:ur-end-diaphragm}" in tex


def test_chapter5_figure_integration_without_paths():
    """Verify Chapter 5 omits figures when fig_paths is None or empty."""
    _meta = ReportMetadata("Test Bridge", "City", "Engineer", "Client", "Company")
    _opts = ReportOptions(sections=[], include_figures=False, include_toc=False, include_pdf=False)
    bridge = ReportDataBridge({}, {}, ReportPayload(
        metadata=_meta,
        options=_opts,
        inputs={},
        analysis_summary={},
        design_checks=[],
        figures=None,
    ))
    tex = ch5_design_checks({}, bridge, fig_paths=None)
    assert r"\subsection{Component Utilization Ratio Visualizations}" not in tex
    assert "chart_ur_girders.png" not in tex


def test_chapter7_figure_integration_with_paths():
    """Verify Chapter 7 embeds material quantity figures when fig_paths are provided."""
    fig_paths = {
        "chart_boq_steel_tonnage": "images/chart_boq_steel_tonnage.png",
        "chart_boq_materials": "images/chart_boq_materials.png",
    }
    tex = ch7_quantities({}, fig_paths=fig_paths)
    assert r"\section{Material Quantity Visualizations}" in tex
    assert r"\includegraphics[width=0.88\textwidth]{images/chart_boq_steel_tonnage.png}" in tex
    assert r"\label{fig:boq-steel}" in tex
    assert r"\includegraphics[width=0.88\textwidth]{images/chart_boq_materials.png}" in tex
    assert r"\label{fig:boq-materials}" in tex
    # Group balance should still hold
    assert tex.count(r"\begingroup") == tex.count(r"\endgroup") == 1


def test_chapter7_figure_integration_without_paths():
    """Verify Chapter 7 omits material figures when fig_paths is None."""
    tex = ch7_quantities({}, fig_paths=None)
    assert r"\section{Material Quantity Visualizations}" not in tex
    assert "chart_boq_steel_tonnage.png" not in tex
    assert tex.count(r"\begingroup") == tex.count(r"\endgroup") == 1
