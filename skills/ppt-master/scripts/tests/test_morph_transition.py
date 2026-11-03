#!/usr/bin/env python3
"""Tests for native Morph transition normalization, aliases, and pairing validation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
