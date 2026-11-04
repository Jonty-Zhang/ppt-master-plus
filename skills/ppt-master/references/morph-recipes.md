# Advanced Morph Recipes & Continuous Scene Motion

Authoring and pairing guide for multi-slide continuous motion, spatial camera continuity, traveling continuity carriers, and scene choreography in natively editable DrawingML PPTX.

> See [`animations.md`](./animations.md) for baseline transition sidecars and object animation lifecycles; see [`shared-standards-core.md`](./shared-standards-core.md) §4.3 for root-group syntax and off-canvas staging.

---

## 1. Capability Menu & Scene Selector

Morph tweening is authored during slide generation as discrete, visually complete static SVG states across consecutive slides ($P_N \to P_{N+1}$); presentation engines (PowerPoint, WPS) compute the interpolation. Deterministic object matching is governed by explicit sidecar pairing in `animations.json`.

**Trigger**: Activated whenever a presentation plan, section beat, or user request requires cross-page spatial continuity (pan/zoom/drill-down), traveling continuity carriers, progressive state transitions, interactive hub-and-spoke navigation, or multi-step component transformations.

### 1.1 The Five Core Morph Archetypes

| Visual Job / Semantic Goal | Recommended Architecture | Endpoint Construction | Pairing Contract |
|---|---|---|---|
| [**Interactive Hub-and-Spoke / TOC**](../examples/morph_hub_nav/README.md) | Central hub branches to detail spokes and returns | $P_1$: Full navigation hub; $P_2$: Spoke detail with stationary nav labels and moving highlight pill | Chained persistent keys on hub nodes; canonical `<a href="#slide-N">` hyperlinks on buttons |
| [**Persistent Clickable Nav**](../examples/morph_persistent_nav/README.md) | Navigation rail across chapters with moving active marker | $P_N$: Common rail with identical static text labels; highlight shape glides to current index | Stable pair key on highlight pill only; text labels remain independent static chrome |
| [**Cover-to-Content Spatial Handoff**](../examples/morph_cover_reveal/README.md) | Hero title or section card re-seats smoothly into content header | $P_1$: Centered hero headline; $P_2$: Top-left compact masthead headline | Stable pair key on carrier group; keep text string and font-size identical |
| [**Rotating Carousel / True Wheel**](../examples/morph_carousel_wheel/README.md) | Rigid-body angular rotation around a stationary pivot | $P_N$: Rotor group centered on pivot with invariant square frame; angle advances $90^\circ$ per step | Uniform key chained across sequence; `transform="rotate(angle cx cy)"` on group |
| [**Semantic Title & Card Expansion**](../examples/morph_card_expansion/README.md) | Compact card or tile expands to large half-panel or full-page detail | $P_1$: Grid tile with title; $P_2$: Expanded modal/detail card with identical title + evidence body | Stable pair key on expanding card and title; staging marker on exiting neighbors |

### 1.2 Extended Morph Patterns (Candidate Architecture)

Beyond the 5 core implementation archetypes, the following extended choreography patterns share the same underlying container parity and pairing rules:

| Extended Pattern | Visual Behavior | Endpoint Geometry Contract | Technical Boundaries |
|---|---|---|---|
| **Camera Pan / Strip Tracking** | Viewport glides across an oversized horizontal or vertical composite strip | Background carrier shifts $x$ or $y$ across slides while content cards enter/exit view | Carrier must be enclosed in a top-level direct-root `<g id>` if explicitly paired (raw `<rect>` cannot take a sidecar pair key); child items staged off-canvas |
| **Spatial Zoom / Drill-Down** | High-level system diagram zooms into a detailed sub-module | Sub-module bounds expand from micro scale ($w_1, h_1$) to hero scale ($w_2, h_2$); overview dims | Maintain container parity (`grpSp` $\leftrightarrow$ `grpSp`); avoid transforming native chart/table frames |
| **Multi-Plane Parallax** | Foreground cards translate faster than slower-moving background scenery | Foreground layer shifts $\Delta x_1$; background layer shifts $\Delta x_2 < \Delta x_1$ | Separate into distinct root `<g id>` layers; declare independent pair keys per plane |
| **Focal Image Crop Handoff** | Thumbnail crop expands to full-bleed hero photo backdrop | $P_1$: Small picture frame ($320 \times 240$); $P_2$: Full canvas ($1280 \times 720$) | Strict Picture-to-Picture parity (`p:pic` $\leftrightarrow$ `p:pic`); references the same prepared project-local image asset, never an external URL |
| **Before / After Comparison** | State A and State B components expand or contract side-by-side | Left panel contracts from 70% to 30% width; right panel expands from 30% to 70% width | Text containers must maintain aspect ratios to avoid mid-transition line re-wrapping |
| **Progressive Flow Stepper** | Active node status advances sequentially along a connecting pipeline | Connector rail stays static; active node indicator advances to next cardinal position | Keep connecting line static; pair only the moving indicator carrier shape |

