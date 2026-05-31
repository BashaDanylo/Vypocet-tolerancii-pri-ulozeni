import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from tolerances import *

def draw_wavy_material_edge(ax, x1, x2, y_straight, y_wavy, hatch_pattern, alpha=0.25):
    xs = np.linspace(x1, x2, 100)
    ys = np.full_like(xs, y_wavy)
    mid = (x1 + x2) / 2
    span = (x2 - x1)
    w = span * 0.15
    amp = 0.12 if y_wavy > y_straight else -0.12
    for i, x in enumerate(xs):
        if mid - w <= x <= mid + w:
            ys[i] = y_wavy + amp * np.sin((x - (mid - w)) / (2 * w) * 2 * np.pi)
    ax.plot(xs, ys, color='black', linewidth=0.9)
    ax.plot([x1, x1], [y_straight, ys[0]], color='black', linewidth=0.9)
    ax.plot([x2, x2], [y_straight, ys[-1]], color='black', linewidth=0.9)
    ax.fill_between(xs, y_straight, ys, facecolor='none', edgecolor='black', hatch=hatch_pattern, alpha=alpha, linewidth=0)

def get_range_key(nominal, data_dict):
    matches = []
    for key in data_dict.keys():
        try:
            start, end = map(float, key.split('-'))
            if start <= nominal <= end:
                matches.append((key, start))
        except ValueError:
            continue

    if not matches:
        return None

    matches.sort(key=lambda x: x[1], reverse=False)
    return matches[0][0]


def draw_dim(x, y1, y2, text, text_pos='side', color='black', arrow_style='<->'):
    if abs(y1 - y2) < 0.01: return
    ax.annotate('', xy=(x, y1), xytext=(x, y2), arrowprops=dict(arrowstyle=arrow_style, color=color, lw=0.8))

    # Nastavenie podložky pre lepší kontrast
    bbox_props = dict(facecolor='white', edgecolor='none', pad=1.5, alpha=0.8)

    if text_pos == 'side':
        ax.text(x + 0.08, (y1 + y2) / 2, text, fontsize=9, va='center', ha='left',
                color=color, fontweight='bold', bbox=bbox_props)
    elif text_pos == 'center':
        ax.text(x, (y1 + y2) / 2, text, fontsize=9, va='center', ha='center',
                color=color, fontweight='bold', bbox=bbox_props)


# -----------------------------------
# Sidebar
# -----------------------------------

st.title("Vizualizácia uloženia hriadeľ – diera")

shaft_tolerance_field = st.sidebar.selectbox(
    "Tolerančné pole hriadela",
    ["-- Vyberte --"] + list(Shaft_Tolearnces.keys())
)

shaft_tolerance_options = []
if shaft_tolerance_field != "-- Vyberte --":
    shaft_tolerance_options = list(Shaft_Tolearnces[shaft_tolerance_field].keys())

shaft_tolerance_grade = st.sidebar.selectbox(
    "Stupeň tolerancie hradeľa",
    ["-- Vyberte --"] + shaft_tolerance_options
)

hole_tolerance_field = st.sidebar.selectbox(
    "Tolerančné pole diery",
    ["-- Vyberte --"] + list(Hole_Tolerances.keys())
)

# ---- SELECTBOX 2 ----
hole_tolerance_options = []
if hole_tolerance_field != "-- Vyberte --":
    hole_tolerance_options = list(Hole_Tolerances[hole_tolerance_field].keys())

hole_tolerance_grade = st.sidebar.selectbox(
    "Stupeň tolerancie diery",
    ["-- Vyberte --"] + hole_tolerance_options
)

disabled = (hole_tolerance_field == "-- Vyberte --" or hole_tolerance_grade == "-- Vyberte --" or
            shaft_tolerance_grade == "-- Vyberte --" or shaft_tolerance_field == "-- Vyberte --")

if not disabled:
    shaft_lower = Shaft_Tolearnces[shaft_tolerance_field][shaft_tolerance_grade]["size_min"]
    hole_lower = Hole_Tolerances[hole_tolerance_field][hole_tolerance_grade]["size_min"]
    min_val = max(hole_lower, shaft_lower)

    shaft_upper = Shaft_Tolearnces[shaft_tolerance_field][shaft_tolerance_grade]["size_max"]
    hole_upper = Hole_Tolerances[hole_tolerance_field][hole_tolerance_grade]["size_max"]
    max_val = min(hole_upper, shaft_upper)
else:
    min_val, max_val = 0, 0

