# Aero-SHM: Airframe Structural Health Monitoring System

An interactive full-stack Python & Streamlit application designed for undergraduate Aeronautical & Aerospace Engineering students. The system performs automated Non-Destructive Optical Inspection (NDI) on aircraft aluminum skins (2024-T3 / 7075-T6) and Carbon Fiber Reinforced Polymer (CFRP) composite panels using OpenCV, NumPy, and Matplotlib.

---

## ✈️ System Architecture & Engineering Features

1. **High-Resolution Inspection & Out-of-the-Box Mock Specimen Generator**:
   - Students can upload laboratory imagery or select procedurally generated aircraft specimens with realistic textures:
     - **Pristine 2024-T3 Airframe Skin** with countersunk fastener lines (MS20426 standard).
     - **Fatigue Crack Propagating from Fastener Rivet Notch** ($K_t \approx 3.0$ stress concentration, jagged transgranular path).
     - **Pitting & Exfoliation Corrosion Patch** (sacrificial cladding breakdown, micro-cavities).
     - **CFRP Composite Panel** ($0^\circ/90^\circ$ twill weave with surface gouge / delamination).

2. **Automated Computer Vision & Edge-Detection Pipeline (`shm_cv.py`)**:
   - **Stage 1: Grayscale & Luminance Decoupling**: Eliminates color bias from hangar lighting.
   - **Stage 2: CLAHE Contrast Enhancement**: Enhances micro-cracks without saturating smooth aluminum.
   - **Stage 3: 2D Gaussian Spatial Filtering**: Attenuates rolling grain striations and sensor noise.
   - **Stage 4: Canny Gradient & Hysteresis Edge Detection**: Sobel gradients with Non-Maximum Suppression (NMS).
   - **Stage 5: Adaptive Localized Corrosion Segmentation**: Captures non-continuous oxidation clusters.
   - **Stage 6: Morphological Refinement & Fusion**: Closing bridges fracture micro-gaps; opening removes salt noise.
   - **Stage 7: Circular Fastener Head Suppression**: Prevents normal rivets from causing false defect alarms.
   - **Stage 8: Geometric Invariant Feature Extraction**: Bounding boxes, aspect ratios, centroids, and solidities.
   - **Stage 9: Airworthiness Assessment**: Computes defect pixel density ($\%$) and assigns FAA/EASA-compliant status (`HEALTHY`, `CAUTION`, `CRITICAL`).

3. **Real-Time Engineering Metrics & Interactive Dashboard**:
   - Dynamic Airworthiness Status Badge (Green / Amber / Red).
   - Defect Pixel Density ($\%$), Max Flaw Dimension ($mm$), Total Damaged Pixels ($px$).
   - Interactive Anomaly Log Table with Bounding Box coordinates $[X, Y, W, H]$ and CSV export.
   - Paris' Law Cyclic Crack Growth Calculator ($\frac{da}{dN} = C(\Delta K)^m$) and remaining cycles to failure ($N_f$).

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- `uv` or standard Python `pip`

### 2. Activate Environment & Run Application
```bash
# Navigate to the project directory
cd "C:\Users\moham\.gemini\antigravity\scratch\aero_shm_app"

# If using the pre-configured virtual environment:
.\.venv\Scripts\activate

# Launch the Streamlit application
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Run Automated Verification Test Suite
```bash
.\.venv\Scripts\python.exe verify_shm.py
```

---

## 📂 Project Structure
```
aero_shm_app/
├── app.py                   # Streamlit dashboard interface & interactive workbench
├── shm_cv.py                # Core OpenCV computer vision and damage tolerance pipeline
├── mock_generator.py        # Procedural aeronautical specimen generator (no dataset needed)
├── utils.py                 # Aerospace materials database, plotting, and CSV formatters
├── verify_shm.py            # Automated test suite and validation engine
├── requirements.txt         # Project dependencies
└── verification_artifacts/  # Generated validation reports and annotated inspection images
```

---

## 📖 Academic Presentation Topics
- **LEFM (Linear Elastic Fracture Mechanics)**: Stress intensity factors ($K = Y \sigma \sqrt{\pi a}$) and critical flaw length ($a_c$).
- **Damage Tolerance Philosophy (FAA AC 25.571-1D)**: Fail-safe design, threshold crack detection, and scheduled inspection intervals ($N_f / 2$).
- **Digital Image Processing**: How CLAHE prevents over-amplification of noise compared to global histogram equalization.