### 1.3 Sibling Native Transition Selector (Boundary Matrix)

When the visual job is whole-slide motion rather than object-level transformation, prefer native PPTX transitions over manual Morph authoring:

| Native Transition Key | Visual Characteristic | When to Use Instead of Morph |
|---|---|---|
| `push` / `wipe` | Strict directional slide translation | Sequential timelines or linear section progressions with no continuing elements |
| `pan` / `conveyor` | Viewport camera tracking across uniform slides | Repeating collections where no individual element alters size or internal state |
| `rotate` / `orbit` | Whole-stage pseudo-3D cubic rotation | High-energy section pivots or thematic act boundaries |
| `switch` / `flip` | Two-card visible rotation | Rapid binary state comparisons without internal object tracking |
| `ferris_wheel` | Circular tumbling slide transition | Dynamic collection reviews where whole pages tumble along an orbital arc |
| `zoom` / `box` | Center-out aperture reveal | High-level introductory act reveals without shared object continuity |

---

## 2. Morph Invariants & Technical Mechanics

### 2.1 Object Container Compatibility

Per [`animations.md`](./animations.md) §2.1 and [`pptx-transitions.md`](../scripts/docs/pptx-transitions.md) §3.2, presentation software interpolates only between identical DrawingML container types:

- **Shape to Shape** (`p:sp` $\leftrightarrow$ `p:sp`): Full vector, fill, stroke, and coordinate interpolation.
- **Picture to Picture** (`p:pic` $\leftrightarrow$ `p:pic`): Position, dimension, and crop interpolation.
- **Group to Group** (`p:grpSp` $\leftrightarrow$ `p:grpSp`): Group bounds, rotation, and recursive child interpolation when internal group structures match.
- **Forbidden Pairing Targets**: Native charts and tables (`p:graphicFrame`), structured layout placeholders (`data-pptx-placeholder`), and cross-type pairs (Shape $\leftrightarrow$ Picture) cannot tween smoothly. Pair Slide-local shapes or groups only.

### 2.2 Namespace Disambiguation: SVG ID vs Sidecar Key vs Emitted `!!` Name

Deterministic Morph relies on three distinct namespaces. Do not conflate them:

1. **SVG Group ID**: The authoring identifier on the direct-root group `<g id="card-hero">`. Must be a valid, descriptive XML NCName. Must **never** include the `!!` prefix.
2. **Sidecar Pair Key**: The stable logical identity declared in `animations.json` under `slides.<dest>.morph.pairs.<key>` (e.g. `"hero-card"`). Must be trimmed, non-empty, and written **without** `!!`.
3. **Emitted Selection Pane Name**: Written automatically by the PPTX builder into OOXML (`p:cNvPr@name="!!hero-card"`). The `!!` prefix instructs the presentation engine's Morph solver to force matching regardless of internal shape IDs.

### 2.3 Stationary Labels & Independent Highlight Carriers

**Hard Rule — Separate static labels from moving highlight carriers**:
When animating a tab bar, progress rail, or navigation dock:
- Navigation text labels (`nav-label-1`, `nav-label-2`, etc.) must be authored as **separate, independent shapes or groups** outside the moving highlight shape.
- The highlight pill (`active-pill`) must contain **only the moving colored background shape**.
- In `animations.json`, declare Morph pairing **only for the highlight pill**.
- **Important**: Structural separation alone does not automatically prevent movement. To ensure labels remain visually stationary:
  1. Maintain identical text content, font family, font size, text color/fill, and bounding box coordinates across all participating slides;
  2. Verify that exported shape names (`p:cNvPr@name`) remain consistent;
  3. Validate visual stability through real playback inspection, as differing runtime font metrics or auto-flow can otherwise cause subtle layout shifts.

### 2.4 Fixed-Pivot Rigid Rotation Invariant

To achieve mathematically rigid rotation around a fixed pivot without translation, squashing, or wobble:
1. **Centered Group Frame**: In DrawingML, `<p:grpSp>` rotates around its own bounding box centre. When a group declares `transform="rotate(angle, cx, cy)"`, the DrawingML exporter establishes a pivot-centered, angle-invariant group frame:
   $$\text{ext} = (2r, 2r), \quad \text{off} = (c_x - r, c_y - r)$$
