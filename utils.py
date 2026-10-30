"""
AERONAUTICAL STRUCTURAL HEALTH MONITORING (SHM) SYSTEM
Module: utils.py
Purpose: Engineering visualization utilities, aerospace materials library,
         and diagnostic charting for academic presentations.
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import cv2

from shm_cv import DefectAnomaly, SHMAnalysisResult


# Aerospace Structural Materials Specification Database
AEROSPACE_MATERIALS: Dict[str, Dict[str, Any]] = {
    "Al 2024-T3 (Al-Cu-Mg)": {
        "description": "Standard fuselage skin alloy. High fracture toughness, excellent fatigue resistance with Alclad sacrificial cladding.",
        "yield_strength_mpa": 345,
        "ultimate_strength_mpa": 483,
        "fracture_toughness_kic": 34.0,  # MPa*sqrt(m)
        "paris_law_C": 1.2e-11,
        "paris_law_m": 3.4,
        "primary_applications": "Fuselage skins, lower wing tension skins, shear webs.",
        "susceptibility": "Fatigue cracking at fastener holes; exfoliation/pitting corrosion when cladding is breached."
    },
    "Al 7075-T6 (Al-Zn-Mg-Cu)": {
        "description": "High-strength zinc alloy. Superior compressive yield strength, but lower fracture toughness and higher stress-corrosion susceptibility.",
        "yield_strength_mpa": 503,
        "ultimate_strength_mpa": 572,
        "fracture_toughness_kic": 29.0,
        "paris_law_C": 2.5e-11,
        "paris_law_m": 3.8,
        "primary_applications": "Upper wing compression skins, spar caps, fuselage frames.",
        "susceptibility": "Stress corrosion cracking (SCC), fast brittle fracture once critical crack length is reached."
    },
    "CFRP Composite (Carbon/Epoxy)": {
        "description": "Twill/Unidirectional carbon fibers embedded in toughened epoxy matrix. Zero corrosion, excellent specific stiffness.",
        "yield_strength_mpa": 1850,
        "ultimate_strength_mpa": 2280,
        "fracture_toughness_kic": 45.0,  # Equivalent interlaminar G_IC
        "paris_law_C": 5.0e-13,
        "paris_law_m": 4.5,
        "primary_applications": "Boeing 787 / A350 wings, empennage, fuselage barrel sections.",
        "susceptibility": "Barely Visible Impact Damage (BVID), delamination, matrix micro-crazing."
    }
}


def bgr_to_rgb(bgr_array: np.ndarray) -> np.ndarray:
    """Converts an OpenCV BGR image array to RGB for Streamlit/Matplotlib display."""
    return cv2.cvtColor(bgr_array, cv2.COLOR_BGR2RGB)


def anomalies_to_dataframe(anomalies: List[DefectAnomaly]) -> pd.DataFrame:
    """
    Converts list of DefectAnomaly dataclass objects into a clean,
    academically formatted pandas DataFrame.
    """
    if not anomalies:
        return pd.DataFrame(columns=[
            "Defect ID", "Classification", "Severity", "Length (mm)",
            "Area (px)", "Aspect Ratio", "Solidity", "Bounding Box [X, Y, W, H]", "Centroid"
        ])

    records = []
    for a in anomalies:
        records.append({
            "Defect ID": f"#{a.defect_id}",
            "Classification": a.defect_type,
            "Severity": a.severity,
            "Length (mm)": a.estimated_length_mm,
            "Area (px)": int(a.area_pixels),
            "Aspect Ratio": a.aspect_ratio,
            "Solidity": a.solidity,
            "Bounding Box [X, Y, W, H]": f"[{a.bbox[0]}, {a.bbox[1]}, {a.bbox[2]}, {a.bbox[3]}]",
            "Centroid": f"({a.centroid[0]}, {a.centroid[1]})"
        })

    return pd.DataFrame(records)


def plot_defect_distribution(anomalies: List[DefectAnomaly]) -> plt.Figure:
    """
    Generates a multi-panel aeronautical engineering diagnostic chart:
    1. Aspect Ratio vs Area scatter plot (demonstrates clustering between cracks and corrosion).
    2. Defect classification counts.
    """
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), dpi=120)
    fig.patch.set_facecolor("#0e1117")

    for ax in axes:
        ax.set_facecolor("#161b22")
        ax.tick_params(colors="#c9d1d9")
        for spine in ax.spines.values():
            spine.set_color("#30363d")

    if not anomalies:
        axes[0].text(
            0.5, 0.5, "No Defects Detected\n(Airframe Structure Pristine)",
            color="#28a745", ha="center", va="center", fontsize=12, fontweight="bold"
        )
        axes[1].text(
            0.5, 0.5, "100% Structural Integrity",
            color="#28a745", ha="center", va="center", fontsize=12, fontweight="bold"
        )
        plt.tight_layout()
        return fig

    # Plot 1: Aspect Ratio vs Area (LEFM vs Corrosion morphological separation)
    areas = [a.area_pixels for a in anomalies]
    aspect_ratios = [a.aspect_ratio for a in anomalies]
    colors = [
        "#ff4b4b" if "Crack" in a.defect_type else "#ffa726" if "Corrosion" in a.defect_type else "#29b6f6"
        for a in anomalies
    ]

    axes[0].scatter(areas, aspect_ratios, c=colors, s=55, alpha=0.85, edgecolors="#ffffff", linewidth=0.6)
    axes[0].axhline(y=3.2, color="#ff4b4b", linestyle="--", linewidth=1.0, label="Crack Threshold (AR >= 3.2)")
    axes[0].set_xlabel("Defect Pixel Area", color="#c9d1d9", fontsize=9)
    axes[0].set_ylabel("Aspect Ratio (Elongation)", color="#c9d1d9", fontsize=9)
    axes[0].set_title("Morphological Clustering (Crack vs Pit)", color="#ffffff", fontsize=10, fontweight="bold")
    axes[0].legend(facecolor="#21262d", edgecolor="#30363d", labelcolor="#c9d1d9", fontsize=8)
    axes[0].grid(True, linestyle=":", alpha=0.3, color="#8b949e")

    # Plot 2: Defect Classification Breakdown
    categories = [a.defect_type for a in anomalies]
    unique_cats, counts = np.unique(categories, return_counts=True)
    
    bar_colors = ["#ff4b4b" if "Crack" in c else "#ffa726" if "Corrosion" in c else "#29b6f6" for c in unique_cats]
    bars = axes[1].barh(unique_cats, counts, color=bar_colors, edgecolor="#ffffff", height=0.55, linewidth=0.5)
    axes[1].set_xlabel("Anomaly Count", color="#c9d1d9", fontsize=9)
    axes[1].set_title("Damage Type Distribution", color="#ffffff", fontsize=10, fontweight="bold")
    axes[1].grid(True, axis="x", linestyle=":", alpha=0.3, color="#8b949e")

    for bar in bars:
        w = bar.get_width()
        axes[1].text(w + 0.1, bar.get_y() + bar.get_height() / 2, f"{int(w)}",
                     va="center", color="#ffffff", fontsize=9, fontweight="bold")

    plt.tight_layout()
    return fig


def plot_histogram_comparison(gray_img: np.ndarray, clahe_img: np.ndarray) -> plt.Figure:
    """
    Plots the pixel intensity histograms before and after CLAHE.
    Academic demonstration of dynamic range enhancement.
    """
    fig, ax = plt.subplots(figsize=(6, 2.8), dpi=110)
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#161b22")
    ax.tick_params(colors="#c9d1d9")
    for spine in ax.spines.values():
        spine.set_color("#30363d")

    hist_gray = cv2.calcHist([gray_img], [0], None, [256], [0, 256])
    hist_clahe = cv2.calcHist([clahe_img], [0], None, [256], [0, 256])

    ax.plot(hist_gray, color="#8b949e", linewidth=1.5, label="Raw Grayscale")
    ax.plot(hist_clahe, color="#58a6ff", linewidth=1.5, label="After CLAHE")
    ax.fill_between(range(256), hist_clahe.flatten(), color="#58a6ff", alpha=0.25)
    
    ax.set_title("Luminance Dynamic Range (CLAHE Redistribution)", color="#ffffff", fontsize=9, fontweight="bold")
    ax.set_xlabel("Pixel Intensity (0-255)", color="#c9d1d9", fontsize=8)
    ax.set_ylabel("Pixel Count", color="#c9d1d9", fontsize=8)
    ax.legend(facecolor="#21262d", edgecolor="#30363d", labelcolor="#c9d1d9", fontsize=8)
    ax.grid(True, linestyle=":", alpha=0.3, color="#8b949e")

    plt.tight_layout()
    return fig
