import re
import pytest
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_CLASS_SV,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
)


def test_chap3_longtable_headers():
    """Verify all longtables in chap3 have matched endfirsthead and endhead."""
    tex = ch3_loads({})
    n_begin = tex.count(r"\begin{longtable}")
    n_endfirsthead = tex.count(r"\endfirsthead")
    n_endhead = tex.count(r"\endhead")
    n_end = tex.count(r"\end{longtable}")

    assert n_begin >= 8
    assert n_begin == n_end
    assert n_endfirsthead == n_begin
    assert n_endhead == n_begin
    assert tex.count("(continued)") >= n_begin


def test_chap5_longtable_headers():
    """Verify all longtables in chap5 source have matched endfirsthead and endhead."""
    with open("src/osdagbridge/core/reports/chap5.py") as f:
        src = f.read()

    n_begin = src.count(r"\begin{longtable}")
    n_endfirsthead = src.count(r"\endfirsthead")
    n_endhead = src.count(r"\endhead")

    assert n_begin == 30
    assert n_endfirsthead == 30
    assert n_endhead == 30
    assert src.count("(continued)") == 30


def test_chap7_longtable_headers():
    """Verify Table 7.1 has endfirsthead and endhead with continuation header."""
    tex = ch7_quantities({})
    assert tex.count(r"\begin{longtable}") == 1
    assert tex.count(r"\endfirsthead") == 1
    assert tex.count(r"\endhead") == 1
    assert tex.count(r"\end{longtable}") == 1
    assert "Table 7.1  Bill of Materials (continued)" in tex


def test_chap7_table_col_width_within_a4():
    """Verify Table 7.1 total column widths fit within A4 textwidth (15.92 cm)."""
    tex = ch7_quantities({})
    for line in tex.splitlines():
        if line.startswith(r"\begin{longtable}"):
            widths = [float(w) for w in re.findall(r"\{([0-9.]+)cm\}", line)]
            break
    else:
        pytest.fail("begin{longtable} not found in chap7")

    assert len(widths) == 7
    total_col_width = sum(widths)
    assert total_col_width <= 14.5  # 13.9 cm total column widths

    # tabcolsep is set to 2.5pt (14 * 2.5pt = 35pt = 1.23 cm)
    # Total table width approx 13.9 + 1.23 + 0.14 = 15.27 cm < 15.92 cm textwidth
    assert r"\setlength{\tabcolsep}{2.5pt}" in tex


def test_live_load_table_selected_vehicles_only():
    """Verify live load table only contains rows for selected vehicles."""
    inp = {
        KEY_SPAN: "30.0",
        KEY_WC_LD_LANE_TABLE_COUNT: "2",
        KEY_LL_ECCENTRICITY: "1.2",
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_WHEELED: False,
        KEY_LL_IRC_CLASS_SV: False,
    }
    tex = ch3_loads(inp)
    assert r"\textbf{Vehicle Class}" in tex
    assert "Class A" in tex
    assert "Class 70R" not in tex
    assert "Class SV" not in tex
    assert "543.47" in tex or "543.5" in tex
    assert "1.20" in tex


def test_live_load_table_multiple_vehicles():
    """Verify live load table formats multiple selected vehicle classes."""
    inp = {
        KEY_SPAN: "25.0",
        KEY_WC_LD_LANE_TABLE_COUNT: "2",
        KEY_LL_ECCENTRICITY: "1.5",
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_WHEELED: True,
        KEY_LL_IRC_CLASS_SV: True,
    }
    tex = ch3_loads(inp)
    assert "Class A" in tex
    assert "Class 70R (Wheeled)" in tex
    assert "Class SV" in tex
    assert "3776.85" in tex
    assert "1.50" in tex


def test_live_load_table_no_vehicles():
    """Verify live load table displays None Selected when no vehicles chosen."""
    inp = {}
    tex = ch3_loads(inp)
    assert "None Selected" in tex


