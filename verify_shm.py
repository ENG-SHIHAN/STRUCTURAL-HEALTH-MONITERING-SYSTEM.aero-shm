"""
Automated Verification Suite for Aero-SHM System
Validates computer vision algorithms, mock image generator, metric computations,
and outputs detailed verification logs.
"""

import os
import sys
import time
import numpy as np
import cv2

from mock_generator import (
    generate_healthy_aluminum,
    generate_fatigue_crack,
    generate_corrosion_patch,
    generate_cfrp_composite
)
from shm_cv import SHMComputerVisionPipeline
from utils import anomalies_to_dataframe, AEROSPACE_MATERIALS

def run_verification():
    log_lines = []
    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("=" * 70)
    log("AERO-SHM SYSTEM AUTOMATED VERIFICATION SUITE")
    log("=" * 70)
    start_time = time.time()

    pipeline = SHMComputerVisionPipeline(
        clahe_clip_limit=3.2,
        clahe_grid_size=8,
        gaussian_kernel=5,
        canny_thresh_low=35,
        canny_thresh_high=115,
        min_defect_area=18,
        pixel_to_mm_scale=0.10,
        density_crit_threshold=0.45,
        density_caution_threshold=0.10,
        critical_crack_length_mm=12.0
    )

    output_dir = os.path.join(os.path.dirname(__file__), "verification_artifacts")
    os.makedirs(output_dir, exist_ok=True)

    # -------------------------------------------------------------
    # TEST CASE 1: Healthy 2024-T3 Baseline Airframe Skin
    # -------------------------------------------------------------
    log("\n[TEST CASE 1] Generating Healthy 2024-T3 Baseline Specimen...")
    healthy_img = generate_healthy_aluminum(width=800, height=550, seed=101, noise_level=6.0, with_rivets=True)
    assert healthy_img.shape == (550, 800, 3), f"Unexpected shape: {healthy_img.shape}"
    log(f"  -> Generated specimen image: shape={healthy_img.shape}, dtype={healthy_img.dtype}")

    res_healthy = pipeline.run_pipeline(healthy_img, filter_fasteners=True)
    log(f"  -> Health Status: {res_healthy.status}")
    log(f"  -> Defect Density: {res_healthy.defect_pixel_density_pct:.4f}%")
    log(f"  -> Detected Defects: {res_healthy.total_defects_count}")
    log(f"  -> Integrity Index: {res_healthy.structural_integrity_index:.1f}%")
    assert "HEALTHY" in res_healthy.status, f"Expected HEALTHY, got {res_healthy.status}"
    assert res_healthy.defect_pixel_density_pct < 0.10, "Defect density should be minimal for pristine skin"
    cv2.imwrite(os.path.join(output_dir, "test1_healthy_annotated.png"), res_healthy.stages["Annotated Inspection"])
    log("  [PASS] Test Case 1 passed.")

    # -------------------------------------------------------------
    # TEST CASE 2: Fatigue Crack Propagating from Fastener Rivet
    # -------------------------------------------------------------
    log("\n[TEST CASE 2] Generating Fastener Fatigue Crack Specimen...")
    crack_img = generate_fatigue_crack(width=800, height=550, seed=202, crack_length=220, branching=True)
    log(f"  -> Generated specimen image: shape={crack_img.shape}")

    res_crack = pipeline.run_pipeline(crack_img, filter_fasteners=True)
    log(f"  -> Health Status: {res_crack.status}")
    log(f"  -> Defect Density: {res_crack.defect_pixel_density_pct:.4f}%")
    log(f"  -> Detected Defects: {res_crack.total_defects_count}")
    log(f"  -> Max Flaw Dimension: {res_crack.max_defect_dimension_px} px ({res_crack.max_defect_length_mm:.1f} mm)")
    log(f"  -> Integrity Index: {res_crack.structural_integrity_index:.1f}%")

    assert res_crack.total_defects_count > 0, "Failed to detect crack anomalies"
    # Find crack defect
    crack_defects = [a for a in res_crack.anomalies if "Crack" in a.defect_type]
    log(f"  -> Identified {len(crack_defects)} fatigue crack segment(s)")
    for a in crack_defects:
        log(f"     * Defect #{a.defect_id}: Type={a.defect_type}, AR={a.aspect_ratio}, Length={a.estimated_length_mm}mm, BBox={a.bbox}")
    assert len(crack_defects) > 0, "Should classify at least one anomaly as Fatigue Crack"
    assert "CRITICAL" in res_crack.status or "CAUTION" in res_crack.status

    cv2.imwrite(os.path.join(output_dir, "test2_crack_annotated.png"), res_crack.stages["Annotated Inspection"])
    cv2.imwrite(os.path.join(output_dir, "test2_crack_heatmap.png"), res_crack.stages["Damage Heatmap"])
    log("  [PASS] Test Case 2 passed.")

    # -------------------------------------------------------------
    # TEST CASE 3: Pitting / Exfoliation Corrosion Patch
    # -------------------------------------------------------------
    log("\n[TEST CASE 3] Generating Exfoliation Corrosion Patch Specimen...")
    corrosion_img = generate_corrosion_patch(width=800, height=550, seed=303, severity="moderate")
    log(f"  -> Generated specimen image: shape={corrosion_img.shape}")

    res_corrosion = pipeline.run_pipeline(corrosion_img, filter_fasteners=True)
    log(f"  -> Health Status: {res_corrosion.status}")
    log(f"  -> Defect Density: {res_corrosion.defect_pixel_density_pct:.4f}%")
    log(f"  -> Detected Defects: {res_corrosion.total_defects_count}")
    log(f"  -> Total Damaged Pixels: {res_corrosion.total_defect_area_pixels}")
    assert res_corrosion.total_defects_count >= 3, "Corrosion patch should produce multiple localized defect clusters"

    cv2.imwrite(os.path.join(output_dir, "test3_corrosion_annotated.png"), res_corrosion.stages["Annotated Inspection"])
    log("  [PASS] Test Case 3 passed.")

    # -------------------------------------------------------------
    # TEST CASE 4: Carbon Fiber (CFRP) Composite Panel Scratch
    # -------------------------------------------------------------
    log("\n[TEST CASE 4] Generating CFRP Composite Panel Specimen...")
    cfrp_img = generate_cfrp_composite(width=800, height=550, seed=404, defect_type="scratch")
    log(f"  -> Generated specimen image: shape={cfrp_img.shape}")

    res_cfrp = pipeline.run_pipeline(cfrp_img, filter_fasteners=False)
    log(f"  -> Health Status: {res_cfrp.status}")
    log(f"  -> Detected Defects: {res_cfrp.total_defects_count}")
    assert res_cfrp.total_defects_count > 0, "CFRP scratch should be detected"

    cv2.imwrite(os.path.join(output_dir, "test4_cfrp_annotated.png"), res_cfrp.stages["Annotated Inspection"])
    log("  [PASS] Test Case 4 passed.")

    # -------------------------------------------------------------
    # TEST CASE 5: DataFrame and Materials Database Verification
    # -------------------------------------------------------------
    log("\n[TEST CASE 5] Verifying DataFrame formatting and Materials Library...")
    df = anomalies_to_dataframe(res_crack.anomalies)
    log(f"  -> DataFrame rows: {len(df)}, columns: {list(df.columns)}")
    assert not df.empty
    assert "Defect ID" in df.columns and "Bounding Box [X, Y, W, H]" in df.columns
    assert len(AEROSPACE_MATERIALS) >= 3
    log("  [PASS] Test Case 5 passed.")

    elapsed = time.time() - start_time
    log("\n" + "=" * 70)
    log(f"ALL 5 TEST CASES PASSED SUCCESSFULLY in {elapsed:.2f} seconds!")
    log("=" * 70)

    # Save log to file
    with open(os.path.join(output_dir, "verification_report.txt"), "w") as f:
        f.write("\n".join(log_lines))

    return log_lines

if __name__ == "__main__":
    run_verification()
