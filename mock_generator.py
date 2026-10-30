"""
AERONAUTICAL STRUCTURAL HEALTH MONITORING (SHM) SYSTEM
Module: mock_generator.py
Purpose: Fallback synthetic specimen generator producing high-resolution,
         physically plausible aircraft surface images for undergraduate SHM labs.

Aeronautical Engineering Concepts Covered:
1. 2024-T3 / 7075-T6 Clad Aluminum Alloy Surface Morphology (Brushed rolling grain,
   anodized protective film, specular reflectivity).
2. Fastener Lines & Rivet Rows (Countersunk MS20426 rivets, pitch/edge-distance ratios,
   high stress-concentration factor Kt around fastener holes).
3. Fatigue Crack Propagation (Linear Elastic Fracture Mechanics - LEFM, stress risers,
   transgranular jagged crack paths, crack tip tapering).
4. Pitting and Exfoliation Corrosion (Localized breakdown of passivating Al2O3 layer,
   micro-cavities, galvanic oxidation crusts).
5. Carbon Fiber Reinforced Polymers (CFRP) (Twill weave fabric, epoxy matrix scratches,
   delamination signatures).
"""

from typing import Tuple, Optional
import numpy as np
import cv2


def _apply_brushed_metal_texture(
    base_image: np.ndarray,
    grain_intensity: float = 12.0,
    rng: Optional[np.random.Generator] = None
) -> np.ndarray:
    """
    Simulates directional cold-rolled grain texture characteristic of 
    aerospace-grade aluminum sheet (AMS-QQ-A-250/4 / 2024-T3).

    Rolling direction produces anisotropic microscopic striations.
    We simulate this via 1D Gaussian-filtered noise stretched horizontally.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    h, w = base_image.shape[:2]
    # Generate high-frequency noise
    noise = rng.normal(0, grain_intensity, (h, w)).astype(np.float32)
    
    # Anisotropic horizontal blur simulates the mechanical rolling/brushing direction
    kernel_size = (31, 3)
    brushed_noise = cv2.GaussianBlur(noise, kernel_size, sigmaX=8.0, sigmaY=0.8)
    
    textured = base_image.astype(np.float32) + brushed_noise[:, :, np.newaxis]
    return np.clip(textured, 0, 255).astype(np.uint8)


def _render_aerospace_rivet(
    img: np.ndarray,
    center: Tuple[int, int],
    radius: int = 24,
    countersunk: bool = True
) -> None:
    """
    Renders an aeronautical flush countersunk rivet (e.g., MS20426 100° flush rivet).
    Features modeled:
    - Outer chamfer perimeter line
    - Spherical illumination gradient (light source from top-left)
    - Fastener center driven indentation / tool mark
    - Surrounding annular stress field micro-shadow
    """
    cx, cy = int(center[0]), int(center[1])
    h, w = img.shape[:2]

    # Subtle circular shadow around fastener perimeter (micro-recess)
    cv2.circle(img, (cx, cy), radius + 2, (110, 115, 120), 1, lineType=cv2.LINE_AA)

    # Fastener head gradient
    y, x = np.ogrid[:h, :w]
    dist_sq = (x - cx) ** 2 + (y - cy) ** 2
    mask = dist_sq <= radius ** 2

    # Vector pointing towards simulated top-left light source
    lx, ly = cx - radius * 0.4, cy - radius * 0.4
    light_dist = np.sqrt((x - lx) ** 2 + (y - ly) ** 2) / (radius * 1.5)
    light_dist = np.clip(light_dist, 0.0, 1.0)

    # Specular metallic shading for the rivet button
    shading = (210 - light_dist * 85).astype(np.uint8)
    
    for c in range(3):
        channel = img[:, :, c]
        # Color tone: slightly cooler alloy tint for 2117-T4 rivet material
        alloy_shading = np.clip(shading + (10 if c == 0 else 0), 0, 255).astype(np.uint8)
        channel[mask] = alloy_shading[mask]
        img[:, :, c] = channel

    # Outer perimeter ring
    cv2.circle(img, (cx, cy), radius, (90, 95, 100), 2, lineType=cv2.LINE_AA)
    # Center indentation (manufacturing punch / bucking bar dimple)
    cv2.circle(img, (cx, cy), max(2, radius // 6), (70, 75, 80), -1, lineType=cv2.LINE_AA)
    cv2.circle(img, (cx, cy), max(2, radius // 6), (180, 185, 190), 1, lineType=cv2.LINE_AA)


def generate_healthy_aluminum(
    width: int = 800,
    height: int = 600,
    seed: int = 101,
    noise_level: float = 8.0,
    with_rivets: bool = True
) -> np.ndarray:
    """
    Generates a pristine, undamaged baseline specimen of aircraft aluminum skin.
    Complies with FAA airworthiness standards (no detectable surface flaws).

    Returns:
        np.ndarray: BGR image suitable for OpenCV display and inspection.
    """
    rng = np.random.default_rng(seed)

    # Base aluminum tone: Silver-grey (approx RGB [192, 198, 204], BGR [204, 198, 192])
    base_color = np.array([200, 195, 190], dtype=np.float32)
    img = np.full((height, width, 3), base_color, dtype=np.float32)

    # Subtle lighting gradient across wing panel (ambient illumination falloff)
    gradient_x = np.linspace(-10, 15, width, dtype=np.float32)
    gradient_y = np.linspace(-8, 12, height, dtype=np.float32)[:, np.newaxis]
    img[:, :, 0] += gradient_x + gradient_y
    img[:, :, 1] += gradient_x + gradient_y
    img[:, :, 2] += gradient_x + gradient_y
    img = np.clip(img, 0, 255).astype(np.uint8)

    # Apply rolling grain texture
    img = _apply_brushed_metal_texture(img, grain_intensity=noise_level, rng=rng)

    # Add standard fastener line (pitch = 4D to 5D spacing)
    if with_rivets:
        rivet_radius = 22
        rivet_pitch = 160
        y_pos = height // 2
        for x_pos in range(80, width - 40, rivet_pitch):
            _render_aerospace_rivet(img, (x_pos, y_pos), radius=rivet_radius)

    return img


def generate_fatigue_crack(
    width: int = 800,
    height: int = 600,
    seed: int = 202,
    crack_origin: str = "rivet",
    crack_length: int = 210,
    branching: bool = True
) -> np.ndarray:
    """
    Simulates a high-stress mechanical fatigue crack in an airframe skin.

    Physical Background for Students:
    - Fastener holes introduce a theoretical stress concentration factor Kt ≈ 3.0.
    - Under cyclic flight pressurization loads (fuselage hoop stress σ_hoop = P*r/t),
      microcracks initiate at fastener hole boundaries.
    - Propagation follows Linear Elastic Fracture Mechanics (Paris' Law: da/dN = C*(ΔK)^m).
    - Morphologically, cracks exhibit tortuous paths, sharp jagged angles along
      crystallographic slip bands, and crack tip opening displacement (CTOD) tapering.
    """
    rng = np.random.default_rng(seed)
    img = generate_healthy_aluminum(width=width, height=height, seed=seed, with_rivets=True)

    rivet_x = 240
    rivet_y = height // 2
    rivet_radius = 22

    if crack_origin == "rivet":
        # Initiation at the right boundary of the rivet hole (stress concentration zone)
        start_x = rivet_x + rivet_radius
        start_y = rivet_y + int(rng.integers(-4, 4))
    else:
        start_x = width // 3
        start_y = height // 2

    # Simulate crack trajectory via constrained random walk with horizontal tension drift
    points = [(int(start_x), int(start_y))]
    curr_x, curr_y = float(start_x), float(start_y)
    
    remaining_len = crack_length
    
    while remaining_len > 0 and curr_x < width - 20:
        # High tensile stress causes predominant horizontal growth (+x)
        dx = float(rng.uniform(2.5, 4.8))
        # Jagged crystallographic deviation
        dy = float(rng.normal(0.0, 1.7))
        curr_x += dx
        curr_y += dy
        points.append((int(curr_x), int(curr_y)))
        remaining_len -= int(np.sqrt(dx**2 + dy**2))

    # Render main crack with realistic tapering width (wider at root, sub-pixel at tip)
    n_pts = len(points)
    for i in range(n_pts - 1):
        pt1 = points[i]
        pt2 = points[i + 1]
        
        # Tapering from ~3px at notch down to 1px at the crack tip
        fraction = i / max(1, n_pts)
        thickness = max(1, int(3.2 * (1.0 - fraction**0.7)))
        
        # Dark fracture shadow (inner crack cavity)
        cv2.line(img, pt1, pt2, (25, 25, 30), thickness=thickness, lineType=cv2.LINE_AA)
        
        # Plastic deformation / micro-fretting halo around crack flanks
        if fraction < 0.6 and rng.random() > 0.4:
            fretting_pt = (int(pt1[0] + rng.integers(-2, 3)), int(pt1[1] + rng.integers(-2, 3)))
            cv2.circle(img, fretting_pt, 1, (65, 68, 72), -1, lineType=cv2.LINE_AA)

    # Secondary micro-branching (characteristic of high-amplitude overload cycles)
    if branching and n_pts > 20:
        branch_idx = int(n_pts * rng.uniform(0.35, 0.65))
        bx, by = float(points[branch_idx][0]), float(points[branch_idx][1])
        b_len = int(rng.integers(25, 55))
        b_points = [(int(bx), int(by))]
        
        # Branch shoots off at an acute shear angle (~30° to 45°)
        angle_sign = float(rng.choice([-1.0, 1.0]))
        for _ in range(b_len // 4):
            bx += float(rng.uniform(2.0, 3.8))
            by += angle_sign * float(rng.uniform(1.2, 3.0)) + float(rng.normal(0, 0.8))
            b_points.append((int(bx), int(by)))
            
        for i in range(len(b_points) - 1):
            cv2.line(img, b_points[i], b_points[i + 1], (30, 30, 35), thickness=1, lineType=cv2.LINE_AA)

    return img


def generate_corrosion_patch(
    width: int = 800,
    height: int = 600,
    seed: int = 303,
    severity: str = "moderate"
) -> np.ndarray:
    """
    Simulates pitting and exfoliation corrosion on aircraft alloy skin.

    Physical Background for Students:
    - Aluminum cladding (Alclad) provides sacrificial cathodic protection.
    - Moisture, de-icing salts, or marine atmospheric chlorides breach the cladding.
    - Electrochemical micro-cells produce pitting corrosion: deep localized pits
      acting as severe stress notches.
    - Exfoliation occurs along elongated grain boundaries in 7000-series alloys,
      causing flaking, blistering, and dark powdery corrosion products (Al(OH)3).
    """
    rng = np.random.default_rng(seed)
    img = generate_healthy_aluminum(width=width, height=height, seed=seed, with_rivets=True)

    # Define epicenter of corrosion attack (often near lap joints or water-traps)
    center_x = int(rng.integers(width // 3, 2 * width // 3))
    center_y = int(rng.integers(height // 3, 2 * height // 3))

    num_pits = {"mild": 80, "moderate": 220, "severe": 500}.get(severity, 220)
    cluster_radius_x = int(rng.integers(70, 130))
    cluster_radius_y = int(rng.integers(40, 85))

    # 1. Oxidized discolored halo (exfoliation blister zone)
    overlay = img.copy()
    cv2.ellipse(
        overlay,
        (center_x, center_y),
        (cluster_radius_x + 30, cluster_radius_y + 20),
        angle=int(rng.integers(-15, 15)),
        startAngle=0,
        endAngle=360,
        color=(135, 138, 142),
        thickness=-1
    )
    # Blend discoloration softly with original surface
    cv2.addWeighted(overlay, 0.45, img, 0.55, 0, img)

    # 2. Individual pitting cavities and micro-craters
    for _ in range(num_pits):
        # Generate clustered distribution centered around corrosion core
        dx = int(rng.normal(0, cluster_radius_x * 0.45))
        dy = int(rng.normal(0, cluster_radius_y * 0.45))
        pit_x = int(np.clip(center_x + dx, 5, width - 6))
        pit_y = int(np.clip(center_y + dy, 5, height - 6))

        pit_r = int(rng.integers(1, 5))
        # Deep pit core (dark corrosion product / cavity shadow)
        pit_color = int(rng.integers(20, 60))
        cv2.circle(img, (pit_x, pit_y), pit_r, (pit_color, pit_color + 2, pit_color + 5), -1)

        # White/grey crystalline oxidation ring surrounding pit mouth
        if rng.random() > 0.4:
            crust_color = int(rng.integers(220, 250))
            cv2.circle(img, (pit_x, pit_y), pit_r + 1, (crust_color, crust_color, crust_color), 1)

    return img


def generate_cfrp_composite(
    width: int = 800,
    height: int = 600,
    seed: int = 404,
    defect_type: str = "scratch"
) -> np.ndarray:
    """
    Generates a Carbon Fiber Reinforced Polymer (CFRP) composite panel
    with surface matrix cracking, fiber scratch, or localized impact damage.

    Physical Background for Students:
    - Modern aerospace structures (Boeing 787, Airbus A350) utilize CFRP for >50%
      of primary airframe weight.
    - CFRP consists of high-strength carbon fibers embedded in an epoxy polymer matrix.
    - Visual inspection seeks Barely Visible Impact Damage (BVID), matrix crazing,
      and gouges that could cause internal inter-laminar delamination.
    """
    rng = np.random.default_rng(seed)

    # Base carbon weave: alternating 0°/90° or 2x2 twill weave pattern
    y_coords, x_coords = np.ogrid[:height, :width]
    
    # Spatial frequency of carbon fiber bundles (tows)
    tow_size = 16
    weave_x = ((x_coords // tow_size) % 2)
    weave_y = ((y_coords // tow_size) % 2)
    twill = (weave_x ^ weave_y).astype(np.float32)

    # Base dark graphite tone (RGB [35, 38, 42] / BGR [42, 38, 35])
    panel = np.zeros((height, width, 3), dtype=np.float32)
    base_lum = 38.0 + twill * 22.0  # Specular difference between warp and weft
    
    # Fine carbon filament micro-grain
    filament_noise = rng.normal(0, 4.0, (height, width)).astype(np.float32)
    
    for c in range(3):
        panel[:, :, c] = np.clip(base_lum + filament_noise, 15, 95)
        
    img = panel.astype(np.uint8)

    if defect_type == "scratch":
        # Surface scratch breaking through epoxy coat and severing carbon tows
        x1, y1 = int(rng.integers(80, width // 3)), int(rng.integers(100, height // 2))
        x2, y2 = int(x1 + rng.integers(180, 320)), int(y1 + rng.integers(60, 180))
        
        # Scratched resin creates bright whitish/translucent scuff
        cv2.line(img, (x1, y1), (x2, y2), (210, 215, 220), thickness=2, lineType=cv2.LINE_AA)
        
        # Broken fiber groove shadow
        cv2.line(img, (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), (15, 15, 18), thickness=1, lineType=cv2.LINE_AA)

    elif defect_type == "delamination":
        # Low-velocity impact site (blunt impact from tool drop or hail)
        impact_x = int(width // 2)
        impact_y = int(height // 2)
        # Blistering ring
        cv2.circle(img, (impact_x, impact_y), 45, (130, 135, 140), 2, lineType=cv2.LINE_AA)
        cv2.circle(img, (impact_x, impact_y), 15, (15, 15, 20), -1, lineType=cv2.LINE_AA)
        
        # Radial micro-cracks
        for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            rad_x = int(impact_x + np.cos(angle) * rng.uniform(25, 60))
            rad_y = int(impact_y + np.sin(angle) * rng.uniform(25, 60))
            cv2.line(img, (impact_x, impact_y), (rad_x, rad_y), (170, 175, 180), 1, lineType=cv2.LINE_AA)

    return img