def test_live_load_footway_load_separated():
    """Verify vehicle live loads and footpath live load are in separate tables."""
    inp = {
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6",
    }
    tex = ch3_loads(inp)
    assert r"\caption{\textbf{Live Loads (LL) --- Vehicle Details}}" in tex
    assert r"\caption{\textbf{Footpath / Pedestrian Live Load}}" in tex
    assert "Footpath Live Load (if applicable)" in tex


def test_live_load_missing_optional_data():
    """Verify missing span or lanes does not crash and outputs safe fallbacks."""
    inp = {
        KEY_LL_IRC_CLASS_A: True,
        # KEY_SPAN missing
        # KEY_WC_LD_LANE_TABLE_COUNT missing
        # KEY_LL_ECCENTRICITY missing
    }
    tex = ch3_loads(inp)
    assert "Class A" in tex
    assert "---" in tex  # for impact, braking, eccentricity


def test_page_layout_preamble_invariants():
    """Verify preamble includes enhanced layout, needspace and footer margin settings."""
    with open("src/osdagbridge/core/reports/report_generator.py") as f:
        src = f.read()

    assert r"\usepackage[a4paper, margin=1in, headheight=15pt, footskip=25pt]{geometry}" in src
    assert r"\BeforeBeginEnvironment{longtable}{\needspace{8\baselineskip}}" in src
    assert r"\setlength{\tabcolsep}{5pt}" in src
    assert r"\renewcommand{\arraystretch}{1.15}" in src
    assert r"\setlength{\LTpre}{4pt}" in src
    assert r"\setlength{\LTpost}{8pt}" in src
    assert r"\setlength{\intextsep}{8pt}" in src
    assert r"\setlength{\textfloatsep}{10pt}" in src


def test_live_load_all_vehicle_types():
    """Verify live load table correctly handles all IRC 6 vehicle types and custom vehicles."""
    inp = {
        KEY_SPAN: "20.0",
        KEY_WC_LD_LANE_TABLE_COUNT: "2",
        KEY_LL_ECCENTRICITY: "1.2",
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_WHEELED: True,
        KEY_LL_IRC_70R_TRACKED: True,
        KEY_LL_IRC_AA_WHEELED: True,
        KEY_LL_IRC_AA_TRACKED: True,
        KEY_LL_IRC_CLASS_SV: True,
        KEY_LL_IRC_70R_BOGIE: True,
        KEY_LL_IRC_CLASS_FATIGUE: True,
        KEY_LL_CUSTOM_VEHICLES: ["Special Crane 50T", {"name": "Modular Transporter"}],
    }
    tex = ch3_loads(inp)
    assert "Class A" in tex
    assert "Class 70R (Wheeled)" in tex
    assert "Class 70R (Tracked)" in tex
    assert "Class AA (Wheeled)" in tex
    assert "Class AA (Tracked)" in tex
    assert "Class SV" in tex
    assert "Class 70R (Bogie)" in tex
    assert "Class Fatigue" in tex
    assert "Special Crane 50T" in tex
    assert "Modular Transporter" in tex
    # Check that loads are listed
    assert "700.00" in tex  # Tracked
    assert "400.00" in tex  # AA Wheeled
    assert "392.40" in tex  # Bogie / Fatigue


def test_longtable_environment_balance():
    """Verify balanced begin/end longtable environments and headers in chap3."""
    tex = ch3_loads({})
    assert tex.count(r"\begin{longtable}") == tex.count(r"\end{longtable}")
    assert tex.count(r"\endfirsthead") == tex.count(r"\endhead")
    assert tex.count(r"\begin{longtable}") == tex.count(r"\endhead")


def test_continuation_captions_format():
    """Verify continuation captions have empty brackets to avoid duplicate LOT entries."""
    tex = ch3_loads({})
    assert r"\caption[]{" in tex
    assert tex.count(r"\caption[]{") == tex.count(r"\begin{longtable}")
