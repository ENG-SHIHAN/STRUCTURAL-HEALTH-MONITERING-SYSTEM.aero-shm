"""
AERONAUTICAL STRUCTURAL HEALTH MONITORING (SHM) SYSTEM
Module: shm_cv.py
Purpose: Modular, pedagogical Computer Vision & Edge-Detection Pipeline
         for aircraft skin fatigue cracks, corrosion, and composite irregularities.

Author: Aero-SHM Engineering Lab
Target Level: Second-Year Undergraduate Aeronautical & Aerospace Engineering
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import numpy as np
import cv2


@dataclass
class DefectAnomaly:
    """
    Represents an individual structural anomaly detected on the aircraft skin.
    Contains spatial, geometric, and non-destructive testing (NDT) metrics.
    """
    defect_id: int
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    centroid: Tuple[int, int]         # (cx, cy)
    area_pixels: float                # Surface area of defect in pixels
    perimeter_pixels: float           # Boundary perimeter
    aspect_ratio: float               # max(w, h) / min(w, h) - crack elongation metric
    solidity: float                   # Contour Area / Convex Hull Area
    extent: float                     # Contour Area / Bounding Box Area
    defect_type: str                  # Fatigue Crack, Corrosion Pitting, Surface Scratch, etc.
    severity: str                     # Low, Moderate, High, Critical
    estimated_length_mm: float        # Calibrated physical length in millimeters


@dataclass
class SHMAnalysisResult:
    """
    Comprehensive Structural Health Monitoring inspection report.
    Aggregates global airframe integrity metrics and segmented visual stages.
    """
    status: str                       # 'HEALTHY', 'CAUTION / DEGRADED', 'CRITICAL - GROUND AIRCRAFT'
    status_color: str                 # Hex color for UI badges
    defect_pixel_density_pct: float   # Damaged Area / Total Inspected Area * 100%
    total_defects_count: int
    total_defect_area_pixels: int
    max_defect_dimension_px: float
    max_defect_length_mm: float
    structural_integrity_index: float # 0.0 to 100.0% structural health rating
    anomalies: List[DefectAnomaly] = field(default_factory=list)
    stages: Dict[str, np.ndarray] = field(default_factory=dict)
    maintenance_action: str = ""
    airworthiness_assessment: str = ""


class SHMComputerVisionPipeline:
    """
    Pedagogical CV pipeline designed to demonstrate classic digital image processing
    applied to aeronautical non-destructive inspection (NDI).

    Engineering Pipeline Steps:
    1. Grayscale & Luminance Decoupling
    2. Contrast Limited Adaptive Histogram Equalization (CLAHE)
    3. Gaussian Spatial Filtering (Sensor Noise Attenuation)
    4. Canny Gradient & Hysteresis Edge Detection
    5. Adaptive Localized Corrosion Segmentation
    6. Morphological Mask Fusion & Topological Cleaning
    7. Fastener (Rivet) Geometry Suppression
    8. Contour Geometry & Aeromechanical Classification
    9. Global Airframe Structural Integrity Evaluation
    """

    def __init__(
        self,
        clahe_clip_limit: float = 3.2,
        clahe_grid_size: int = 8,
        gaussian_kernel: int = 5,
        canny_thresh_low: int = 35,
        canny_thresh_high: int = 115,
        min_defect_area: int = 18,
        pixel_to_mm_scale: float = 0.1,  # 1 pixel = 0.1 mm (10 px/mm)
        density_crit_threshold: float = 0.45,
        density_caution_threshold: float = 0.10,
        critical_crack_length_mm: float = 12.0
    ):
        """
        Initializes pipeline parameters with tunable engineering thresholds.
        """
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_grid_size = clahe_grid_size
        self.gaussian_kernel = gaussian_kernel if gaussian_kernel % 2 == 1 else gaussian_kernel + 1
        self.canny_thresh_low = canny_thresh_low
        self.canny_thresh_high = canny_thresh_high
        self.min_defect_area = min_defect_area
        self.pixel_to_mm_scale = pixel_to_mm_scale
        self.density_crit_threshold = density_crit_threshold
        self.density_caution_threshold = density_caution_threshold
        self.critical_crack_length_mm = critical_crack_length_mm

    def run_pipeline(
        self,
        bgr_image: np.ndarray,
        filter_fasteners: bool = True
    ) -> SHMAnalysisResult:
        """
        Executes the full structural health monitoring inspection workflow.

        Args:
            bgr_image: Input raw inspection image (numpy array, BGR format).
            filter_fasteners: If True, identifies circular rivet geometries to prevent
                              normal fastener boundaries from triggering false alarms.

        Returns:
            SHMAnalysisResult with engineering metrics and visual diagnostic stages.
        """
        h, w = bgr_image.shape[:2]
        total_roi_pixels = h * w
        stages: Dict[str, np.ndarray] = {"Original": bgr_image.copy()}

        # -------------------------------------------------------------
        # STAGE 1: Grayscale Luminance Conversion
        # Aeronautical note: Color is often dominated by ambient hangar
        # lighting or paint sheen. Structural flaws (cracks, cavities)
        # cause micro-shadows best characterized in luminance space.
        # -------------------------------------------------------------
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        stages["Grayscale"] = gray

        # -------------------------------------------------------------
        # STAGE 2: Contrast Limited Adaptive Histogram Equalization (CLAHE)
        # Why CLAHE for aerospace?
        # Standard Global Histogram Equalization over-amplifies grain noise
        # across flat aluminum skins. CLAHE operates on localized 8x8 tiles,
        # clipping histogram peaks to prevent noise saturation while vastly
        # boosting local contrast of sub-millimeter hairline cracks.
        # -------------------------------------------------------------
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=(self.clahe_grid_size, self.clahe_grid_size)
        )
        equalized = clahe.apply(gray)
        stages["CLAHE Enhanced"] = equalized

        # -------------------------------------------------------------
        # STAGE 3: Gaussian Spatial Filtering
        # Mathematical foundation: 2D Gaussian kernel G(x,y) suppresses
        # high-frequency optical sensor noise and aluminum cold-rolling
        # grain without severely blurring high-gradient crack boundaries.
        # -------------------------------------------------------------
        blurred = cv2.GaussianBlur(
            equalized,
            (self.gaussian_kernel, self.gaussian_kernel),
            sigmaX=1.2,
            sigmaY=1.2
        )
        stages["Gaussian Filtered"] = blurred

        # -------------------------------------------------------------
        # STAGE 4: Canny Edge Detection (Cracks & Structural Discontinuities)
        # 1. Gradient magnitude & angle via Sobel operators:
        #    G = sqrt(Gx^2 + Gy^2), theta = arctan(Gy/Gx)
        # 2. Non-Maximum Suppression (NMS) creates 1-pixel thin ridges.
        # 3. Dual-threshold Hysteresis links weak fracture edges to strong ones.
        # -------------------------------------------------------------
        canny_edges = cv2.Canny(
            blurred,
            threshold1=self.canny_thresh_low,
            threshold2=self.canny_thresh_high,
            apertureSize=3,
            L2gradient=True
        )
        stages["Canny Edges"] = canny_edges

        # -------------------------------------------------------------
        # STAGE 5: Adaptive Localized Corrosion / Pitting Segmentation
        # Corrosion creates clustered dark micro-pits and oxidation crusts
        # that may not form continuous edge lines. We use adaptive
        # thresholding to isolate localized reflectance drop-offs.
        # -------------------------------------------------------------
        corrosion_thresh = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=19,
            C=8
        )
        stages["Corrosion Threshold"] = corrosion_thresh

        # -------------------------------------------------------------
        # STAGE 6: Morphological Refinement & Structural Mask Fusion
        # - Closing (dilation then erosion) connects disjointed crack segments.
        # - Opening (erosion then dilation) eliminates isolated sensor salt noise.
        # -------------------------------------------------------------
        # Combine Canny edge map with corrosion pit mask
        combined_raw = cv2.bitwise_or(canny_edges, corrosion_thresh)

        # Elliptical / rectangular structuring elements
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))

        # Close micro-voids along crack trajectories
        closed_mask = cv2.morphologyEx(combined_raw, cv2.MORPH_CLOSE, kernel_close, iterations=1)
        # Suppress single-pixel salt noise
        cleaned_mask = cv2.morphologyEx(closed_mask, cv2.MORPH_OPEN, kernel_open, iterations=1)

        # -------------------------------------------------------------
        # STAGE 7: Fastener Rivet Suppression (Normal Geometry Masking)
        # Detect circular rivet patterns using Hough Circle Transform so normal
        # fastener boundaries are not counted as damage, UNLESS an irregular crack
        # extends outside the fastener diameter into the sheet.
        # -------------------------------------------------------------
        fastener_mask = np.zeros_like(cleaned_mask)
        if filter_fasteners:
            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                dp=1.2,
                minDist=50,
                param1=100,
                param2=24,
                minRadius=16,
                maxRadius=38
            )
            if circles is not None:
                circles = np.uint16(np.around(circles))
                for pt in circles[0, :]:
                    cx, cy, r = pt[0], pt[1], pt[2]
                    # Mask the entire body of normal fasteners (radius + 2px buffer)
                    cv2.circle(fastener_mask, (cx, cy), int(r * 1.15), 255, thickness=-1)

            # Subtract normal fastener bodies from damage mask
            cleaned_mask = cv2.bitwise_and(cleaned_mask, cv2.bitwise_not(fastener_mask))

        stages["Cleaned Defect Mask"] = cleaned_mask

        # -------------------------------------------------------------
        # STAGE 8: Connected Component Analysis & Anomaly Feature Extraction
        # Extract geometric invariant properties:
        # - Bounding Box (x, y, w, h)
        # - Aspect Ratio: max(w,h) / min(w,h) (Fatigue cracks have high AR > 3.2)
        # - Solidity: Area / ConvexHullArea (Cracks and jagged corrosion < 0.6)
        # - Physical size in mm
        # -------------------------------------------------------------
        contours, _ = cv2.findContours(
            cleaned_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        anomalies: List[DefectAnomaly] = []
        annotated_overlay = bgr_image.copy()
        heatmap = np.zeros((h, w), dtype=np.float32)

        defect_idx = 1
        max_dim_px = 0.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_defect_area:
                continue

            perimeter = cv2.arcLength(cnt, closed=True)
            if perimeter <= 0:
                continue

            # Circularity metric: 4 * pi * Area / Perimeter^2 (1.0 = perfect circle)
            circularity = float((4.0 * np.pi * area) / (perimeter ** 2))

            x, y, bw, bh = cv2.boundingRect(cnt)
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = float(area / hull_area) if hull_area > 0 else 0.0
            extent = float(area / (bw * bh)) if (bw * bh) > 0 else 0.0

            # Compute elongation / aspect ratio
            major_dim = max(bw, bh)
            minor_dim = max(1, min(bw, bh))
            aspect_ratio = float(major_dim / minor_dim)

            # Filter out any lingering circular fastener remnant
            if filter_fasteners and circularity > 0.60 and aspect_ratio < 1.35:
                continue

            if major_dim > max_dim_px:
                max_dim_px = float(major_dim)

            # Centroid computation via image spatial moments
            moments = cv2.moments(cnt)
            if moments["m00"] != 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
            else:
                cx, cy = x + bw // 2, y + bh // 2

            # Physical length calibration
            length_mm = major_dim * self.pixel_to_mm_scale

            # Aeromechanical Classification Heuristics
            defect_type, severity, box_color = self._classify_defect(
                area, aspect_ratio, solidity, length_mm
            )

            anomaly = DefectAnomaly(
                defect_id=defect_idx,
                bbox=(x, y, bw, bh),
                centroid=(cx, cy),
                area_pixels=float(area),
                perimeter_pixels=float(perimeter),
                aspect_ratio=round(aspect_ratio, 2),
                solidity=round(solidity, 2),
                extent=round(extent, 2),
                defect_type=defect_type,
                severity=severity,
                estimated_length_mm=round(length_mm, 2)
            )
            anomalies.append(anomaly)

            # Draw visual annotations on overlay
            # 1. Bounding box
            cv2.rectangle(annotated_overlay, (x, y), (x + bw, y + bh), box_color, 2)
            
            # 2. Contour boundary (neon trace)
            cv2.drawContours(annotated_overlay, [cnt], -1, (0, 255, 255), 1)

            # 3. Label tag
            tag = f"#{defect_idx} {defect_type[:4]} {length_mm:.1f}mm"
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
            cv2.rectangle(
                annotated_overlay,
                (x, max(0, y - th - 6)),
                (x + tw + 6, y),
                box_color,
                -1
            )
            cv2.putText(
                annotated_overlay,
                tag,
                (x + 3, max(th + 2, y - 3)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.40,
                (255, 255, 255),
                1,
                lineType=cv2.LINE_AA
            )

            # Accumulate spatial damage intensity into heatmap
            cv2.drawContours(heatmap, [cnt], -1, 1.0, thickness=-1)
            defect_idx += 1

        # Smooth and colorize damage heatmap
        heatmap = cv2.GaussianBlur(heatmap, (25, 25), sigmaX=8.0)
        heatmap_norm = np.clip(heatmap * 255.0, 0, 255).astype(np.uint8)
        color_heatmap = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)

        # Alpha-blend heatmap onto original inspection image
        heatmap_overlay = cv2.addWeighted(bgr_image, 0.65, color_heatmap, 0.35, 0)

        stages["Annotated Inspection"] = annotated_overlay
        stages["Damage Heatmap"] = heatmap_overlay

        # -------------------------------------------------------------
        # STAGE 9: Global Airframe Structural Integrity Evaluation
        # -------------------------------------------------------------
        total_defect_pixels = sum(int(a.area_pixels) for a in anomalies)
        defect_density_pct = (total_defect_pixels / total_roi_pixels) * 100.0
        max_length_mm = max_dim_px * self.pixel_to_mm_scale

        status, status_color, health_index, action, assessment = self._compute_airworthiness_status(
            defect_density_pct, max_length_mm, anomalies
        )

        return SHMAnalysisResult(
            status=status,
            status_color=status_color,
            defect_pixel_density_pct=round(defect_density_pct, 4),
            total_defects_count=len(anomalies),
            total_defect_area_pixels=total_defect_pixels,
            max_defect_dimension_px=round(max_dim_px, 1),
            max_defect_length_mm=round(max_length_mm, 2),
            structural_integrity_index=round(health_index, 1),
            anomalies=anomalies,
            stages=stages,
            maintenance_action=action,
            airworthiness_assessment=assessment
        )

    def _classify_defect(
        self,
        area: float,
        aspect_ratio: float,
        solidity: float,
        length_mm: float
    ) -> Tuple[str, str, Tuple[int, int, int]]:
        """
        Classifies an identified anomaly using aeromechanical morphology rules.

        Returns:
            Tuple of (defect_type, severity, bgr_color)
        """
        # Linear Elastic Fracture Mechanics criteria:
        # Cracks are narrow, highly directional, and jagged (high AR, low solidity)
        if aspect_ratio >= 3.0:
            if length_mm >= self.critical_crack_length_mm:
                return "Critical Fatigue Crack", "Critical", (0, 0, 230)  # Bright Red
            elif length_mm >= 5.0:
                return "Developing Fatigue Crack", "High", (0, 100, 255)   # Amber/Orange
            else:
                return "Micro-Crack / Hairline", "Moderate", (0, 165, 255)

        # Corrosion criteria:
        # Pitting and exfoliation form dispersed clusters with moderate elongation
        # but very irregular boundaries (moderate AR, lower solidity)
        elif area > 100 and solidity < 0.72:
            if area > 450:
                return "Exfoliation Corrosion", "High", (0, 140, 255)
            else:
                return "Pitting Corrosion Patch", "Moderate", (0, 215, 255)

        # Composite / Surface scuff:
        elif aspect_ratio >= 2.0 and solidity >= 0.65:
            return "Surface Scratch / Gouge", "Moderate", (255, 140, 0)

        # Minor structural void / irregularity
        else:
            return "Structural Irregularity", "Low", (200, 200, 0)

    def _compute_airworthiness_status(
        self,
        density_pct: float,
        max_length_mm: float,
        anomalies: List[DefectAnomaly]
    ) -> Tuple[str, str, float, str, str]:
        """
        Computes FAA/EASA-aligned Damage Tolerance & Airworthiness Status.
        """
        has_critical_crack = any(
            "Critical Fatigue Crack" in a.defect_type or a.estimated_length_mm >= self.critical_crack_length_mm
            for a in anomalies
        )
        high_severity_count = sum(1 for a in anomalies if a.severity in ("High", "Critical"))

        # Base structural health index (100% = pristine airframe skin)
        penalty = min(95.0, (density_pct * 80.0) + (max_length_mm * 1.5) + (high_severity_count * 8.0))
        health_index = max(5.0, 100.0 - penalty)

        if density_pct >= self.density_crit_threshold or has_critical_crack or health_index < 60.0:
            status = "CRITICAL - GROUND AIRCRAFT"
            status_color = "#dc3545"  # Danger Red
            action = (
                "IMMEDIATE ACTION REQUIRED: Structural defect exceeds allowable damage limit (ADL). "
                "Ground aircraft for secondary High-Frequency Eddy Current (HFEC) or Phased Array "
                "Ultrasonic Testing (PAUT). Issue FAA Form 8130-3 Major Repair / Structural Alteration."
            )
            assessment = "UNSAFE: Exceeds critical crack/corrosion threshold. Structural failure hazard."

        elif density_pct >= self.density_caution_threshold or high_severity_count > 0 or health_index < 85.0:
            status = "CAUTION - DEGRADED"
            status_color = "#ffc107"  # Warning Amber
            action = (
                "SCHEDULED MAINTENANCE REQUIRED: Surface anomaly detected within tolerable limits. "
                "Apply stop-drill or corrosion inhibitor compound (CIC) per Structural Repair Manual (SRM). "
                "Re-inspect at next A-Check (500 flight hours)."
            )
            assessment = "AIRWORTHY WITH RESTRICTIONS: Monitor propagation rate under cyclic flight loads."

        else:
            status = "HEALTHY - AIRWORTHY"
            status_color = "#28a745"  # Success Green
            action = (
                "NORMAL STATUS: Structural panel meets FAA Part 25 airworthiness standards. "
                "No defects exceeding NDT threshold. Clear for commercial revenue flight."
            )
            assessment = "AIRWORTHY: Surface integrity fully intact. Routine visual inspection valid."

        return status, status_color, health_index, action, assessment
