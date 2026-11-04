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
        ctx = ConvertContext()
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
            ctx = ConvertContext()
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
        ctx = ConvertContext()
        res = convert_element(elem, ctx)
        self.assertIsNotNone(res)
        root = _parse_dml_fragment(res.xml)
        self.assertTrue(root.tag.endswith("grpSp"), "Single-child rotating group must not be flattened to p:sp")


if __name__ == "__main__":
    unittest.main()