nominal = st.sidebar.number_input(
    "Menovitý rozmer (mm)",
    min_value=float(min_val),
    max_value=float(max_val),
    step=1.0,
    format="%.2f",
    disabled=disabled
)
st.sidebar.caption(f"Povolený rozsah: **{min_val} – {max_val} mm**")

if not disabled and nominal > 0:
    shaft_data = Shaft_Tolearnces[shaft_tolerance_field][shaft_tolerance_grade]
    hole_data = Hole_Tolerances[hole_tolerance_field][hole_tolerance_grade]

    shaft_key = get_range_key(nominal, shaft_data["upper_value"])
    hole_key = get_range_key(nominal, hole_data["upper_value"])

    if shaft_key and hole_key:
        # Hodnoty v mm
        sh_upper = shaft_data["upper_value"][shaft_key] / 1000
        sh_lower = shaft_data["lower_value"][shaft_key] / 1000
        ho_upper = hole_data["upper_value"][hole_key] / 1000
        ho_lower = hole_data["lower_value"][hole_key] / 1000

        if 'H' in hole_tolerance_field.upper():
            system_type = "Sústava jednotnej diery"
        elif 'h' in shaft_tolerance_field:
            system_type = "Sústava jednotného hriadeľa"
        else:
            system_type = "Sústava aj jednotného hriadeľa aj jednotnéj diery"

        max_clearance = ho_upper - sh_lower
        min_clearance = ho_lower - sh_upper

        if min_clearance > 0:
            fit_type_str = "Hybné"
            display_info = f"Max. vôľa: {max_clearance * 1000:.3f} µm\n\nMin. vôľa: {min_clearance * 1000:.3f} µm"
        elif max_clearance < 0:
            fit_type_str = "Nehybné"
            max_interference = abs(min_clearance)
            min_interference = abs(max_clearance)
            display_info = f"Max. presah: {max_interference * 1000:.3f} µm\n\nMin. presah: {min_interference * 1000:.3f} µm"
        else:
            fit_type_str = "Prechodné"
            max_interference = abs(min_clearance)
            display_info = f"Max. vôľa: {max_clearance * 1000:.3f} µm\n\nMax. presah: {max_interference * 1000:.3f} µm"

        st.subheader("Výsledky uloženia")
        st.write(f"**Typ sústavy:** {system_type}")
        st.write(f"**Typ uloženia:** {fit_type_str}")
        st.info(display_info)
        st.write("Vypočtové premenne:")

        st.write(f"Horná odchylka diery [ES]: {ho_upper * 1000:.1f} µm")

        st.write(f"Dolná odchylka diery [EI]: {ho_lower * 1000:.1f} µm")

        st.write(f"Horná odchylka hriadeľa [es]: {sh_upper * 1000:.1f} µm")

        st.write(f"Dolná odchylka hriadeľa [ei]: {sh_lower * 1000:.1f} µm")

        # --------------------------------------------------
        # VIZUALIZÁCIA
        # --------------------------------------------------
        fig, ax = plt.subplots(figsize=(10, 7.5))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.axis('off')

        # Prepočet odchýlok na mikrometre pre popisy
        es_um, ei_um = sh_upper * 1000, sh_lower * 1000
        ES_um, EI_um = ho_upper * 1000, ho_lower * 1000

        # Dynamická mierka pre tolerančné polia (Y os)
        max_dev = max(abs(es_um), abs(ei_um), abs(ES_um), abs(EI_um), 1)
        scale_y = 1.8 / max_dev

        y_base = 1.3  # Základná čiara
        y_zero = 4.5  # Nulová čiara

        # Výpočet polôh
        y_ho_high = y_zero + ES_um * scale_y
        y_ho_low = y_zero + EI_um * scale_y
        y_sh_high = y_zero + es_um * scale_y
        y_sh_low = y_zero + ei_um * scale_y

        color_hole = '#003399'
        color_shaft = '#990000'

        # --- Referenčné čiary ---
        ax.plot([0.5, 9.5], [y_zero, y_zero], color='gray', linestyle='-', linewidth=0.8)
        ax.text(9.4, y_zero + 0.05, "nulová čiara", fontsize=9, ha='right', va='bottom', style='italic')
        ax.plot([0.5, 9.5], [y_base, y_base], color='black', linestyle='-', linewidth=1)

        # --- DIERA ---
        draw_wavy_material_edge(ax, 2.0, 4.0, y_base, 0.6, hatch_pattern='//')
        ax.plot([2.0, 2.0], [y_base, y_ho_low], color='black', linewidth=1)
        ax.plot([4.0, 4.0], [y_base, y_ho_low], color='black', linewidth=1)
        hole_tol_box = patches.Rectangle((2.0, min(y_ho_low, y_ho_high)), 2.0, abs(y_ho_high - y_ho_low),
                                         facecolor='#b3e5fc', edgecolor='black', hatch='//', alpha=0.6)
        ax.add_patch(hole_tol_box)
        y_ho_top_start = max(y_ho_low, y_ho_high)
        draw_wavy_material_edge(ax, 2.0, 4.0, y_ho_top_start, 7.6, hatch_pattern='//')
        ax.text(3.0, y_base + 0.2, f"Ø {nominal} {hole_tolerance_field}{hole_tolerance_grade}",
                fontsize=11, fontweight='bold', ha='center', va='bottom')

        # --- HRIADEĽ ---
        draw_wavy_material_edge(ax, 6.0, 8.0, y_base, 0.6, hatch_pattern='\\\\')
        ax.plot([6.0, 6.0], [y_base, y_sh_low], color='black', linewidth=1)
        ax.plot([8.0, 8.0], [y_base, y_sh_low], color='black', linewidth=1)
        shaft_tol_box = patches.Rectangle((6.0, min(y_sh_low, y_sh_high)), 2.0, abs(y_sh_high - y_sh_low),
                                          facecolor='#ffe0b2', edgecolor='black', hatch='\\\\', alpha=0.6)
        ax.add_patch(shaft_tol_box)
        ax.plot([6.0, 8.0], [y_sh_high, y_sh_high], color='black', linewidth=1.5)
        ax.text(7.0, y_base + 0.2, f"Ø {nominal} {shaft_tolerance_field}{shaft_tolerance_grade}",
                fontsize=11, fontweight='bold', ha='center', va='bottom')

        # --- KÓTOVANIE DIERY ---
        draw_dim(0.6, y_base, y_ho_high, f"Dmax", text_pos='center')
        draw_dim(1.2, y_base, y_ho_low, f"Dmin", text_pos='center')
        ax.plot([0.5, 2.0], [y_ho_high, y_ho_high], color='black', linestyle=':', linewidth=0.6)
        ax.plot([0.5, 2.0], [y_ho_low, y_ho_low], color='black', linestyle=':', linewidth=0.6)

        draw_dim(2.2, y_zero, y_ho_high, f"ES", color=color_hole)
        draw_dim(2.6, y_zero, y_ho_low, f"EI", color=color_hole)
        draw_dim(3.8, y_ho_low, y_ho_high, f"T", color=color_hole)

        # --- KÓTOVANIE HRIADEĽA ---
        draw_dim(8.8, y_base, y_sh_low, f"dmin", text_pos='center')
        draw_dim(9.4, y_base, y_sh_high, f"dmax", text_pos='center')
        ax.plot([8.0, 9.5], [y_sh_high, y_sh_high], color='black', linestyle=':', linewidth=0.6)
        ax.plot([8.0, 9.5], [y_sh_low, y_sh_low], color='black', linestyle=':', linewidth=0.6)

        draw_dim(7.8, y_zero, y_sh_high, f"es", color=color_shaft)
        draw_dim(7.4, y_zero, y_sh_low, f"ei", color=color_shaft)
        draw_dim(6.2, y_sh_low, y_sh_high, f"t", color=color_shaft)

        # --- KÓTOVANIE ULOŽENIA ---
        ax.plot([2.0, 6.0], [y_ho_high, y_ho_high], color='gray', linestyle=':', linewidth=0.5)
        ax.plot([2.0, 6.0], [y_ho_low, y_ho_low], color='gray', linestyle=':', linewidth=0.5)
        ax.plot([4.0, 8.0], [y_sh_high, y_sh_high], color='gray', linestyle=':', linewidth=0.5)
        ax.plot([4.0, 8.0], [y_sh_low, y_sh_low], color='gray', linestyle=':', linewidth=0.5)

        if fit_type_str == "Hybné":
            draw_dim(4.7, y_sh_low, y_ho_high, f"Vmax", text_pos='center', color='green')
            draw_dim(5.3, y_sh_high, y_ho_low, f"Vmin", text_pos='center', color='green')
        elif fit_type_str == "Nehybné":
            draw_dim(4.7, y_ho_low, y_sh_high, f"pmax", text_pos='center', color='purple')
            draw_dim(5.3, y_ho_high, y_sh_low, f"pmin", text_pos='center', color='purple')
        else:
            draw_dim(4.7, y_sh_low, y_ho_high, f"Vmax", text_pos='center', color='green')
            draw_dim(5.3, y_ho_low, y_sh_high, f"pmax", text_pos='center', color='purple')

        st.pyplot(fig)
    else:
        st.error("Chyba: Rozmer nie je v rozsahu tabuliek.")

