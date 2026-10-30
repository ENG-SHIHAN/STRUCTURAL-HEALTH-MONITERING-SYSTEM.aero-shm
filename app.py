"""
AERONAUTICAL STRUCTURAL HEALTH MONITORING (SHM) SYSTEM
Interactive Full-Stack Streamlit Application

Authors: Aerospace Engineering & Computer Vision Pair Programming
Pedagogical Level: Second-Year Undergraduate Aeronautical & Aerospace Engineering
"""

import io
from typing import Optional
import streamlit as st
import numpy as np
import cv2
from PIL import Image

# Import local SHM modules
from mock_generator import (
    generate_healthy_aluminum,
    generate_fatigue_crack,
    generate_corrosion_patch,
    generate_cfrp_composite
)
from shm_cv import SHMComputerVisionPipeline, SHMAnalysisResult
from utils import (
    bgr_to_rgb,
    anomalies_to_dataframe,
    plot_defect_distribution,
    plot_histogram_comparison,
    AEROSPACE_MATERIALS
)

# -----------------------------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Aero-SHM: Airframe Structural Health Monitoring",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern aerospace dark/engineering aesthetic
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #58a6ff;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #8b949e;
        margin-bottom: 1.4rem;
    }
    .status-badge {
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 1.25rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
        color: white;
        letter-spacing: 0.5px;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f0f6fc;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .info-box {
        background-color: #0d1117;
        border-left: 4px solid #58a6ff;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 1rem;
        font-size: 0.92rem;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/fluency/96/airplane-mode-on.png", width=64)
st.sidebar.title("Aero-SHM Control")
st.sidebar.caption("FAA Part 25 / Damage Tolerance Diagnostic Console")

# 1. Specimen Input Mode Selection
input_source = st.sidebar.radio(
    "📥 Specimen Input Source",
    ["Built-in Aircraft Mock Generator", "Upload Laboratory Image"],
    index=0
)

bgr_image: Optional[np.ndarray] = None
specimen_name = ""

if input_source == "Built-in Aircraft Mock Generator":
    st.sidebar.subheader("Synthetic Specimen Config")
    specimen_preset = st.sidebar.selectbox(
        "Specimen Preset",
        [
            "Fatigue Crack at Fastener Rivet (Critical)",
            "Pitting / Exfoliation Corrosion Patch (Degraded)",
            "Healthy 2024-T3 Airframe Skin (Airworthy)",
            "CFRP Composite Panel with Surface Scratch"
        ]
    )
    seed = st.sidebar.slider("Random Generator Seed", 1, 999, 202)

    if specimen_preset == "Fatigue Crack at Fastener Rivet (Critical)":
        crack_len = st.sidebar.slider("Simulated Crack Length (px)", 60, 320, 210)
        branching = st.sidebar.checkbox("Simulate Overload Micro-Branching", value=True)
        bgr_image = generate_fatigue_crack(width=800, height=550, seed=seed, crack_length=crack_len, branching=branching)
        specimen_name = "2024-T3 Fuselage Skin (Fastener Notch Fatigue Crack)"

    elif specimen_preset == "Pitting / Exfoliation Corrosion Patch (Degraded)":
        severity = st.sidebar.select_slider("Corrosion Severity", ["mild", "moderate", "severe"], value="moderate")
        bgr_image = generate_corrosion_patch(width=800, height=550, seed=seed, severity=severity)
        specimen_name = f"7075-T6 Wing Panel ({severity.capitalize()} Corrosion Pitting)"

    elif specimen_preset == "Healthy 2024-T3 Airframe Skin (Airworthy)":
        noise = st.sidebar.slider("Rolling Grain / Noise Level", 2.0, 18.0, 7.0)
        bgr_image = generate_healthy_aluminum(width=800, height=550, seed=seed, noise_level=noise, with_rivets=True)
        specimen_name = "2024-T3 Baseline Airframe Skin (Healthy Specification)"

    else:
        cfrp_defect = st.sidebar.radio("CFRP Defect Mode", ["scratch", "delamination"])
        bgr_image = generate_cfrp_composite(width=800, height=550, seed=seed, defect_type=cfrp_defect)
        specimen_name = f"AS4/3501-6 CFRP Composite Panel ({cfrp_defect.capitalize()})"

else:
    st.sidebar.subheader("Image Upload")
    uploaded_file = st.sidebar.file_uploader(
        "Upload high-res inspection image (JPG, PNG, TIFF)",
        type=["jpg", "jpeg", "png", "tif", "tiff"]
    )
    if uploaded_file is not None:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        bgr_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        specimen_name = f"Uploaded Specimen: {uploaded_file.name}"
    else:
        st.info("👈 Please upload an image from the sidebar or switch to the Built-in Mock Generator.")
        st.stop()

# 2. Material Specification
st.sidebar.markdown("---")
st.sidebar.subheader("✈️ Airframe Alloy Specification")
material_key = st.sidebar.selectbox(
    "Active Substrate Material",
    list(AEROSPACE_MATERIALS.keys()),
    index=0
)
mat_info = AEROSPACE_MATERIALS[material_key]

# 3. CV Pipeline Hyperparameters
with st.sidebar.expander("⚙️ CV Pipeline Tuner (Advanced)", expanded=False):
    st.caption("Adjust classical digital image processing parameters:")
    clahe_clip = st.slider("CLAHE Clip Limit", 1.0, 8.0, 3.2, 0.2)
    clahe_grid = st.slider("CLAHE Tile Grid Size", 4, 16, 8, 2)
    blur_kernel = st.slider("Gaussian Blur Kernel", 3, 11, 5, 2)
    canny_low = st.slider("Canny Hysteresis Low Thresh", 10, 100, 35, 5)
    canny_high = st.slider("Canny Hysteresis High Thresh", 50, 200, 115, 5)
    filter_rivets = st.checkbox("Fastener Rivet Filtering", value=True, help="Suppresses circular fastener heads to prevent false crack positives.")
    min_area = st.slider("Min Defect Area (px)", 5, 80, 18, 1)
    px_scale = st.slider("Sensor Resolution (mm/pixel)", 0.02, 0.50, 0.10, 0.01)

# 4. Critical Engineering Thresholds
with st.sidebar.expander("🛡️ Airworthiness Limits (FAA ADL)", expanded=False):
    crit_density = st.slider("Critical Defect Density (%)", 0.1, 2.0, 0.45, 0.05)
    caution_density = st.slider("Caution Defect Density (%)", 0.02, 0.5, 0.10, 0.01)
    crit_crack_len_mm = st.slider("Critical Crack Length ac (mm)", 2.0, 30.0, 12.0, 0.5)


# -----------------------------------------------------------------------------
# RUN COMPUTER VISION PIPELINE
# -----------------------------------------------------------------------------
pipeline = SHMComputerVisionPipeline(
    clahe_clip_limit=clahe_clip,
    clahe_grid_size=clahe_grid,
    gaussian_kernel=blur_kernel,
    canny_thresh_low=canny_low,
    canny_thresh_high=canny_high,
    min_defect_area=min_area,
    pixel_to_mm_scale=px_scale,
    density_crit_threshold=crit_density,
    density_caution_threshold=caution_density,
    critical_crack_length_mm=crit_crack_len_mm
)

analysis: SHMAnalysisResult = pipeline.run_pipeline(bgr_image, filter_fasteners=filter_rivets)


# -----------------------------------------------------------------------------
# MAIN DASHBOARD INTERFACE
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">✈️ Structural Health Monitoring (SHM) System</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">Automated Optical NDT Inspection Console | Target: <strong>{specimen_name}</strong></div>', unsafe_allow_html=True)

# Prominent Interactive Airworthiness Health Status Badge
st.markdown(
    f'<div class="status-badge" style="background-color: {analysis.status_color};">'
    f'AIRFRAME STATUS: {analysis.status}'
    f'</div>',
    unsafe_allow_html=True
)

# Top KPI Metric Cards
kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

with kpi_col1:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-val">{analysis.defect_pixel_density_pct:.3f}%</div>'
        f'<div class="metric-lbl">Defect Pixel Density</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with kpi_col2:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-val">{analysis.total_defects_count}</div>'
        f'<div class="metric-lbl">Detected Anomalies</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with kpi_col3:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-val">{analysis.max_defect_length_mm:.1f} mm</div>'
        f'<div class="metric-lbl">Max Flaw Length</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with kpi_col4:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-val">{analysis.total_defect_area_pixels} px</div>'
        f'<div class="metric-lbl">Total Damaged Area</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with kpi_col5:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-val">{analysis.structural_integrity_index:.1f}%</div>'
        f'<div class="metric-lbl">Integrity Index</div>'
        f'</div>',
        unsafe_allow_html=True
    )

st.write("")

# Action advisory alert banner
if "CRITICAL" in analysis.status:
    st.error(f"🚨 **FAA/EASA Compliance Directive:** {analysis.maintenance_action}")
elif "CAUTION" in analysis.status:
    st.warning(f"⚠️ **Maintenance Advisory:** {analysis.maintenance_action}")
else:
    st.success(f"✅ **Airworthiness Clearance:** {analysis.maintenance_action}")


# -----------------------------------------------------------------------------
# MAIN TABBED WORKBENCH
# -----------------------------------------------------------------------------
tab_inspection, tab_pipeline, tab_lefm = st.tabs([
    "🔍 Optical Inspection & Defect Log",
    "🔬 Undergraduate CV Lab (Stage-by-Stage)",
    "📐 Aero-Structural Mechanics & LEFM Theory"
])

# =============================================================================
# TAB 1: INSPECTION & DEFECT LOG
# =============================================================================
with tab_inspection:
    st.subheader("High-Resolution Inspection Overlays")
    view_mode = st.radio(
        "Display Mode",
        ["Split View (Original vs Annotated)", "Damage Density Heatmap", "Side-by-Side Tri-View"],
        horizontal=True
    )

    orig_rgb = bgr_to_rgb(analysis.stages["Original"])
    annotated_rgb = bgr_to_rgb(analysis.stages["Annotated Inspection"])
    heatmap_rgb = bgr_to_rgb(analysis.stages["Damage Heatmap"])

    if view_mode == "Split View (Original vs Annotated)":
        c1, c2 = st.columns(2)
        with c1:
            st.image(orig_rgb, caption="Raw Specimen Surface", use_container_width=True)
        with c2:
            st.image(annotated_rgb, caption="Annotated Inspection with Bounding Boxes & Identifiers", use_container_width=True)

    elif view_mode == "Damage Density Heatmap":
        c1, c2 = st.columns(2)
        with c1:
            st.image(annotated_rgb, caption="Segmented Anomaly Contours", use_container_width=True)
        with c2:
            st.image(heatmap_rgb, caption="Thermal Stress / Damage Spatial Heatmap (JET)", use_container_width=True)

    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.image(orig_rgb, caption="1. Raw Surface", use_container_width=True)
        with c2:
            st.image(annotated_rgb, caption="2. Bounding Boxes & Tags", use_container_width=True)
        with c3:
            st.image(heatmap_rgb, caption="3. Damage Heatmap", use_container_width=True)

    st.markdown("---")
    
    # Anomaly Coordinates and Engineering Metrics Table
    st.subheader("📋 Detected Anomaly Log & Bounding Box Coordinates")
    df_anomalies = anomalies_to_dataframe(analysis.anomalies)

    if not df_anomalies.empty:
        col_tbl, col_plot = st.columns([1.3, 1.0])
        with col_tbl:
            st.dataframe(df_anomalies, use_container_width=True, height=280)
            
            # CSV Download Button
            csv_buffer = io.StringIO()
            df_anomalies.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Export NDT Inspection Log (CSV)",
                data=csv_buffer.getvalue(),
                file_name=f"shm_inspection_log_{specimen_preset.split()[0].lower()}.csv",
                mime="text/csv"
            )

        with col_plot:
            fig_dist = plot_defect_distribution(analysis.anomalies)
            st.pyplot(fig_dist)
    else:
        st.info("✨ No surface defects or anomalies were identified above the noise floor. Specimen meets pristine baseline standards.")