2. **Frame Invariance**: Across consecutive slides ($P_1 \to P_2$), `off`, `ext`, `chOff`, and `chExt` remain identical; only `a:xfrm@rot` changes ($0 \to 5400000 \to 10800000 \to 16200000$).
3. **Unrotated Child Coordinates**: Child shapes inside the rotating group maintain identical local coordinates across all slides.
4. **Counter-Rotation for Upright Content**: If child text or cards must remain upright while orbiting, apply counter-rotation `transform="rotate(-angle, cx_child, cy_child)"` to the child elements.

### 2.5 Text Frame Mechanics & `morph_by` Matching Modes

- **Explicit Pairs Requirement**: When explicit object pairing keys (`morph.pairs`) are declared in `animations.json`, the configuration validator requires `morph_by: object` (mapped to OOXML `option="byObject"`). This guarantees deterministic 1:1 vector matching on named carrier shapes without word-level splitting.
- **Word and Character Morph**: Unpaired or full-slide text transitions continue to support `morph_by: word` (`byWord`) and `morph_by: character` (`byChar`) per [`pptx-transitions.md`](../scripts/docs/pptx-transitions.md) §3.2.
- **Text Stability & Font Sizing**: Prioritize stable font family, font size, and text containers across paired elements. Do **not** assume arbitrary `font-size` differences between text boxes will automatically interpolate smoothly in playback. When text size or content must change across slides, prefer scaling pure vector shape carriers (`<rect>`, icons) while keeping text layers stable or allowing transient text to cross-fade via native dissolve, retaining only native-verified font scaling patterns.
- **Line Wraps**: Maintain consistent aspect ratios on text containers to prevent text from abruptly re-wrapping mid-transition.
- **Trajectory Separation**: When multiple independent actors morph simultaneously across scenes, verify their spatial motion corridors to ensure interpolation trajectories do not cross or cut through adjacent visual elements.

### 2.6 Off-Canvas Staging Protocol

Wholly off-canvas endpoints must follow [`shared-standards-core.md`](./shared-standards-core.md) §4.3:
1. Enclosed in a top-level direct-root `<g id="...">`.
2. Carry valid, space-separated root bounds: `data-pptx-bounds="x y width height"`.
   - `width` and `height` must be strictly positive (`width > 0, height > 0`).
   - `x` and `y` may be negative (e.g. staged off-canvas left $x = -400$ or top $y = -300$) or exceed canvas dimensions (e.g. staged off-canvas right $x \ge 1280$).
3. Include the explicit marker: `data-pptx-morph-staging="true"`. This marker provides a checker overlap exemption for actors waiting outside the slide canvas.

```xml
<!-- Valid Staging Anchor on Slide 1 (Waiting off-canvas right to enter on Slide 2) -->
<g id="incoming-panel" 
   data-pptx-bounds="1320 120 400 500" 
   data-pptx-morph-staging="true">
  <rect x="1320" y="120" width="400" height="500" rx="8" fill="#1E293B" opacity="0.5"/>
  <text x="1340" y="160" font-size="20" fill="#F8FAFC">Incoming Stage</text>
</g>
```

### 2.7 Native Slide Hyperlinks vs Animation Triggers

Per [`native-hyperlinks.md`](./native-hyperlinks.md):
- Slide navigation (e.g. jumping between Hub and Chapter slides) uses canonical SVG hyperlinks:
  `<a href="#slide-N"><g id="...">...</g></a>`
- `trigger_shape` is PowerPoint's / WPS's in-slide `On Click of` animation trigger, **not** slide navigation. Do not confuse in-slide animation triggers with same-deck slide jumps.
- Wrapping a group in `<a href="#slide-N">` preserves the group as the slide's top-level layout unit and animation anchor.

### 2.8 Static Chrome vs Explicit Motion

Per [`animations.md`](./animations.md) §5, groups matching chrome tokens (`bg`, `header`, `footer`, `decor`, `watermark`, `pagenumber`, `nav`, `logo`, bare `rule`) are **default-static** and excluded from automatic builds. However, when an explicit sidecar entry targets a chrome ID (e.g. morphing a header banner or progress rail), the exporter honors it.

---

## 3. Detailed Actionable Specifications for the 5 Core Families

### 3.1 Interactive Hub-and-Spoke / TOC

