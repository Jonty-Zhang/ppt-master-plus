# Morph Cover Reveal & Header Handoff Example

A polished 3-slide native PowerPoint (DrawingML) presentation demonstrating the **Cover-to-Content Spatial Transition** (`#R-COV-01`), where a centered hero badge and title recede into a top masthead header bar across scene transitions, followed by a full-width pillar expansion.

## Design Principle: Decoupled Multi-Actor Spatial Continuity

Presentations often suffer from jarring visual disconnects when transitioning from a title cover to the first content slide. When entire groups of mixed typography and shapes are paired together in Morph transitions, text elements stretch or cross-fade abruptly.

This pattern is structured with the **design intent** to maintain spatial continuity using a **decoupled multi-actor architecture**:

1. **Cover-to-Header Masthead Handoff**: On Slide 1 (Cover), the hero badge (`#hero-badge`) is positioned in a dedicated left-aligned track at `x=80` (`80 130 290 52`), horizontally decoupled from the display headline (`#hero-title-block`, $x \ge 390$, fixed at 32px display weight). On Slide 2 (Agenda), `#hero-badge` glides vertically along its constant $x=80$ lane to the top masthead position (`80 36 290 52`) while `#hero-title-block` glides vertically along its parallel track ($x=390$) to the top header zone (`390 32 810 40`). Maintaining strictly non-intersecting motion corridors ensures the badge trajectory never cuts through the headline during forward or reverse interpolation. On Slide 3, this masthead remains anchored at exact coordinates.
2. **Decoupled Carrier Surface (`#pillar-card-1`)**: Pillar 1's pure background frame (`data-pptx-role="decoration"`) expands from a 350px column (`80 130 350 530`) on Slide 2 into a full-width architecture blueprint container (`80 130 1120 530`) on Slide 3. Decoupling the carrier shape prevents child text from being stretched or distorted during vector interpolation.
3. **Atomic Pillar Title Actor (`#pillar-title-1`)**: A single atomic `<text>` element (`Core Engine Stack`) paired directly across slides. Because it contains only this exact string with identical font styling across slides, the design intent is for the presentation runtime to translate the title stably without font glyph re-layout or font collision.
4. **Independent Badge & Caption Actors (`#pillar-badge-1`, `#pillar-caption-1`)**: The numeric badge (`01`) and category caption (`High-Speed Vector Pipeline`) are independently paired groups structured to translate stably alongside the title to their expanded coordinates.
5. **Transient Content Layers (`#pillar-summary-1` vs `#pillar-detail-1`)**: Overview latency metrics on Slide 2 (`#pillar-summary-1`) and deep 3-stage pipeline diagrams on Slide 3 (`#pillar-detail-1`) live in independent page-local groups. Because these groups are un-paired, the design relies on the presentation engine's native in-place cross-fade behavior to transition content rather than scaling old text into enlarged overlapping frames.

## Project Structure

```text
morph_cover_reveal/
├── svg_output/
│   ├── 01_cover.svg           # Slide 1 (Cover: centered badge + title + teaser showcase)
│   ├── 02_agenda.svg          # Slide 2 (Agenda: title recedes to header; 3 pillar cards)
│   └── 03_detail.svg          # Slide 3 (Detail: Pillar 1 expands into architecture view)
├── animations.json            # Deterministic adjacent Morph pairing configuration
├── metadata.json              # Document properties
└── README.md                  # Design pattern and verification documentation
```

## Morph Pairing Configuration

`animations.json` defines deterministic adjacent pairing keys compiled by `svg_to_pptx.py` into OpenXML `p159:morph` tags:

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
    "01_cover": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.6 }
    },
    "02_agenda": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.6 },
      "morph": {
        "from": "01_cover",
        "pairs": {
          "hero-badge-carrier": { "from": "hero-badge", "to": "hero-badge" },
          "hero-title-carrier": { "from": "hero-title-block", "to": "hero-title-block" }
        }
      }
    },
    "03_detail": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.6 },
      "morph": {
        "from": "02_agenda",
        "pairs": {
          "hero-badge-carrier": { "from": "hero-badge", "to": "hero-badge" },
          "hero-title-carrier": { "from": "hero-title-block", "to": "hero-title-block" },
          "pillar-card-1-carrier": { "from": "pillar-card-1", "to": "pillar-card-1" },
          "pillar-title-1-carrier": { "from": "pillar-title-1", "to": "pillar-title-1" },
          "pillar-badge-1-carrier": { "from": "pillar-badge-1", "to": "pillar-badge-1" },
          "pillar-caption-1-carrier": { "from": "pillar-caption-1", "to": "pillar-caption-1" }
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
$ExampleRoot = "$SkillRoot/examples/morph_cover_reveal"

# 1. Quality check validation (zero warnings canonical authoring gate)
python "$SkillRoot/scripts/svg_quality_checker.py" "$ExampleRoot" --quick-generate --canonical-authoring --stage final --json

# 2. Export native DrawingML presentation
python "$SkillRoot/scripts/svg_to_pptx.py" "$ExampleRoot" --quick-generate --no-notes
```

## Runtime Boundary & Compatibility

- **Canvas**: Exact 16:9 widescreen canvas (`1280x720` px, matching `12,192,000 x 6,858,000` EMU).
- **Native Geometry**: 100% native DrawingML vectors and editable text boxes. Zero rasterized full-slide screenshots.
- **Playback Verification Status**: Cover-to-header motion and pillar expansion were manually inspected in WPS Office 12.1.0.29161 on Windows. The corrected cover keeps the badge in a separate left lane; sampled intermediate frames and the destination header were checked.

Sample content and metrics illustrate the animation layout; they are not product benchmarks.
