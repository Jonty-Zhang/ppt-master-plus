# Morph Card Expansion & Return Bridge Example

A polished 3-slide native PowerPoint (DrawingML) presentation demonstrating **Semantic Title & Card Expansion with a Return Bridge** (`#R-EXP-01`).

## Design Principle: Decoupled Multi-Actor Expansion

Interactive presentations often need to drill into a summary card to inspect complex metrics or architectural blueprints without losing the spatial context of the parent dashboard.

This pattern is structured with the **design intent** to prevent typography distortion, glyph re-layout, and text scaling artifacts during presentation Morph transitions by choreographing motion across **distinct, decoupled actors**:

1. **Carrier Surface Actor (`#card-alpha`)**: A pure decoration background frame (`data-pptx-role="decoration"`) that expands from a 350px column (`80 140 350 520`) into an expansive modal panel (`50 100 1180 590`, occupying $\ge 75\%$ canvas area: $75.54\%$) and collapses back on return. Decoupling the carrier shape prevents child text from being stretched or distorted during vector interpolation.
2. **Atomic Title Actor (`#title-alpha`)**: A single atomic `<text>` element (`API Ingress Gateway`) paired directly across slides. Because it contains only this exact string with identical font styling across slides, the design intent is for the presentation runtime to translate the title stably along its trajectory without font glyph re-layout or size collisions.
3. **Independent Badge & Caption Actors (`#title-alpha-badge`, `#title-alpha-caption`)**: The icon badge/tag and category subtitle are independently paired groups structured to translate stably alongside the title to their expanded modal coordinates.
4. **Anchored Page Header (`#page-header`)**: Completely fixed top header bounds ensuring absolute visual anchoring.
5. **Transient Body Content Layer (`#summary-alpha` vs `#detail-alpha`)**: High-throughput telemetry and 4-line overview copy (`#summary-alpha`) live in an independent page-local group on Slides 1 and 3, while deep multi-column specifications and topology stages (`#detail-alpha`) live in `#detail-alpha` on Slide 2. Because these groups are un-paired, the design relies on the presentation engine's native in-place cross-dissolve behavior to smoothly transition body copy, avoiding scaling old text into enlarged overlapping frames.

## Interaction Paths
- **Slide 1 (Overview Grid)**: Card Alpha has an interactive click target linking to `#slide-2`.
- **Slide 2 (Expanded Modal Inspection)**: Interactive close button wrapped in `<a href="#slide-3">` provides an explicit dismissal route.
- **Slide 3 (Return Bridge)**: Modal collapses back to summary grid; Card Alpha click target links back to `#slide-2` to allow continuous repeated inspection.

## Project Structure

```text
morph_card_expansion/
├── svg_output/
│   ├── 01_overview.svg        # Slide 1 (Overview: 3 summary cards; Card 1 clickable)
│   ├── 02_expand_alpha.svg    # Slide 2 (Modal: Card 1 expanded to >= 75% canvas; Close btn)
│   └── 03_return_overview.svg # Slide 3 (Return Bridge: Card 1 collapsed back to grid; re-open link)
├── animations.json            # Deterministic adjacent Morph pairing configuration
├── metadata.json              # Document properties
└── README.md                  # Design pattern and verification documentation
```

## Morph Pairing Configuration

`animations.json` sets up deterministic adjacent pairing for `#card-alpha`, `#title-alpha`, `#title-alpha-badge`, and `#title-alpha-caption` across expansion and collapse transitions:

```json
{
  "version": 1,
  "defaults": {
    "transition": {
      "effect": "morph",
      "effect_options": { "morph_by": "object" },
      "duration": 0.6
    },
    "animation": { "effect": "none" }
  },
  "slides": {
    "01_overview": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.6 }
    },
    "02_expand_alpha": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.6 },
      "morph": {
        "from": "01_overview",
        "pairs": {
          "card-alpha-carrier": { "from": "card-alpha", "to": "card-alpha" },
          "title-alpha-carrier": { "from": "title-alpha", "to": "title-alpha" },
          "title-alpha-badge-carrier": { "from": "title-alpha-badge", "to": "title-alpha-badge" },
          "title-alpha-caption-carrier": { "from": "title-alpha-caption", "to": "title-alpha-caption" }
        }
      }
    },
    "03_return_overview": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.6 },
      "morph": {
        "from": "02_expand_alpha",
        "pairs": {
          "card-alpha-carrier": { "from": "card-alpha", "to": "card-alpha" },
          "title-alpha-carrier": { "from": "title-alpha", "to": "title-alpha" },
          "title-alpha-badge-carrier": { "from": "title-alpha-badge", "to": "title-alpha-badge" },
          "title-alpha-caption-carrier": { "from": "title-alpha-caption", "to": "title-alpha-caption" }
        }
      }
    }
  }
}
```

## Reproduction & Verification Commands

Specify absolute execution roots using portable placeholder variables:

```powershell
# Set absolute execution roots (replace placeholders with local absolute paths)
$SkillRoot = "/path/to/skills/ppt-master"
$ExampleRoot = "$SkillRoot/examples/morph_card_expansion"

# 1. Quality check validation (zero warnings canonical authoring gate)
python "$SkillRoot/scripts/svg_quality_checker.py" "$ExampleRoot" --quick-generate --canonical-authoring --stage final --json

# 2. Export native DrawingML presentation
python "$SkillRoot/scripts/svg_to_pptx.py" "$ExampleRoot" --quick-generate --no-notes
```

## Runtime Boundary & Compatibility

- **Canvas**: Exact 16:9 widescreen canvas (`1280x720` px, matching `12,192,000 x 6,858,000` EMU).
- **Editability**: 100% native DrawingML vectors and editable text boxes. Zero rasterized full-slide screenshots.
- **Interactive Routing**: Native OpenXML `hlinkClick` anchors connect Slide 1 $\to$ Slide 2 (card click), Slide 2 $\to$ Slide 3 (close button), and Slide 3 $\to$ Slide 2 (re-open click).
- **Playback Verification Status**: Expansion, close-to-overview, and reopen links were manually exercised in WPS Office 12.1.0.29161 on Windows; sampled frames retained a single headline and separate carrier/body layers.

Sample content and metrics illustrate the animation layout; they are not product benchmarks.
