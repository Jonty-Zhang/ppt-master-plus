# Morph Hub & Persistent Spoke Navigation Example

An interactive 4-slide presentation demonstrating PowerPoint-native continuous Morph transitions combined with same-deck slide hyperlinks.

## Visual & Motion Contract

1. **Interactive Hub-and-Spoke TOC**:
   - Slide 1 serves as the central hub overview with three clickable topic cards.
   - Clicking any topic card jumps directly to that chapter's detail slide via canonical same-deck hyperlinks (`<a href="#slide-N">`).
   - Each chapter slide features a prominent return button hyperlinked back to Slide 1 (`<a href="#slide-1">`).
2. **Stationary Navigation Labels & Independent Highlight**:
   - The top navigation bar maintains **100% stationary text labels** across all four slides.
   - The active pill (`active-pill`) contains **only the moving colored background shape** (`rect`).
   - As navigation index changes, only the highlight pill glides smoothly underneath the labels; text labels never travel, resize, or cross-fade.
3. **3-Layer Decoupled Expansion Architecture**:
   - **Carrier Frame Group** (`card-alpha`, `card-beta`, `card-gamma`): Contains only background geometry (`<rect>` fills and accent bars). Scales smoothly from overview ($350 \times 510$) to hero ($1120 \times 510$) dimensions without distorting internal text coordinates.
   - **Identity Title Group** (`title-alpha`, `title-beta`, `title-gamma`): Separated into distinct groups matching stably across slides, smoothly translating into place with consistent typographic scale.
   - **Transient Detail Layer** (`summary-*` on Hub, `detail-*` on Chapters): Unpaired content layers undergo PowerPoint native in-place cross-fade, preventing old overview bullet points from stretching into giant overlapping text during expansion.
4. **Off-Canvas Staging**:
   - Inactive chapter cards and titles slide smoothly to off-canvas positions marked with `data-pptx-morph-staging="true"`.

## Project Structure

```
morph_hub_nav/
├── README.md
├── project.json
├── animations.json
└── svg_output/
    ├── 01_hub.svg
    ├── 02_topic1.svg
    ├── 03_topic2.svg
    └── 04_topic3.svg
```

## Reproducible Build Commands

From repository root:

```bash
# 1. Quality preflight verification
python3 skills/ppt-master/scripts/svg_quality_checker.py skills/ppt-master/examples/morph_hub_nav --quick-generate --canonical-authoring --stage final --json

# 2. Export to native PowerPoint DrawingML
python3 skills/ppt-master/scripts/svg_to_pptx.py skills/ppt-master/examples/morph_hub_nav --quick-generate --no-notes
```

## Verification Boundary

- **Deterministic Matching**: All four slides declare chained `morph.pairs` for 7 continuous elements: `active-pill-carrier`, `card-alpha-carrier`, `card-beta-carrier`, `card-gamma-carrier`, `title-alpha-carrier`, `title-beta-carrier`, and `title-gamma-carrier`.
- **Slide Jump Integrity**: Hyperlinks map to native `ppaction://hlinksldjump` relationships targeting Slide 1, Slide 2, Slide 3, and Slide 4.

## Playback Verification

All three chapter entry buttons and their return-to-hub buttons were manually exercised in WPS Office 12.1.0.29161 on Windows. The final EMU wording correction preserves the tested actor transforms, transitions, and hyperlinks.

Sample content and metrics illustrate the animation layout; they are not product benchmarks.