> Concrete reference example: [`../examples/morph_hub_nav/README.md`](../examples/morph_hub_nav/README.md)

A central overview hub links to multiple spoke slides. Moving between hub and spokes maintains continuous visual anchors and persistent interactive navigation.

```
       [Slide 1: Central Hub]                         [Slide 2: Spoke A Detail]
+-----------------------------------+     +-----------------------------------+
|            [Nav Bar]              |     | [Nav Bar: (A) (B) (C) Return]     |
|                                   |     |                                   |
|   (Spoke A)   (Spoke B) (Spoke C) | ==> | +-------------+  +--------------+ |
|      [O]         [O]       [O]    |     | | (Spoke A)   |  | Detail Body  | |
|                                   |     | | Hero Focus  |  | Spec & Data  | |
|     Click any node to navigate    |     | +-------------+  +--------------+ |
+-----------------------------------+     +-----------------------------------+
```

**Authoring & Flow Rules**:
1. **Adjacency & `morph.from`**:
   - `morph.from` strictly references the immediate predecessor slide ($P_{N-1}$) in the slide deck sequence (e.g. `02_topic1` declares `"from": "01_hub"`).
   - In continuous adjacent sequences (e.g. Slide 1 $\to$ 2 $\to$ 3 $\to$ 4), declare all shared persistent keys (`alpha-carrier`, `beta-carrier`, `active-pill-carrier`) across the entire participating chain.
2. **Non-Adjacent Navigation via Hyperlinks**:
   - Cross-spoke jumps (e.g. clicking directly from Spoke A on Slide 2 to Spoke C on Slide 4) operate via native SVG hyperlinks (`<a href="#slide-4">`), not via direct multi-step `morph.from` declarations.
   - Returning to Slide 1 (Hub) via `<a href="#slide-1">` executes a slide jump. Slide 1 may declare an entry transition effect (e.g. `morph` or `fade`), but does not declare an incoming `morph.pairs` block from non-adjacent spoke slides to avoid conflicting linear chains.
   - Actual visual interpolation across non-adjacent hyperlink jumps depends on runtime presentation player capabilities and must be verified in playback.
3. **`animations.json` Binding Example**:
   ```json
   {
     "slides": {
       "02_topic1": {
         "transition": { "effect": "morph", "duration": 0.8 },
         "morph": {
           "from": "01_hub",
           "pairs": {
             "alpha-carrier": { "from": "card-alpha", "to": "card-alpha" },
             "beta-carrier": { "from": "card-beta", "to": "card-beta" },
             "gamma-carrier": { "from": "card-gamma", "to": "card-gamma" }
           }
         }
       }
     }
   }
   ```
4. **3-Layer Decoupled Architecture (Carrier vs Title vs Detail)**:
   - To avoid body text scaling into oversized distorted characters during card expansion, decouple the container into three distinct layers:
     - **Carrier Group** (`card-alpha`, with `data-pptx-role="decoration"`): Pure background rects and borders. Morph scales this bounding frame cleanly without child coordinate deformation.
     - **Continuous Title Group** (`title-alpha`): Distinct paired group containing only header/title text; translates smoothly into place without font stretching or dual-font collision.
     - **Transient Detail Layer** (`summary-alpha` / `detail-alpha`): Unpaired slide-specific groups. Presentation engines natively cross-fade them cleanly in-place instead of coordinate-stretching old bullets into new text.

---

### 3.2 Persistent Clickable Nav & Moving Active Marker

> Concrete reference example: [`../examples/morph_persistent_nav/README.md`](../examples/morph_persistent_nav/README.md)

A navigation bar sits at the top or side across multiple chapter slides. The labels remain stationary, while a highlight pill glides to the current chapter index.

**Authoring Rules**:
1. **Stationary Text Labels**:
   Each tab label is an independent group with identical coordinates on all slides:
   `<a href="#slide-1"><g id="nav-tab-1" data-pptx-bounds="84 94 176 36">...<text>1. Architecture</text></g></a>`
   `<a href="#slide-2"><g id="nav-tab-2" data-pptx-bounds="268 94 176 36">...<text>2. Performance</text></g></a>`
   `<a href="#slide-3"><g id="nav-tab-3" data-pptx-bounds="452 94 176 36">...<text>3. Security</text></g></a>`
2. **Moving Highlight Pill**:
   `<g id="active-pill" data-pptx-bounds="x 94 176 36">` contains **only** the background `<rect rx="6" fill="#0284C7"/>`.
   - On Slide 1: $x = 84$.
   - On Slide 2: $x = 268$.
   - On Slide 3: $x = 452$.
