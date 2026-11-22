# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value

def ch3_loads(input_dict, output_dict=None):
    if output_dict is None:
        output_dict = {}
    # Live load vehicle names mapping
    vehicles = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        vehicles.append("Class A")
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        vehicles.append("Class 70R (Wheeled)")
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        vehicles.append("Class 70R (Tracked)")
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        vehicles.append("Class AA (Wheeled)")
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        vehicles.append("Class AA (Tracked)")
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        vehicles.append("Class SV")
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        vehicles.append("Class 70R (Bogie)")
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        vehicles.append("Class Fatigue")
    
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get('name'):
                vehicles.append(c['name'])
            elif isinstance(c, str):
                vehicles.append(c)
                
    vehicles_str = ", ".join(vehicles) if vehicles else "None"

    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    span = input_dict.get(KEY_SPAN)
    span_m = None
    if span not in (None, ""):
        try:
            span_m = float(span)
        except Exception:
            span_m = None

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_val_str = "---"
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_val_str = f"{braking_force_kN:.2f}"
        except Exception:
            braking_force_val_str = "---"

    ecc_val = input_dict.get(KEY_LL_ECCENTRICITY)
    if ecc_val not in (None, ""):
        try:
            ecc_str = f"{float(str(ecc_val).replace('m', '').strip()):.2f}"
        except Exception:
            ecc_str = str(ecc_val)
    else:
        ecc_str = "---"

    vehicle_rows = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        im_a_str = f"{1.0 + IRC6_2017.cl_208_2_impact_factor(span_m):.3f}" if span_m is not None else "---"
        load_a = sum(IRC6_2017.cl_204_1_ClassA_vehicle()["wheel_loads"]) / 1000.0
        vehicle_rows.append(
            f"\\textnormal{{Class A}} & {load_a:.2f} & {im_a_str} & {braking_force_val_str} & {ecc_str} \\\\[6pt]\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        im_70r_str = f"{1.0 + IRC6_2017.cl_208_3_impact_factor(span_m):.3f}" if span_m is not None else "---"
        load_70rw = sum(IRC6_2017.cl_204_1_Class70R_vehicle_wheel()["wheel_loads"]) / 1000.0
        vehicle_rows.append(
            f"\\textnormal{{Class 70R (Wheeled)}} & {load_70rw:.2f} & {im_70r_str} & {braking_force_val_str} & {ecc_str} \\\\[6pt]\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        im_70rt_str = f"{1.0 + IRC6_2017.cl_208_3_impact_factor(span_m):.3f}" if span_m is not None else "---"
        vehicle_rows.append(
            f"\\textnormal{{Class 70R (Tracked)}} & 700.00 & {im_70rt_str} & {braking_force_val_str} & {ecc_str} \\\\[6pt]\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        im_aaw_str = f"{1.0 + IRC6_2017.cl_208_3_impact_factor(span_m):.3f}" if span_m is not None else "---"
        vehicle_rows.append(
            f"\\textnormal{{Class AA (Wheeled)}} & 400.00 & {im_aaw_str} & {braking_force_val_str} & {ecc_str} \\\\[6pt]\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        im_aat_str = f"{1.0 + IRC6_2017.cl_208_3_impact_factor(span_m):.3f}" if span_m is not None else "---"
        vehicle_rows.append(
            f"\\textnormal{{Class AA (Tracked)}} & 700.00 & {im_aat_str} & {braking_force_val_str} & {ecc_str} \\\\[6pt]\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        sv_load = IRC6_2017.cl_204_5_1_special_vehicle().get("total_load_kN", 3776.85)
        vehicle_rows.append(
            f"\\textnormal{{Class SV}} & {sv_load:.2f} & 1.000 & {braking_force_val_str} & {ecc_str} \\\\[6pt]\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        im_bog_str = f"{1.0 + IRC6_2017.cl_208_3_impact_factor(span_m):.3f}" if span_m is not None else "---"
        vehicle_rows.append(
            f"\\textnormal{{Class 70R (Bogie)}} & 392.40 & {im_bog_str} & {braking_force_val_str} & {ecc_str} \\\\[6pt]\n\\hline"
        )
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        load_fat = sum(IRC6_2017.cl_204_6_fatigue_load()["wheel_loads"]) / 1000.0
        vehicle_rows.append(
            f"\\textnormal{{Class Fatigue}} & {load_fat:.2f} & 1.000 & --- & {ecc_str} \\\\[6pt]\n\\hline"
        )
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            c_name = c.get('name') if isinstance(c, dict) else str(c)
            if c_name:
                vehicle_rows.append(
                    f"\\textnormal{{{_tex(c_name)}}} & --- & --- & {braking_force_val_str} & {ecc_str} \\\\[6pt]\n\\hline"
                )
    if not vehicle_rows:
        vehicle_rows.append(
            r"\textnormal{None Selected} & --- & --- & --- & --- \\[6pt]" + "\n" + r"\hline"
        )
    vehicle_rows_str = "\n".join(vehicle_rows)

    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_str = f"{IRC6_2017.cl_206_1_footway_load():.3f} kN/m² (IRC 6 Cl. 206.1)"
        except Exception:
            fp_str = "N/A"
    elif fp_value not in (None, ""):
        fp_str = f"{fp_value} kN/m²"
    else:
        fp_str = "N/A"

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "") else "N/A"

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral    = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah          = _res.get("Ah")
            if not sl_av:
                sl_av          = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # Seismic forces (longitudinal and transverse)
    # Check output_dict and input_dict first; if missing, derive via IRC6 if inputs exist
    seismic_fx = output_dict.get("seismic_force_longitudinal") or output_dict.get("seismic_fx") or input_dict.get("seismic_force_longitudinal")
    seismic_fz = output_dict.get("seismic_force_transverse") or output_dict.get("seismic_fz") or input_dict.get("seismic_force_transverse")
    
    if seismic_fx is None or seismic_fz is None:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            
            if _zone and (_dead > 0 or _live > 0):
                if seismic_fx is None:
                    _res_long = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                                                     live_load_kN=_live, period_T=float(_tp) if _tp else None,
                                                     damping_percent=float(_damp), direction='parallel')
                    seismic_fx = _res_long.get("Feq_design") or _res_long.get("Feq")
                if seismic_fz is None:
                    _res_trans = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                                                      live_load_kN=_live, period_T=float(_tp) if _tp else None,
                                                      damping_percent=float(_damp), direction='perpendicular')
                    seismic_fz = _res_trans.get("Feq_design") or _res_trans.get("Feq")
        except Exception:
            pass

    seismic_fx_str = f"{float(seismic_fx):.2f}" if seismic_fx not in (None, "") else ""
    seismic_fz_str = f"{float(seismic_fz):.2f}" if seismic_fz not in (None, "") else ""

    # Table 3.6 — Temperature: compute effective bridge temp range from shade temps
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res    = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean   = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise     = f"{_bt_max - _mean:.2f}"
            tl_fall     = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # --- Table 3.7: Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textit{Dead Load -- Self Weight (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endhead
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textit{Dead Load for Surfacing (DW) (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endhead
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{3.5cm}|C{2.6cm}|C{2.6cm}|C{3.0cm}|C{2.8cm}|}
\caption{\textbf{Live Loads (LL) --- Vehicle Details}} \\
\hline
\textbf{Vehicle Class} & \textbf{Total Load (kN)} & \textbf{Impact Factor} & \textbf{Braking Load (kN)} & \textbf{Eccentricity (m)} \\[6pt]
\hline
\endfirsthead
\caption[]{\textit{Live Loads (LL) --- Vehicle Details (continued)}} \\
\hline
\textbf{Vehicle Class} & \textbf{Total Load (kN)} & \textbf{Impact Factor} & \textbf{Braking Load (kN)} & \textbf{Eccentricity (m)} \\[6pt]
\hline
\endhead
""" + vehicle_rows_str + r"""
\end{longtable}
\noindent\textit{Note: Vehicle load configurations per IRC 6:2017 Clause 204. Impact factor per Clause 208. Longitudinal braking load per Clause 211.2 applied to carriageway.}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Footpath / Pedestrian Live Load}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textit{Footpath / Pedestrian Live Load (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endhead
\textnormal{Footpath Live Load (if applicable)} & """ + _tex(fp_str) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 6:2017 Clause 206.1.}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textit{Wind Load (WL) --- per IRC 6 (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endhead
\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict,'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')) + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, ' N/m\\textsuperscript{2}')) + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textit{Earthquake Load (EL) --- per IRC 6 (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endhead
\textnormal{Seismic Zone} & """ + (_render_value(input_dict,'seismic_zone')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & """ + (_tex(seismic_fx_str) + ' kN' if seismic_fx_str else '') + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & """ + (_tex(seismic_fz_str) + ' kN' if seismic_fz_str else '') + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endfirsthead
\caption[]{\textit{Temperature Load (TL) --- per IRC 6 (continued)}} \\
\hline
\textbf{parameter} & \textbf{value} \\[6pt]
\hline
\endhead
\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}} \\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endfirsthead
\caption[]{\textit{Load Combinations (continued)}} \\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endhead
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


