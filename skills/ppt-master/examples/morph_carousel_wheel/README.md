# Rotating Carousel / True Wheel Morph Example (`morph_carousel_wheel`)

This portable example demonstrates the **Rigid Wheel / Rotating Dial** transition pattern using native PowerPoint Morph (`p159:morph` with `option="byObject"`).

## Core Architecture & Invariants

1. **Fixed Pivot Centering**:
   - SVG pivot coordinates: $(c_x, c_y) = (640, 400)\text{ px} = (6,096,000, 3,810,000)\text{ EMU}$.
   - Rotating group ID: `asym-rotor`.
   - DrawingML frame: Symmetrized square extent $320 \times 320\text{ px} = 3,048,000 \times 3,048,000\text{ EMU}$ centered at $(640, 400)\text{ px}$.
   - Coordinates in OpenXML DrawingML:
     - `off = (4,572,000, 2,286,000) EMU` (i.e. $480 \times 240\text{ px}$)
     - `ext = (3,048,000, 3,048,000) EMU` (i.e. $320 \times 320\text{ px}$)
     - `chOff = (4,572,000, 2,286,000) EMU`
     - `chExt = (3,048,000, 3,048,000) EMU`

2. **Invariance Across Angles**:
   - Slide 1 (`01_phase1`): `transform="rotate(0 640 400)"` $\rightarrow$ `rot="0"` (omitted in OpenXML).
   - Slide 2 (`02_phase2`): `transform="rotate(90 640 400)"` $\rightarrow$ `rot="5400000"`.
   - Slide 3 (`03_phase3`): `transform="rotate(180 640 400)"` $\rightarrow$ `rot="10800000"`.
   - Slide 4 (`04_phase4`): `transform="rotate(270 640 400)"` $\rightarrow$ `rot="16200000"`.
   - Slide 5 (`05_loop`): `transform="rotate(0 640 400)"` $\rightarrow$ loop reset.

3. **Zero-Drift Rigid Rotation Contract**:
   - Because `off`, `ext`, `chOff`, and `chExt` remain 100% byte-identical across all slides, PowerPoint receives an invariant container frame and interpolates angular rotation around the fixed pivot point $(640, 400)\text{ px}$.
   - Eliminates the previous defect where ink-derived bounding boxes caused translational drift and aspect-ratio squashing.

4. **Interactive Navigation**:
   - Cardinal phase markers (`01 INTAKE`, `02 TRANSFORM`, `03 VALIDATE`, `04 DELIVER`) are hyperlinked to their respective slides.
   - Slide 5 provides forward continuation (`#slide-2`) and restart (`#slide-1`) navigation.

## Verification Status

- Structural compilation, container parity, DrawingML invariant frame emission, and quality checker: **VERIFIED PASS**.
- Runtime native motion playback in WPS Office: **VERIFIED** (see below).
- Runtime native motion playback in Microsoft PowerPoint: **UNVERIFIED**, including the direction of the 270-to-0 degree edge into Slide 5.

## Playback Verification

All four rotation edges, the forward-cycle link, and the restart link were manually inspected in WPS Office 12.1.0.29161 on Windows. The final badge contrast correction preserves the tested actor transforms, transitions, and hyperlinks.

Sample content and metrics illustrate the animation layout; they are not product benchmarks.
