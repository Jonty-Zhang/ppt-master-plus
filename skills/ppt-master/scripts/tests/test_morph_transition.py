#!/usr/bin/env python3
"""Tests for native Morph transition normalization, aliases, pairing validation, and group rotation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if not sys.path or sys.path[0] != str(SCRIPTS_DIR):
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_transitions import (  # noqa: E402
    CANONICAL_TRANSITIONS,
    LEGACY_TRANSITION_KEYS,
    NATIVE_TRANSITION_KEYS,
    NATIVE_TRANSITIONS,
    TRANSITION_ALIASES,
    normalize_transition_effect,
    normalize_transition_effect_request,
)
from svg_to_pptx.animation_config import (  # noqa: E402
    resolve_morph_pairs,
    validate_animation_config,
    validate_transition_config,
)
from svg_to_pptx.drawingml.context import ConvertContext  # noqa: E402
from svg_to_pptx.drawingml.converter import convert_element  # noqa: E402


class TestMorphTransitionNormalization(unittest.TestCase):
    """Verify that smooth and 平滑 aliases normalize to native morph without polluting canonical registry."""

    def test_canonical_transitions_unpolluted(self) -> None:
        """The canonical gallery must retain only the 48 native PowerPoint transitions."""
        self.assertIn("morph", NATIVE_TRANSITION_KEYS)
        self.assertNotIn("smooth", NATIVE_TRANSITION_KEYS)
        self.assertNotIn("平滑", NATIVE_TRANSITION_KEYS)
        self.assertNotIn("smooth", NATIVE_TRANSITIONS)
        self.assertNotIn("平滑", NATIVE_TRANSITIONS)
        self.assertEqual(len(NATIVE_TRANSITION_KEYS), 48)
        self.assertIs(CANONICAL_TRANSITIONS, NATIVE_TRANSITIONS)

    def test_aliases_include_smooth_and_pinghua(self) -> None:
        """TRANSITION_ALIASES and LEGACY_TRANSITION_KEYS must include smooth and 平滑 pointing to morph."""
        self.assertEqual(TRANSITION_ALIASES.get("smooth"), "morph")
        self.assertEqual(TRANSITION_ALIASES.get("平滑"), "morph")
        self.assertIn("smooth", LEGACY_TRANSITION_KEYS)
        self.assertIn("平滑", LEGACY_TRANSITION_KEYS)

    def test_normalize_transition_effect(self) -> None:
        """normalize_transition_effect must normalize morph, smooth, and 平滑 with case insensitivity."""
        self.assertEqual(normalize_transition_effect("morph"), "morph")
        self.assertEqual(normalize_transition_effect("smooth"), "morph")
        self.assertEqual(normalize_transition_effect("Smooth"), "morph")
        self.assertEqual(normalize_transition_effect("SMOOTH"), "morph")
        self.assertEqual(normalize_transition_effect("平滑"), "morph")
        self.assertEqual(normalize_transition_effect("Morph"), "morph")

    def test_normalize_transition_effect_request(self) -> None:
        """normalize_transition_effect_request must return canonical 'morph' and validated options."""
        for alias in ("morph", "smooth", "Smooth", "平滑"):
            effect, options = normalize_transition_effect_request(alias)
            self.assertEqual(effect, "morph")
            self.assertEqual(options, {})

            effect, options = normalize_transition_effect_request(
                alias, {"morph_by": "object"}
            )
            self.assertEqual(effect, "morph")
            self.assertEqual(options, {"morph_by": "object"})

    def test_case_insensitive_aliases_keep_implied_options(self) -> None:
        """An alias must imply the same native options in any letter case."""
        for alias in ("wedge", "wheel", "circle", "diamond", "plus", "strips"):
            self.assertEqual(
                normalize_transition_effect_request(alias.upper()),
                normalize_transition_effect_request(alias),
            )

    def test_explicit_none_is_case_insensitive(self) -> None:
        """Letter case must not change the explicit no-effect input."""
        self.assertIsNone(normalize_transition_effect("NONE"))


class TestMorphPairValidationWithAliases(unittest.TestCase):
    """Verify that pair validation and sidecar validation accept normalized Morph aliases."""

    def test_validate_transition_config_accepts_aliases(self) -> None:
        """validate_transition_config accepts transition effects '平滑' and 'smooth'."""
        config_pinghua = {
            "version": 1,
            "defaults": {"transition": {"effect": "平滑", "duration": 0.8}},
            "slides": {
                "01_intro": {},
                "02_detail": {
                    "transition": {"effect": "平滑", "duration": 0.8},
                    "morph": {
                        "from": "01_intro",
                        "pairs": {"hero": {"from": "hero_1", "to": "hero_2"}},
                    },
                },
            },
        }
        errors = validate_transition_config(config_pinghua)
        self.assertEqual(errors, [])

        config_smooth = {
            "version": 1,
            "slides": {
                "01_intro": {},
                "02_detail": {
                    "transition": {"effect": "smooth", "duration": 0.5},
                    "morph": {
                        "from": "01_intro",
                        "pairs": {"hero": {"from": "hero_1", "to": "hero_2"}},
                    },
                },
            },
        }
        errors = validate_transition_config(config_smooth)
        self.assertEqual(errors, [])

    def test_resolve_morph_pairs_with_aliases(self) -> None:
        """resolve_morph_pairs succeeds when destination declares '平滑' or 'smooth'."""
        config = {
            "version": 1,
            "slides": {
                "01_intro": {},
                "02_detail": {
                    "transition": {"effect": "平滑", "duration": 0.8},
                    "morph": {
                        "from": "01_intro",
                        "pairs": {"hero": {"from": "card_a", "to": "card_b"}},
                    },
                },
            },
        }
        pairs = resolve_morph_pairs(["01_intro", "02_detail"], config)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0].key, "hero")
        self.assertEqual(pairs[0].source_slide, "01_intro")
        self.assertEqual(pairs[0].destination_slide, "02_detail")
        self.assertEqual(pairs[0].shape_name, "!!hero")



_DML_WRAPPER = (
    '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
    '<p:spTree>{xml}</p:spTree>'
    '</p:sld>'
)


def _parse_dml_fragment(xml_fragment: str) -> ET.Element:
    tree = ET.fromstring(_DML_WRAPPER.format(xml=xml_fragment))
    sp_tree = tree.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}spTree")
    return sp_tree[0]


P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
TWO_RECTS = (
    '<rect x="40" y="10" width="20" height="10" fill="#000000"/>'
    '<rect x="60" y="60" width="4" height="4" fill="#000000"/>'
)
# (rot, off x, off y, ext cx, ext cy) in px for TWO_RECTS under
# scale(2) rotate(90 50 50): the rects' centres land on (170, 100) and (76, 124).
SCALED_ROTATED_FRAMES = [
    (5400000, 150, 90, 40, 20),
    (5400000, 72, 120, 8, 8),
]


def _paired_context(elem: ET.Element, group_id: str | None = None) -> ConvertContext:
    return ConvertContext(morph_group_ids=frozenset({group_id or elem.get("id")}))


def _shape_frames(xml_fragment: str) -> list[tuple[int, int, int, int, int]]:
    frames = []
    for sp_pr in _parse_dml_fragment(xml_fragment).iter(f"{P_NS}spPr"):
        xfrm = sp_pr.find(f"{A_NS}xfrm")
        off, ext = xfrm.find(f"{A_NS}off"), xfrm.find(f"{A_NS}ext")
        frames.append((
            int(xfrm.get("rot", "0")),
            round(int(off.get("x")) / 9525),
            round(int(off.get("y")) / 9525),
            round(int(ext.get("cx")) / 9525),
            round(int(ext.get("cy")) / 9525),
        ))
    return frames


class TestGroupRotationPreservation(unittest.TestCase):

    """Verify that pure group rotate transforms are preserved as DrawingML grpSp rot with invariant frames."""

    def test_pure_group_rotate_emits_grpsp_rot(self) -> None:
        """A pure rotate(90 cx cy) must emit p:grpSp with a:xfrm rot='5400000' and pivot-centered frame."""
        svg_xml = (
            '<g id="rotor" data-pptx-bounds="600 200 80 320" transform="rotate(90 640 360)">'
            '  <circle cx="640" cy="360" r="32" fill="#3B82F6"/>'
            '  <path d="M 622 360 L 640 210 L 658 360 Z" fill="#EF4444"/>'
            '  <rect x="632" y="360" width="16" height="80" rx="4" fill="#3B82F6"/>'
            '</g>'
        )
        elem = ET.fromstring(svg_xml)
        ctx = _paired_context(elem)
        res = convert_element(elem, ctx)
        self.assertIsNotNone(res)
        root = _parse_dml_fragment(res.xml)
        self.assertTrue(root.tag.endswith("grpSp"))
        xfrm = root.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm")
        self.assertIsNotNone(xfrm)
        self.assertEqual(xfrm.get("rot"), "5400000")

    def test_group_frame_invariant_across_rotation_angles(self) -> None:
        """Rotating groups with identical local geometry must produce invariant off/ext/chOff/chExt across all angles."""
        template = (
            '<g id="rotor" data-pptx-bounds="600 200 80 320" transform="rotate({angle} 640 360)">'
            '  <circle cx="640" cy="360" r="32" fill="#3B82F6"/>'
            '  <path d="M 622 360 L 640 210 L 658 360 Z" fill="#EF4444"/>'
            '  <rect x="632" y="360" width="16" height="80" rx="4" fill="#3B82F6"/>'
            '</g>'
        )
        frames = []
        for angle in (0, 90, 180, 270):
            elem = ET.fromstring(template.format(angle=angle))
            ctx = _paired_context(elem)
            res = convert_element(elem, ctx)
            self.assertIsNotNone(res)
            root = _parse_dml_fragment(res.xml)
            self.assertTrue(root.tag.endswith("grpSp"))
            xfrm = root.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm")
            self.assertIsNotNone(xfrm)
            off = xfrm.find("{http://schemas.openxmlformats.org/drawingml/2006/main}off")
            ext = xfrm.find("{http://schemas.openxmlformats.org/drawingml/2006/main}ext")
            ch_off = xfrm.find("{http://schemas.openxmlformats.org/drawingml/2006/main}chOff")
            ch_ext = xfrm.find("{http://schemas.openxmlformats.org/drawingml/2006/main}chExt")
            frames.append({
                "angle": angle,
                "rot": xfrm.get("rot"),
                "off": (off.get("x"), off.get("y")),
                "ext": (ext.get("cx"), ext.get("cy")),
                "chOff": (ch_off.get("x"), ch_off.get("y")),
                "chExt": (ch_ext.get("cx"), ch_ext.get("cy")),
            })

        # All frames must have identical off, ext, chOff, chExt
        first = frames[0]
        self.assertIsNone(first["rot"])  # 0 deg rot attribute omitted
        for idx in range(1, 4):
            f = frames[idx]
            self.assertEqual(f["off"], first["off"], f"off mismatch at angle {f['angle']}")
            self.assertEqual(f["ext"], first["ext"], f"ext mismatch at angle {f['angle']}")
            self.assertEqual(f["chOff"], first["chOff"], f"chOff mismatch at angle {f['angle']}")
            self.assertEqual(f["chExt"], first["chExt"], f"chExt mismatch at angle {f['angle']}")
            # ext must be square (cx == cy)
            self.assertEqual(f["ext"][0], f["ext"][1], "ext must be square")

        # Verify exact rot angles
        self.assertEqual(frames[1]["rot"], "5400000")    # 90 deg
        self.assertEqual(frames[2]["rot"], "10800000")   # 180 deg
        self.assertEqual(frames[3]["rot"], "16200000")   # 270 deg

    def test_single_child_rotating_group_not_flattened(self) -> None:
        """A rotating group with a single child must remain p:grpSp even at angle 0 to preserve container parity."""
        svg_xml = (
            '<g id="single-child" transform="rotate(0 640 360)">'
            '  <rect x="632" y="360" width="16" height="80" fill="#3B82F6"/>'
            '</g>'
        )
        elem = ET.fromstring(svg_xml)
        ctx = _paired_context(elem)
        res = convert_element(elem, ctx)
        self.assertIsNotNone(res)
        root = _parse_dml_fragment(res.xml)
        self.assertTrue(root.tag.endswith("grpSp"), "Single-child rotating group must not be flattened to p:sp")

    def test_declared_bounds_keep_frame_invariant_under_counter_rotation(self) -> None:
        """Counter-rotated children must not change the frame when bounds are declared."""
        frames = set()
        for angle in (0, 45, 90, 135, 180):
            elem = ET.fromstring(
                f'<g id="rotor" data-pptx-bounds="320 40 640 640" transform="rotate({angle} 640 360)">'
                '<circle cx="640" cy="360" r="32" fill="#000000"/>'
                f'<rect x="600" y="100" width="160" height="60" fill="#000000" transform="rotate({-angle} 680 130)"/>'
                '</g>'
            )
            res = convert_element(elem, _paired_context(elem))
            xfrm = _parse_dml_fragment(res.xml).find(f"{P_NS}grpSpPr/{A_NS}xfrm")
            frames.add(tuple(
                tuple(sorted(xfrm.find(f"{A_NS}{name}").attrib.items()))
                for name in ("off", "ext", "chOff", "chExt")
            ))
        self.assertEqual(len(frames), 1)

    def test_paired_id_only_applies_at_root(self) -> None:
        """A nested group sharing a paired id must keep its ancestor's projection."""
        elem = ET.fromstring(
            '<g transform="scale(2)"><g id="rotor" transform="rotate(90 50 50)">'
            f'{TWO_RECTS}</g></g>'
        )
        self.assertEqual(
            _shape_frames(convert_element(elem, _paired_context(elem, "rotor")).xml),
            SCALED_ROTATED_FRAMES,
        )