3. **`animations.json` Sidecar**:
   Declare Morph pairing **only** for `"active-pill-carrier": { "from": "active-pill", "to": "active-pill" }`. Do not pair the text labels.

---

### 3.3 Cover-to-Content Spatial Handoff

> Concrete reference example: [`../examples/morph_cover_reveal/README.md`](../examples/morph_cover_reveal/README.md)

A continuous section title smoothly re-seats from a centered cover hero position into the top masthead header of the following content slide.

**Authoring Rules**:
1. **Slide 1 (Cover / Section Title)**:
   - **Atomic Continuous Headline**: `<g id="headline" data-pptx-bounds="160 280 960 64">` with stable font styling (`font-size="32"`, identical text string).
   - **Independent Metadata**: Badge `<g id="badge">`, kicker/caption `<g id="kicker">`, and subtitle are authored as independent groups outside `headline`.
2. **Slide 2 (Content Slide)**:
   - **Continuous Headline Translates**: `<g id="headline" data-pptx-bounds="80 48 960 64">` with identical font size (`font-size="32"`).
   - **Independent Content Body**: Slide 2 body copy and graphics enter independently and fade into view.
3. **Continuity & Headline Pairing**:
   - Pair **only** the atomic headline: `"title-continuity": { "from": "headline", "to": "headline" }`.
   - **Stationary / Independent Identity**: Keep badge, category tag, and caption as separate groups with their own IDs. Do not pack subtitles or badges inside the headline group.
   - **Single Headline Translation**: While presentation software natively permits font-size changes across slides, authoring identical font metrics and dimensions ($960 \times 64$, `font-size="32"`) across both endpoints is a robust default pattern that ensures purely translational spatial continuity ($x=160, y=280 \to x=80, y=48$). When font-size scaling is required by design, verify intermediate frame behavior in the target presentation player (PowerPoint / WPS), while transient subtitles and content body cross-fade in place.

---

### 3.4 Rotating Carousel / True Wheel Scene Choreography

> Concrete reference example: [`../examples/morph_carousel_wheel/README.md`](../examples/morph_carousel_wheel/README.md)

Simulating a rotating dial, stage wheel, or cyclic carousel where an asymmetric pointer or multi-card rotor rotates rigidly around a fixed pivot point.

**Authoring Rules**:
1. **Rotor Group Centering**:
   Enclose the rotating assembly in a square frame centered on pivot $(c_x, c_y)$:
   `<g id="rotor-assembly" data-pptx-bounds="480 200 320 320" transform="rotate(angle 640 360)">`
2. **Angular Sequence**:
   - Slide 1: `rotate(0 640 360)`
   - Slide 2: `rotate(90 640 360)`
   - Slide 3: `rotate(180 640 360)`
   - Slide 4: `rotate(270 640 360)`
   - Slide 5: `rotate(0 640 360)` (with forward loop button back to Slide 2).
3. **Rotor Pairing**:
   Pair `"rotor-carrier": { "from": "rotor-assembly", "to": "rotor-assembly" }` chained across all slides.

---

### 3.5 Semantic Title & Card Expansion

> Concrete reference example: [`../examples/morph_card_expansion/README.md`](../examples/morph_card_expansion/README.md)

A compact card in a multi-card overview expands to a large detail modal or full-page view, while neighboring cards push away or fade into staging.

**Authoring & Return Bridge Rules**:
1. **Slide 1 (Overview Grid)**:
   Four compact cards in a grid: `card-alpha` ($x=80, y=160, w=540, h=240$).
2. **Slide 2 (Detail Expansion)**:
   `card-alpha` expands to hero dimensions: $x=80, y=140, w=1120, h=520$.
   Cards beta, gamma, delta shift into off-canvas staging with `opacity="0"` and `data-pptx-morph-staging="true"`.
3. **Return Bridge Options**:
   - **Direct Return**: Close button links directly back to Slide 1 (`<a href="#slide-1"><g id="btn-close">...</g></a>`).
   - **Sequence Return Bridge (Slide 3)**: Close button advances to Slide 3 (`03_return_overview.svg`), which re-establishes the full grid overview via paired Morph transition (`card-alpha` shrinks back to compact tile), and offers re-open links (`#slide-2`) to detail cards. Both patterns are valid; choose based on whether linear presentation flow or direct jump is preferred.