# =============================================================================
# TAB 2: UNDERGRADUATE CV LAB DECOMPOSITION
# =============================================================================
with tab_pipeline:
    st.subheader("🔬 Pedagogical Pipeline Decomposition for Aerospace Students")
    st.markdown("""
    This section exposes the intermediate algorithmic stages of the computer vision inspection engine.
    Students can inspect the mathematical transformations applied to the raw luminance field.
    """)

    # Stage 1 & 2
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        st.markdown("#### 1. Grayscale Conversion (Luminance Decoupling)")
        st.image(analysis.stages["Grayscale"], caption="Grayscale: I = 0.299R + 0.587G + 0.114B", use_container_width=True)
        st.caption("Converts 3-channel RGB to single-channel intensity. Eliminates color temperature variations caused by hangar floodlights.")

    with row1_c2:
        st.markdown("#### 2. Contrast Limited Adaptive Histogram Equalization (CLAHE)")
        st.image(analysis.stages["CLAHE Enhanced"], caption=f"CLAHE (Clip Limit={clahe_clip}, Grid={clahe_grid}x{clahe_grid})", use_container_width=True)
        st.caption("Divides image into contextual tiles. Amplifies micro-contrast of hairline fracture shadows without washing out flat aluminum skin.")

    # CLAHE Histogram Analysis
    st.pyplot(plot_histogram_comparison(analysis.stages["Grayscale"], analysis.stages["CLAHE Enhanced"]))

    # Stage 3 & 4
    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        st.markdown(f"#### 3. Gaussian Spatial Filtering (Kernel {blur_kernel}x{blur_kernel})")
        st.image(analysis.stages["Gaussian Filtered"], caption="Gaussian 2D Convolution", use_container_width=True)
        st.caption("Attenuates sensor thermal noise and cold-rolled aluminum surface striations while preserving structural edge transitions.")

    with row2_c2:
        st.markdown(f"#### 4. Canny Hysteresis Edge Detection ({canny_low} / {canny_high})")
        st.image(analysis.stages["Canny Edges"], caption="Canny Dual-Threshold Edge Ridges", use_container_width=True)
        st.caption("Calculates Sobel gradients Gx and Gy. Uses Non-Maximum Suppression (NMS) for single-pixel ridge thinning and hysteresis linking.")

    # Stage 5 & 6
    row3_c1, row3_c2 = st.columns(2)
    with row3_c1:
        st.markdown("#### 5. Adaptive Corrosion Pitting Segmentation")
        st.image(analysis.stages["Corrosion Threshold"], caption="Adaptive Local Mean Thresholding", use_container_width=True)
        st.caption("Captures clustered micro-pitting cavities and localized oxidation crusts where continuous edge contours do not form.")

    with row3_c2:
        st.markdown("#### 6. Morphological Mask Fusion & Fastener Rim Filtering")
        st.image(analysis.stages["Cleaned Defect Mask"], caption="Morphological Close & Open + Hough Rivet Filtering", use_container_width=True)
        st.caption("Fuses edge and pitting masks, closes micro-gaps along crack branches, and removes circular fastener head perimeters.")