class TestUnpairedRotation(unittest.TestCase):
    """Rotations outside morph.pairs must keep the ordinary export."""

    def test_rotation_under_scaled_ancestor_keeps_position(self) -> None:
        """A rotated group under a scaled ancestor must project through the ancestor."""
        elem = ET.fromstring(
            f'<g transform="scale(2)"><g transform="rotate(90 50 50)">{TWO_RECTS}</g></g>'
        )
        self.assertEqual(
            _shape_frames(convert_element(elem, ConvertContext()).xml),
            SCALED_ROTATED_FRAMES,
        )

    def test_rotation_about_distant_pivot_keeps_content_frame(self) -> None:
        """A bare rotate must not grow the frame out to the origin."""
        elem = ET.fromstring(
            '<g id="badge" transform="rotate(5)">'
            '<rect x="1000" y="600" width="100" height="50" fill="#000000"/>'
            '<rect x="1100" y="600" width="50" height="50" fill="#000000"/>'
            '</g>'
        )
        xfrm = _parse_dml_fragment(convert_element(elem, ConvertContext()).xml).find(
            f"{P_NS}grpSpPr/{A_NS}xfrm"
        )
        self.assertGreater(int(xfrm.find(f"{A_NS}off").get("x")), 0)
        self.assertLess(int(xfrm.find(f"{A_NS}ext").get("cx")), 150 * 9525 * 2)

    def test_single_child_rotation_stays_flat(self) -> None:
        """An unpaired single shape keeps its direct p:sp export."""
        elem = ET.fromstring(
            '<g><g transform="rotate(30 100 100)">'
            '<rect x="50" y="50" width="100" height="100" fill="#000000"/>'
            '</g></g>'
        )
        root = _parse_dml_fragment(convert_element(elem, ConvertContext()).xml)
        self.assertTrue(root.tag.endswith("}sp"))


if __name__ == "__main__":
    unittest.main()
