"""Dynamic engineering visualizations for OsdagBridge reports.

Generates publication-quality charts for:
1. Utilization ratios (Plate Girders, Concrete Deck Slab, Cross Bracing, End Diaphragms)
2. Material quantities (Structural Steel Tonnage Breakdown, Concrete Volume & Rebar Weight)

All charts adhere to centralized styling from styles.py and handle missing
or incomplete data gracefully without inventing engineering values.
"""

import io
import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

from osdagbridge.core.reports.styles import (
    setup_matplotlib_style,
    apply_chart_styling,
    COLORS,
    FONT_SIZES,
    CHART_DPI,
    CHART_FIGSIZE_STANDARD,
    CHART_FIGSIZE_TALL,
    PASS_GREEN_HEX,
    FAIL_RED_HEX,
    STEEL_BLUE_HEX,
    CONCRETE_GRAY_HEX,
    REBAR_ORANGE_HEX,
    TEXT_DARK_HEX,
    THRESHOLD_RED_HEX,
)
from osdagbridge.core.utils.common import (
    KEY_DD_M_ULS_SAG,
    KEY_DD_MU_BOT,
    KEY_DD_M_ULS_HOG,
    KEY_DD_MU_TOP,
    KEY_DD_M_ULS_OH,
    KEY_DD_MU_OH,
    KEY_DD_PUNCH_VED,
    KEY_DD_VRD_C_MPA,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_WK_LIMIT,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Helper Utilities
# =============================================================================

def _safe_float(val: Any) -> Optional[float]:
    """Safely convert value to float, returning None on failure."""
    if val in (None, "", "N/A", "N.A.", "---", "--"):
        return None
    try:
        f = float(val)
        return f if f >= 0 else None
    except (ValueError, TypeError):
        return None


def _extract_osdag_efficiency(raw: Any) -> Optional[float]:
    """Return a member UR only when it is present in a result payload.

    Production transverse-member results retain the keys emitted by the Osdag
    design engine (``Member.efficiency`` or legacy ``Optimum.UR``).  The
    report's existing ``_extract_osdag_summary`` helper owns that key mapping.
    ``efficiency`` is retained solely for already-normalized/legacy report
    payloads.  No demand/capacity calculation or substitute value is made here.
    """
    if not isinstance(raw, dict):
        return None

    # Some callers already provide the normalized summary payload.
    efficiency = _safe_float(raw.get("efficiency"))
    if efficiency is not None:
        return efficiency

    # Match _extract_osdag_summary()'s production-key mapping directly.  This
    # keeps report generation independent of the optional analysis module's
    # import graph while accepting no keys beyond that established schema.
    for key in ("Member.efficiency", "Optimum.UR"):
        efficiency = _safe_float(raw.get(key))
        if efficiency is not None:
            return efficiency
    return None


def _fig_to_bytes(fig: Any) -> bytes:
    """Save matplotlib Figure to PNG bytes and close figure to free memory."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=CHART_DPI, bbox_inches="tight")
    buf.seek(0)
    data = buf.getvalue()
    buf.close()
    import matplotlib.pyplot as plt
    plt.close(fig)
    return data


def _save_or_bytes(fig: Any, output_path: Optional[str] = None) -> Union[bytes, str]:
    """Save figure to path if provided, else return PNG bytes."""
    data = _fig_to_bytes(fig)
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as fh:
            fh.write(data)
        return output_path
    return data


def _create_empty_banner_chart(title: str, message: str, figsize=CHART_FIGSIZE_STANDARD) -> Any:
    """Render a clean placeholder chart when data is missing or not applicable."""
    setup_matplotlib_style()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize)
    apply_chart_styling(ax, title=title, y_threshold=None)
    ax.text(
        0.5, 0.5, message,
        ha="center", va="center", transform=ax.transAxes,
        fontsize=FONT_SIZES["axis_label"], color="#757575", style="italic",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#F5F5F5", edgecolor="#E0E0E0")
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    return fig


# =============================================================================
# Data Extraction Functions (Real output_dict data only)
# =============================================================================

def extract_girder_utilization_ratios(output_dict: dict, input_dict: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Extract utilization ratios for steel plate girders.
    
    Reads from output_dict['design_results']['per_girder'] or individual girder checks.
    Returns list of dicts with keys: 'name', 'ur', 'status', 'girder'.
    """
    if not isinstance(output_dict, dict):
        return []

    per_girder = (output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    items = []

    # Map check names to short readable labels
    _short_names = {
        "moment capacity": "Moment",
        "shear capacity": "Shear",
        "lateral torsional": "LTB",
        "deflection": "Deflection",
        "maximum stress": "Stress",
        "fatigue": "Fatigue",
        "interaction": "M-V / M-N",
    }

    for g_id, g_data in per_girder.items():
        if str(g_id).startswith("EB"):  # Skip edge-beam pseudo girders
            continue
        checks = g_data.get("checks") or []
        for chk in checks:
            dcr = _safe_float(chk.get("dcr"))
            if dcr is None:
                continue
            raw_name = str(chk.get("name", "")).strip()
            short_name = raw_name
            for k, v in _short_names.items():
                if k in raw_name.lower():
                    short_name = v
                    break
            status = "PASS" if ("PASS" in str(chk.get("status", "")).upper() or dcr <= 1.0) else "FAIL"
            items.append({
                "girder": str(g_id),
                "check": short_name,
                "name": f"{g_id} - {short_name}",
                "ur": dcr,
                "status": status,
            })

    # Fallback to controlling DCR per girder if individual checks list is not found
    if not items:
        for g_id, g_data in per_girder.items():
            if str(g_id).startswith("EB"):
                continue
            max_dcr = _safe_float(g_data.get("max_dcr"))
            if max_dcr is not None:
                items.append({
                    "girder": str(g_id),
                    "check": "Controlling",
                    "name": f"{g_id} (Governing)",
                    "ur": max_dcr,
                    "status": "PASS" if max_dcr <= 1.0 else "FAIL",
                })

    return items


def extract_deck_utilization_ratios(output_dict: dict, input_dict: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Extract utilization ratios for reinforced concrete deck slab design checks.
    
    Reads from output_dict['deck_report_values'] or output_dict['deck_design_results']
    or calculates demand/capacity ratios from pre-computed limit states.
    """
    if not isinstance(output_dict, dict):
        return []

    drv = output_dict.get("deck_report_values") or output_dict
    ddr = output_dict.get("deck_design_results") or {}
    items = []

    def _chk(label: str, dem_key: str, cap_key: str, fallback_ur_key: Optional[str] = None):
        ur = None
        dem = _safe_float(drv.get(dem_key))
        cap = _safe_float(drv.get(cap_key))
        if dem is not None and cap is not None and cap > 0:
            ur = dem / cap
        elif fallback_ur_key:
            ur = _safe_float(ddr.get(fallback_ur_key)) or _safe_float(drv.get(fallback_ur_key))

        if ur is not None:
            items.append({
                "name": label,
                "ur": round(ur, 3),
                "status": "PASS" if ur <= 1.0 else "FAIL",
            })

    # Standard IRC 112 / IRC 22 deck checks
    _chk("Midspan Flexure", KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "ur_flexure_sagging")
    _chk("Support Flexure", KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "ur_flexure_hogging")

    # Overhang flexure if cantilever exists
    if drv.get(KEY_DD_MU_OH) and _safe_float(drv.get(KEY_DD_MU_OH)) > 0:
        _chk("Cantilever Overhang", KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "ur_overhang")

    _chk("Punching Shear", KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "ur_punching")
    _chk("One-Way Shear", KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "ur_shear")

    # Crack width check (governing crack width / limit)
    wk = _safe_float(drv.get("deck_design.crack.governing_wk") or drv.get("governing_wk"))
    wk_lim = _safe_float(drv.get(KEY_DD_WK_LIMIT))
    if wk is not None and wk_lim is not None and wk_lim > 0:
        ur_crack = wk / wk_lim
        items.append({
            "name": "Crack Width",
            "ur": round(ur_crack, 3),
            "status": "PASS" if ur_crack <= 1.0 else "FAIL",
        })

    return items


def extract_cross_bracing_utilization_ratios(output_dict: dict, input_dict: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Extract utilization ratios for cross bracing members (compression, tension, slenderness).
    
    Reads from output_dict['crossbracing_design_results'] or output_dict['cross_bracing'].
    """
    if not isinstance(output_dict, dict):
        return []

    cb_results = (
        output_dict.get("crossbracing_design_results")
        or (output_dict.get("cross_bracing", {}) or {}).get("pair_designs")
        or {}
    )
    items = []

    if isinstance(cb_results, dict):
        for pair_name, members in cb_results.items():
            if not isinstance(members, dict):
                continue
            for mem_name, force_types in members.items():
                if not isinstance(force_types, dict):
                    continue
                for ft, raw in force_types.items():
                    if not isinstance(raw, dict):
                        continue
                    eff = _extract_osdag_efficiency(raw)
                    if eff is not None:
                        label = f"{pair_name} {mem_name[:4]} ({ft[:4]})"
                        items.append({
                            "name": label,
                            "ur": round(eff, 3),
                            "status": "PASS" if eff <= 1.0 else "FAIL",
                        })

    # Fallback to bridge-level cross bracing efficiency in output_dict
    if not items:
        comp_ur = _safe_float(output_dict.get("cb_compression_ur"))
        if comp_ur is not None:
            items.append({"name": "Axial Compression", "ur": comp_ur, "status": "PASS" if comp_ur <= 1.0 else "FAIL"})
        tens_ur = _safe_float(output_dict.get("cb_tension_ur"))
        if tens_ur is not None:
            items.append({"name": "Axial Tension", "ur": tens_ur, "status": "PASS" if tens_ur <= 1.0 else "FAIL"})
        slen_ur = _safe_float(output_dict.get("cb_slenderness_ur"))
        if slen_ur is not None:
            items.append({"name": "Slenderness (KL/r)", "ur": slen_ur, "status": "PASS" if slen_ur <= 1.0 else "FAIL"})

    return items


def extract_end_diaphragm_utilization_ratios(output_dict: dict, input_dict: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Extract utilization ratios for end diaphragm members.
    
    Reads from output_dict['end_diaphragm_design_results'] or output_dict['end_diaphragm'].
    """
    if not isinstance(output_dict, dict):
        return []

    ed_results = (
        output_dict.get("end_diaphragm_design_results")
        or (output_dict.get("end_diaphragm", {}) or {}).get("pair_designs")
        or {}
    )
    items = []

    if isinstance(ed_results, dict):
        for pair_name, members in ed_results.items():
            if not isinstance(members, dict):
                continue
            for mem_name, force_types in members.items():
                if not isinstance(force_types, dict):
                    continue
                for ft, raw in force_types.items():
                    if not isinstance(raw, dict):
                        continue
                    eff = _extract_osdag_efficiency(raw)
                    if eff is not None:
                        label = f"ED {pair_name} ({ft[:4]})"
                        items.append({
                            "name": label,
                            "ur": round(eff, 3),
                            "status": "PASS" if eff <= 1.0 else "FAIL",
                        })

    # If end diaphragm mirrors cross-bracing configuration
    if not items:
        ed_comp = _safe_float(output_dict.get("ed_compression_ur"))
        if ed_comp is not None:
            items.append({"name": "ED Compression", "ur": ed_comp, "status": "PASS" if ed_comp <= 1.0 else "FAIL"})
        ed_tens = _safe_float(output_dict.get("ed_tension_ur"))
        if ed_tens is not None:
            items.append({"name": "ED Tension", "ur": ed_tens, "status": "PASS" if ed_tens <= 1.0 else "FAIL"})

    return items


def extract_material_quantities(boq_quantities: dict) -> Dict[str, Any]:
    """Safely extract steel weight breakdown and material quantities from BOQ output.
    
    Returns structured dict with steel breakdown (MT) and concrete/rebar quantities.
    """
    if not isinstance(boq_quantities, dict):
        return {"steel_breakdown": {}, "materials": {}}

    # Structural steel tonnage by component (MT)
    girders_wt = _safe_float(boq_quantities.get("steel_girders_wt_total"))
    
    # Cross bracing weight: top + bottom + diagonal
    cb_top = _safe_float(boq_quantities.get("bracing_top_wt_total")) or 0.0
    cb_bot = _safe_float(boq_quantities.get("bracing_bot_wt_total")) or 0.0
    cb_diag = _safe_float(boq_quantities.get("bracing_diag_wt_total")) or 0.0
    cb_wt = cb_top + cb_bot + cb_diag
    if cb_wt <= 0:
        cb_wt = _safe_float(boq_quantities.get("steel_bracing_wt_total"))

    # End diaphragm weight if computed or separate
    ed_wt = _safe_float(boq_quantities.get("end_diaphragm_wt_total"))
    # Shear studs weight (MT)
    studs_wt = _safe_float(boq_quantities.get("shear_studs_wt_total"))

    steel_breakdown = {}
    if girders_wt is not None and girders_wt > 0:
        steel_breakdown["Plate Girders"] = girders_wt
    if cb_wt is not None and cb_wt > 0:
        steel_breakdown["Cross Bracing"] = cb_wt
    if ed_wt is not None and ed_wt > 0:
        steel_breakdown["End Diaphragms"] = ed_wt
    if studs_wt is not None and studs_wt > 0:
        steel_breakdown["Shear Studs"] = studs_wt

    # Material quantities with different physical units
    concrete_vol = _safe_float(boq_quantities.get("concrete_deck_vol_total"))
    rebar_wt = _safe_float(boq_quantities.get("rebar_deck_wt_total"))
    cb_vol = _safe_float(boq_quantities.get("crash_barrier_vol_total"))

    materials = {}
    if concrete_vol is not None and concrete_vol > 0:
        materials["Deck Concrete (m³)"] = ("m³", concrete_vol)
    if cb_vol is not None and cb_vol > 0:
        materials["Barrier Concrete (m³)"] = ("m³", cb_vol)
    if rebar_wt is not None and rebar_wt > 0:
        materials["Deck Rebar (MT)"] = ("MT", rebar_wt)

    return {
        "steel_breakdown": steel_breakdown,
        "materials": materials,
        "concrete_volume_m3": concrete_vol,
        "rebar_weight_mt": rebar_wt,
    }


# =============================================================================
# Matplotlib Chart Rendering Functions
# =============================================================================

def _render_ur_barchart(
    items: List[Dict[str, Any]],
    title: str,
    xlabel: str = "Design Check / Component",
    output_path: Optional[str] = None,
    empty_message: str = "No design check data available for this component.",
) -> Union[bytes, str]:
    """Generic bar chart renderer for utilization ratio items."""
    setup_matplotlib_style()
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    if not items:
        fig = _create_empty_banner_chart(title, empty_message)
        return _save_or_bytes(fig, output_path)

    labels = [item["name"] for item in items]
    urs = [item["ur"] for item in items]
    colors = [PASS_GREEN_HEX if item["ur"] <= 1.0 else FAIL_RED_HEX for item in items]

    # Dynamically scale chart width if there are many checks
    n = len(items)
    fig_w = max(7.5, min(12.0, 1.2 * n))
    fig, ax = plt.subplots(figsize=(fig_w, 4.0))

    bars = ax.bar(range(n), urs, color=colors, width=0.55, edgecolor="#333333", linewidth=0.7, zorder=3)

    # Apply centralized style and threshold line
    apply_chart_styling(ax, title=title, xlabel=xlabel, ylabel="Utilization Ratio (UR)", y_threshold=1.0)

    # Label on top of each bar
    y_max = max(max(urs) if urs else 1.0, 1.2)
    ax.set_ylim(0, y_max * 1.18)

    for bar, ur in zip(bars, urs):
        h = bar.get_height()
        ax.annotate(
            f"{ur:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=FONT_SIZES["bar_label"],
            fontweight="bold",
            color=TEXT_DARK_HEX,
        )

    ax.set_xticks(range(n))
    # Rotate labels if more than 4 checks or long names
    rot = 20 if (n > 4 or any(len(lbl) > 10 for lbl in labels)) else 0
    ha = "right" if rot > 0 else "center"
    ax.set_xticklabels(labels, rotation=rot, ha=ha, fontsize=FONT_SIZES["tick_label"])

    # Legend for pass/fail status + threshold
    pass_patch = mpatches.Patch(color=PASS_GREEN_HEX, label="Pass (UR ≤ 1.0)")
    fail_patch = mpatches.Patch(color=FAIL_RED_HEX, label="Fail (UR > 1.0)")
    line_patch = plt.Line2D([0], [0], color=THRESHOLD_RED_HEX, linestyle="--", linewidth=1.2, label="Limit (UR = 1.0)")
    ax.legend(handles=[pass_patch, fail_patch, line_patch], loc="upper right")

    return _save_or_bytes(fig, output_path)


def create_girder_ur_chart(output_dict: dict, input_dict: Optional[dict] = None, output_path: Optional[str] = None) -> Union[bytes, str]:
    """Generate utilization ratio chart for Steel Plate Girders."""
    items = extract_girder_utilization_ratios(output_dict, input_dict)
    return _render_ur_barchart(
        items,
        title="Steel Plate Girders — Utilization Ratios",
        xlabel="Girder Design Checks",
        output_path=output_path,
        empty_message="No girder design checks found in output dictionary.",
    )


def create_deck_ur_chart(output_dict: dict, input_dict: Optional[dict] = None, output_path: Optional[str] = None) -> Union[bytes, str]:
    """Generate utilization ratio chart for Reinforced Concrete Deck Slab."""
    items = extract_deck_utilization_ratios(output_dict, input_dict)
    return _render_ur_barchart(
        items,
        title="Concrete Deck Slab — Utilization Ratios",
        xlabel="Deck Limit State Checks",
        output_path=output_path,
        empty_message="No deck slab limit-state results found in output dictionary.",
    )


def create_cross_bracing_ur_chart(output_dict: dict, input_dict: Optional[dict] = None, output_path: Optional[str] = None) -> Union[bytes, str]:
    """Generate utilization ratio chart for Cross Bracing Members."""
    items = extract_cross_bracing_utilization_ratios(output_dict, input_dict)
    return _render_ur_barchart(
        items,
        title="Cross Bracing — Member Utilization Ratios",
        xlabel="Bracing Member Checks",
        output_path=output_path,
        empty_message="No cross bracing design checks available in output dictionary.",
    )


def create_end_diaphragm_ur_chart(output_dict: dict, input_dict: Optional[dict] = None, output_path: Optional[str] = None) -> Union[bytes, str]:
    """Generate utilization ratio chart for End Diaphragms."""
    items = extract_end_diaphragm_utilization_ratios(output_dict, input_dict)
    return _render_ur_barchart(
        items,
        title="End Diaphragms — Utilization Ratios",
        xlabel="Diaphragm Member Checks",
        output_path=output_path,
        empty_message="End Diaphragm: Rolled / Welded section (Capacity design guidance only).",
    )


def create_boq_steel_tonnage_chart(boq_quantities: dict, output_path: Optional[str] = None) -> Union[bytes, str]:
    """Generate chart for Structural Steel Tonnage Breakdown (MT) across components."""
    setup_matplotlib_style()
    import matplotlib.pyplot as plt

    extracted = extract_material_quantities(boq_quantities)
    steel_map = extracted.get("steel_breakdown", {})

    if not steel_map:
        fig = _create_empty_banner_chart(
            "Structural Steel Tonnage Breakdown",
            "No structural steel quantity data available in BOQ.",
        )
        return _save_or_bytes(fig, output_path)

    components = list(steel_map.keys())
    weights = list(steel_map.values())
    total_wt = sum(weights)

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE_STANDARD)
    bars = ax.bar(
        components, weights,
        color=STEEL_BLUE_HEX, width=0.5,
        edgecolor="#0D47A1", linewidth=0.8, zorder=3,
    )

    apply_chart_styling(
        ax,
        title=f"Structural Steel Tonnage Breakdown (Total: {total_wt:.2f} MT)",
        xlabel="Structural Component",
        ylabel="Weight (Metric Tonnes — MT)",
        y_threshold=None,
    )

    max_val = max(weights) if weights else 10.0
    ax.set_ylim(0, max_val * 1.22)

    for bar, wt in zip(bars, weights):
        h = bar.get_height()
        pct = (wt / total_wt * 100.0) if total_wt > 0 else 0
        ax.annotate(
            f"{wt:.2f} MT\n({pct:.1f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=FONT_SIZES["bar_label"],
            fontweight="bold",
            color=TEXT_DARK_HEX,
        )

    return _save_or_bytes(fig, output_path)


def create_boq_materials_chart(boq_quantities: dict, output_path: Optional[str] = None) -> Union[bytes, str]:
    """Generate side-by-side material quantity charts separating Volume (m³) and Weight (MT).
    
    Prevents confusing different physical units on the same single axis.
    """
    setup_matplotlib_style()
    import matplotlib.pyplot as plt

    extracted = extract_material_quantities(boq_quantities)
    c_vol = extracted.get("concrete_volume_m3")
    r_wt = extracted.get("rebar_weight_mt")

    if c_vol is None and r_wt is None:
        fig = _create_empty_banner_chart(
            "Material Quantities — Concrete & Reinforcement",
            "No concrete volume or rebar data available in BOQ.",
        )
        return _save_or_bytes(fig, output_path)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.8))

    # Panel 1: Concrete Volume (m³)
    if c_vol is not None and c_vol > 0:
        bar1 = ax1.bar(["Deck Slab"], [c_vol], color=CONCRETE_GRAY_HEX, width=0.45, edgecolor="#37474F", zorder=3)
        apply_chart_styling(ax1, title="Concrete Volume", xlabel="", ylabel="Volume (m³)", y_threshold=None)
        ax1.set_ylim(0, c_vol * 1.25)
        ax1.annotate(
            f"{c_vol:.2f} m³",
            xy=(bar1[0].get_x() + bar1[0].get_width() / 2, c_vol),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center", va="bottom",
            fontweight="bold", fontsize=FONT_SIZES["bar_label"],
        )
    else:
        ax1.text(0.5, 0.5, "Concrete: N/A", ha="center", va="center", transform=ax1.transAxes, style="italic")
        apply_chart_styling(ax1, title="Concrete Volume", ylabel="Volume (m³)", y_threshold=None)

    # Panel 2: Reinforcement Steel Weight (MT)
    if r_wt is not None and r_wt > 0:
        bar2 = ax2.bar(["Deck Rebar"], [r_wt], color=REBAR_ORANGE_HEX, width=0.45, edgecolor="#BF360C", zorder=3)
        apply_chart_styling(ax2, title="Reinforcement Steel", xlabel="", ylabel="Weight (MT)", y_threshold=None)
        ax2.set_ylim(0, r_wt * 1.25)
        ax2.annotate(
            f"{r_wt:.2f} MT",
            xy=(bar2[0].get_x() + bar2[0].get_width() / 2, r_wt),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center", va="bottom",
            fontweight="bold", fontsize=FONT_SIZES["bar_label"],
        )
    else:
        ax2.text(0.5, 0.5, "Rebar: N/A", ha="center", va="center", transform=ax2.transAxes, style="italic")
        apply_chart_styling(ax2, title="Reinforcement Steel", ylabel="Weight (MT)", y_threshold=None)

    fig.suptitle("Primary Material Quantities by Physical Dimension", fontsize=FONT_SIZES["title"], y=1.02, fontweight="bold")
    plt.tight_layout()

    return _save_or_bytes(fig, output_path)


def generate_all_report_visualizations(
    output_dict: dict,
    input_dict: dict,
    boq_quantities: dict,
    output_dir: Optional[str] = None,
) -> Dict[str, Union[bytes, str]]:
    """Generate all Phase 3 report charts and save to output_dir if provided.
    
    Returns a dictionary mapping figure keys to image file paths or PNG bytes:
      - 'chart_ur_girders'
      - 'chart_ur_deck'
      - 'chart_ur_cross_bracing'
      - 'chart_ur_end_diaphragm'
      - 'chart_boq_steel_tonnage'
      - 'chart_boq_materials'
    """
    charts = {}

    def _path(fname: str) -> Optional[str]:
        return os.path.join(output_dir, fname) if output_dir else None

    chart_specs = (
        ("chart_ur_girders", "chart_ur_girders.png", create_girder_ur_chart, (output_dict, input_dict)),
        ("chart_ur_deck", "chart_ur_deck.png", create_deck_ur_chart, (output_dict, input_dict)),
        ("chart_ur_cross_bracing", "chart_ur_cross_bracing.png", create_cross_bracing_ur_chart, (output_dict, input_dict)),
        ("chart_ur_end_diaphragm", "chart_ur_end_diaphragm.png", create_end_diaphragm_ur_chart, (output_dict, input_dict)),
        ("chart_boq_steel_tonnage", "chart_boq_steel_tonnage.png", create_boq_steel_tonnage_chart, (boq_quantities,)),
        ("chart_boq_materials", "chart_boq_materials.png", create_boq_materials_chart, (boq_quantities,)),
    )
    for chart_key, filename, chart_generator, args in chart_specs:
        try:
            charts[chart_key] = chart_generator(*args, output_path=_path(filename))
        except Exception:
            logger.error("Error generating report visualization %s", chart_key, exc_info=True)

    return charts