# =============================================================================
# TAB 3: AERO-STRUCTURAL MECHANICS & LEFM THEORY
# =============================================================================
with tab_lefm:
    st.subheader("📐 Fracture Mechanics & Damage Tolerance for Aircraft Design")
    
    col_mat, col_lefm = st.columns([1.1, 1.0])

    with col_mat:
        st.markdown(f"### Substrate Material: **{material_key}**")
        st.info(f"**Description:** {mat_info['description']}")
        
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            st.metric("Tensile Yield Strength (σ_y)", f"{mat_info['yield_strength_mpa']} MPa")
            st.metric("Fracture Toughness (K_IC)", f"{mat_info['fracture_toughness_kic']} MPa√m")
        with m_c2:
            st.metric("Ultimate Strength (σ_uts)", f"{mat_info['ultimate_strength_mpa']} MPa")
            st.metric("Paris' Law Exponent (m)", f"{mat_info['paris_law_m']}")

        st.markdown(f"**Primary Applications:** {mat_info['primary_applications']}")
        st.markdown(f"**Structural Susceptibility:** {mat_info['susceptibility']}")

    with col_lefm:
        st.markdown("### Paris' Law Fatigue Propagation Calculator")
        st.markdown(r"""
        $$\frac{da}{dN} = C (\Delta K)^m = C (Y \Delta \sigma \sqrt{\pi a})^m$$
        """)
        
        delta_sigma = st.slider("Cyclic Stress Range Δσ (MPa)", 50.0, 250.0, 120.0, 5.0, help="Flight pressurization hoop stress range")
        init_crack_mm = st.number_input("Detected Crack Size a_0 (mm)", value=max(0.5, float(analysis.max_defect_length_mm)), min_value=0.1, max_value=50.0, step=0.5)

        # Theoretical LEFM calculation
        Y = 1.12  # Geometric edge crack factor
        K_IC = mat_info["fracture_toughness_kic"]
        C = mat_info["paris_law_C"]
        m = mat_info["paris_law_m"]

        # Critical crack length: a_c = (1/pi) * (K_IC / (Y * sigma_max))^2
        a_crit_m = (1.0 / np.pi) * ((K_IC / (Y * (delta_sigma * 1.2))) ** 2)
        a_crit_mm = a_crit_m * 1000.0

        st.metric("Critical Crack Length a_c", f"{a_crit_mm:.1f} mm", help="Length beyond which rapid catastrophic brittle fracture occurs.")

        if init_crack_mm >= a_crit_mm:
            st.error(f"⚠️ Current detected flaw length ({init_crack_mm:.1f} mm) EXCEEDS critical crack length ({a_crit_mm:.1f} mm)! Immediate grounding required.")
        else:
            # Estimate cycles to critical failure
            a0_m = init_crack_mm / 1000.0
            term1 = 2.0 / ((m - 2.0) * C * ((Y * delta_sigma * 1e6 * np.sqrt(np.pi)) ** m))
            term2 = (1.0 / (a0_m ** ((m - 2.0) / 2.0))) - (1.0 / (a_crit_m ** ((m - 2.0) / 2.0)))
            cycles_to_failure = max(0, int(term1 * term2))
            st.metric("Estimated Flight Cycles to Catastrophic Failure (N_f)", f"{cycles_to_failure:,} cycles")
            st.caption(f"Inspection interval recommendation: Inspect at N_f / 2 = {cycles_to_failure // 2:,} cycles.")


# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #8b949e; font-size: 0.85rem;'>"
    "Aero-SHM: Autonomous Structural Health Monitoring System | Department of Aeronautical Engineering<br>"
    "Developed with Streamlit, OpenCV, NumPy, and Matplotlib. Complies with FAA Damage Tolerance Advisory Circular AC 25.571-1D."
    "</div>",
    unsafe_allow_html=True
)