4. **Text Decoupling for Clean Expansion**:
   - When a card expands significantly (e.g. from compact tile to hero view), avoid enclosing dense body text directly inside the expanding group carrier. Group scaling stretches child coordinates, resulting in distorted intermediate text.
   - Author as atomic decoupled layers:
     - Pure carrier frame (`card-alpha`, with `data-pptx-role="decoration"`) that scales smoothly.
     - Single continuous headline (`title-alpha`) that translates cleanly without coordinate deformation.
     - Stable metadata elements (`badge-alpha`, `caption-alpha`) as independent actors that can each be paired separately (e.g. `"badge-carrier"`).
     - Transient content body (`summary-alpha` / `detail-alpha`) left unpaired to natively cross-fade in place.

---

## 4. Phase Workflow & Decision Ownership

```
+-----------------------------------------------------------------------------------+
| PLAN PHASE (Step 4 - Strategist / Plan Core)                                      |
| - Identifies cross-slide continuity needs from brief or user instructions.        |
| - Allocates consecutive slide slots (P_N and P_N+1).                              |
| - Records proposed continuity roles in design_spec.md §IX:                        |
|   "Motion suggestion: Morph (hub spoke A from P01 to P02; key: alpha-carrier)"    |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| DO PHASE (Step 6 - Executor / SVG Authoring)                                      |
| - Authors visually complete static SVGs for both slides.                          |
| - Enforces stationary nav text labels; isolates moving highlight into active-pill.|
| - Centers rotating groups on the pivot to maintain frame invariance.              |
| - Marks wholly off-canvas actors with data-pptx-morph-staging="true".             |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| POST-PROCESSING (Step 7 - Customize Animations Stage)                             |
| - Runs `animation_config.py list-groups` to inspect finalized anchor IDs.         |
| - Authors animations.json sidecar: declares transition effect "morph".            |
| - Maps source and destination IDs into `morph.pairs.<key>`.                       |
| - Preflight validator checks adjacency and container compatibility.               |
+-----------------------------------------------------------------------------------+
```

---

## 5. Anti-Patterns & Failure Boundaries

| Anti-Pattern | Root Mechanism | Failure Symptom | Mandatory Prevention |
|---|---|---|---|
| **Text Inside Moving Pill** | Packing text label inside `active-pill` | Text travels and cross-fades across the navigation bar | Author text as independent static shapes; pair only the background rect |
| **Off-Pivot Ink Bounds** | Rotating group with non-centered ink bounds | Group frame shifts position; pointer squashes and deforms | Center rotating group frame on pivot; use invariant square frame |
| **Cross-Container Pair** | Attempting to morph Shape (`p:sp`) into Picture (`p:pic`) | Abrupt 50% cross-fade; no vector interpolation | Maintain strict container parity (`sp <-> sp`, `grpSp <-> grpSp`) |
| **GraphicFrame Target** | Attempting to morph native charts or tables | Exporter rejects pairing at preflight | Pair slide-local shapes or cards; leave chart frames static |
| **Undeclared Adjacent Key** | Reusing a `!!` name on an adjacent Morph edge without declaring it | Exporter rejects undeclared adjacent key collision | Declare every shared key in the destination's `morph.pairs` block |
| **Single-Child Flattening** | Unrotated group at $0^\circ$ flattening to `p:sp` | OOXML container type mismatch (`sp` vs `grpSp`) | Ensure rotating group retains `rotate_pivot` to suppress flattening |

---

## 6. Official Source Citations & References

1. **Microsoft Support**: *Morph transition: Tips and tricks*  
   `https://support.microsoft.com/en-us/powerpoint/morph-transition-tips-and-tricks`  
   *(Official documentation for the `!!` object-matching naming convention, container compatibility, and off-canvas slide-in mechanics).*
2. **Microsoft Support**: *Use the Morph transition in PowerPoint*  
   `https://support.microsoft.com/en-gb/powerpoint/training/use-the-morph-transition-in-powerpoint`  
   *(Official documentation for Morph by Object, Word, and Character transitions and duration settings).*
3. **Repository Enforced Rules**:  
   - Container parity: [`scripts/docs/pptx-transitions.md`](../scripts/docs/pptx-transitions.md) §3.2.  
   - Sidecar syntax & pairing schema: [`scripts/docs/pptx-animations.md`](../scripts/docs/pptx-animations.md) §2.  
   - Canonical hyperlinks: [`references/native-hyperlinks.md`](./native-hyperlinks.md) §2.  
   - Off-canvas staging: [`references/shared-standards-core.md`](./shared-standards-core.md) §4.3.
