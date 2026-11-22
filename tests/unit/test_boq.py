import pytest
from osdagbridge.core.boq.boq_generator import calculate_material_quantities
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
)


def test_boq_empty_inputs():
    """Verify calculate_material_quantities handles empty/invalid inputs gracefully."""
    quantities = calculate_material_quantities({}, {})
    assert quantities["concrete_deck_qty"] == "N.A."
    assert quantities["steel_girders_qty"] == "N.A."
    assert quantities["shear_studs_qty"] == "N.A."
    # Formulas should not contain bare $ math mode delimiters
    assert "$" not in quantities["concrete_deck_vol_formula"]
    assert "$" not in quantities["steel_girders_vol_formula"]


def test_boq_concrete_and_rebar_calculation():
    """Verify concrete volume and rebar calculations with valid dimensions."""
    inputs = {
        KEY_SPAN: "25.0",
        KEY_TS_NO_OF_GIRDERS: "4",
        "typical_section.overall_bridge_width": "12.0",
        KEY_TS_DECK_THICKNESS: "250",  # mm -> 0.25 m
    }
    outputs = {}
    quantities = calculate_material_quantities(inputs, outputs)

    # Concrete Volume = 25.0 * 12.0 * 0.25 = 75.0 m^3
    assert quantities["concrete_deck_vol_total"] == "75.00"
    # Concrete weight = 75.0 * 2.5 = 187.50 MT
    assert quantities["concrete_deck_wt_total"] == "187.50"
    # Rebar weight = 75.0 * 120 kg = 9000 kg = 9.00 MT
    assert quantities["rebar_deck_wt_total"] == "9.00"

    # Math mode safety: should use \( ... \) instead of $ ... $
    formula = quantities["concrete_deck_vol_formula"]
    assert "$" not in formula
    assert formula.startswith(r"\(") and formula.endswith(r"\)")


def test_boq_steel_girder_calculation():
    """Verify steel girder volume and weight calculation."""
    inputs = {
        KEY_SPAN: "20.0",
        KEY_TS_NO_OF_GIRDERS: "2",
        "member_properties.girder_details.section_properties.area": "0.05",  # m^2
        "member_properties.girder_details.section_properties.mass": "392.5",  # kg/m
    }
    outputs = {}
    quantities = calculate_material_quantities(inputs, outputs)

    assert quantities["steel_girders_qty"] == "2"
    # Girder vol single = 0.05 * 20.0 = 1.0 m^3; total = 2.0 m^3
    assert quantities["steel_girders_vol_total"] == "2.00"
    # Total mass = 2 * 392.5 * 20.0 = 15700 kg = 15.70 MT
    assert quantities["steel_girders_wt_total"] == "15.70"

    formula = quantities["steel_girders_vol_formula"]
    assert "$" not in formula
    assert formula.startswith(r"\(") and formula.endswith(r"\)")


def test_boq_shear_studs_calculation():
    """Verify shear stud connector quantity and weight calculation."""
    inputs = {
        KEY_SPAN: "30.0",
        KEY_TS_NO_OF_GIRDERS: "3",
    }
    outputs = {
        "steeldesign.details.shear.longitudinal_spacing": "150.0",  # mm
        "steeldesign.details.shear.studs_per_section": "2",
        "steeldesign.details.shear.diameter": "25.0",  # mm
        "steeldesign.details.shear.height": "100.0",  # mm
    }
    quantities = calculate_material_quantities(inputs, outputs)

    # n_sections = int(30 * 1000 / 150) + 1 = 201 sections
    # total studs = 3 girders * 2 * 201 = 1206 studs
    assert quantities["shear_studs_qty"] == "1206"
    assert quantities["shear_studs_vol_total"] != "N.A."
    assert quantities["shear_studs_wt_total"] != "N.A."

    formula = quantities["shear_studs_vol_formula"]
    assert "$" not in formula
    assert formula.startswith(r"\(") and formula.endswith(r"\)")


def test_boq_bracing_calculation():
    """Verify cross-bracing calculation with valid geometry and section properties."""
    inputs = {
        KEY_SPAN: "20.0",
        KEY_TS_NO_OF_GIRDERS: "3",
        KEY_TS_GIRDER_SPACING: "2.5",
    }
    outputs = {
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": "15.0",  # cm^2 -> 0.0015 m^2
        "crossbracing_forces_dict": {
            "geometry": {
                "diagonal_length_m": 2.8,
                "cb_spacing_m": 5.0,
            }
        }
    }
    quantities = calculate_material_quantities(inputs, outputs)

    assert quantities["bracing_top_qty"] != "N.A."
    assert quantities["bracing_bot_qty"] != "N.A."
    assert quantities["bracing_diag_qty"] != "N.A."

    for key in ("bracing_top_vol_formula", "bracing_bot_vol_formula", "bracing_diag_vol_formula"):
        formula = quantities[key]
        assert "$" not in formula
        assert formula.startswith(r"\(") and formula.endswith(r"\)")


def test_boq_crash_barrier_calculation():
    """Verify crash barrier volume and weight calculation."""
    inputs = {
        KEY_SPAN: "24.0",
        KEY_TS_NO_OF_GIRDERS: "2",
        "typical_section.crash_barrier.area": "250000.0",  # mm^2 = 0.25 m^2
    }
    outputs = {}
    quantities = calculate_material_quantities(inputs, outputs)

    # cb_vol = 0.25 * 24.0 = 6.0 m^3; total = 12.0 m^3
    assert quantities["crash_barrier_qty"] == "2"
    assert quantities["crash_barrier_vol_total"] == "12.00"
    # Weight total = 12.0 * 2.5 = 30.00 MT
    assert quantities["crash_barrier_wt_total"] == "30.00"

    formula = quantities["crash_barrier_vol_formula"]
    assert "$" not in formula
    assert formula.startswith(r"\(") and formula.endswith(r"\)")
