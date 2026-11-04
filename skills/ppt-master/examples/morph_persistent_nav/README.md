# Morph Persistent Navigation Example

A polished 4-slide native PowerPoint (DrawingML) presentation demonstrating persistent navigation with an **independently moving highlight pill** and **stationary text labels**.

## Design Principle: Static Labels vs. Moving Highlight Pill

In common automated presentations, navigation bars are often grouped as whole units per tab (label + background) and paired together in Morph transitions. This causes the text labels to slide, stretch, or cross-fade unpleasantly across slides when transitioning between pages.

This demonstration separates concerns into three distinct layers:
1. **Persistent Navigation Frame**: A stable top-level container (`#nav-track`) establishing the navigation bar bounds.
2. **Autonomous Highlight Carrier**: A standalone vector pill group (`#highlight-pill`) without text that moves along the X-axis across slides.
3. **Stationary Interactive Labels**: Distinct, fixed hyperlink groups (`#nav-tab-1` through `#nav-tab-4`) that maintain exact identical coordinates, typography, and hit areas across every slide. Each tab provides a canonical `<a href="#slide-N">` anchor allowing direct navigation to any destination (adjacent, nonadjacent, or return).

The **design intent** for Morph transitions across compliant presentation runtimes is:
- Only the autonomous highlight pill glides horizontally between tab positions.
- All tab labels remain completely stationary and crisp, without text drift or resizing.
- Slide body content updates according to its own scene hierarchy.

## Project Structure

```text
morph_persistent_nav/
├── svg_output/
│   ├── 01_overview.svg        # Slide 1 (Overview active: pill at x=196)
│   ├── 02_features.svg        # Slide 2 (Features active: pill at x=420)
│   ├── 03_architecture.svg    # Slide 3 (Architecture active: pill at x=644)
│   └── 04_roadmap.svg         # Slide 4 (Roadmap active: pill at x=868)
├── animations.json            # Deterministic Morph pairing (nav-highlight key)
├── metadata.json              # Document properties
└── README.md                  # Specification and recipe documentation
```

## Morph Pairing Configuration

`animations.json` establishes a deterministic adjacent pairing chain for `#highlight-pill` across all four slides:

```json
{
  "version": 1,
  "defaults": {
    "transition": {
      "effect": "morph",
      "effect_options": { "morph_by": "object" },
      "duration": 0.5
    },
    "animation": { "effect": "none" }
  },
  "slides": {
    "01_overview": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.5 }
    },
    "02_features": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.5 },
      "morph": {
        "from": "01_overview",
        "pairs": {
          "nav-highlight": { "from": "highlight-pill", "to": "highlight-pill" }
        }
      }
    },
    "03_architecture": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.5 },
      "morph": {
        "from": "02_features",
        "pairs": {
          "nav-highlight": { "from": "highlight-pill", "to": "highlight-pill" }
        }
      }
    },
    "04_roadmap": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.5 },
      "morph": {
        "from": "03_architecture",
        "pairs": {
          "nav-highlight": { "from": "highlight-pill", "to": "highlight-pill" }
        }
      }
    }
  }
}
```

The converter compiles `nav-highlight` into `!!nav-highlight` in the PowerPoint Selection Pane on each slide, instructing PowerPoint's Morph engine to treat the pill as the identical object across transitions.

## Reproduction & Verification Commands

Specify absolute execution roots using portable placeholder variables:

```powershell
# Set absolute execution roots (replace placeholders with local absolute paths)
$SkillRoot = "/path/to/skills/ppt-master"
$ExampleRoot = "$SkillRoot/examples/morph_persistent_nav"

# 1. Quality check validation
python "$SkillRoot/scripts/svg_quality_checker.py" "$ExampleRoot" --quick-generate --canonical-authoring --stage final --json

# 2. Export native DrawingML presentation
python "$SkillRoot/scripts/svg_to_pptx.py" "$ExampleRoot" --quick-generate --no-notes
```

## Runtime Boundary & Compatibility

- **Canvas**: Exact 16:9 widescreen canvas (`1280x720` px, matching `12,192,000 x 6,858,000` EMU).
- **Editability**: 100% native DrawingML vectors and editable text boxes. No full-slide screenshots, baked bitmaps, or proprietary engine macros.
- **Playback Verification Status**: Representative adjacent, nonadjacent, and return links were manually exercised in WPS Office 12.1.0.29161 on Windows; sampled transition frames retained stationary labels and an independently moving highlight.

Sample content and metrics illustrate the animation layout; they are not product benchmarks.
