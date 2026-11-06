"""Plus run record and export gate (plus_run.py, svg_to_pptx.py wrapper)."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import deliver  # noqa: E402
import plus_run  # noqa: E402

ANSWERS = {
    "start_point": "topic",
    "audience_style": "课堂汇报，复古报纸风",
    "page_count": "8-10",
    "ai_images": "yes",
    "advanced_animation": "no",
}


def _run(script_dir: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script_dir / "plus_run.py"), *args],
        capture_output=True, text=True,
    )


class PlusRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.project = self.root / "projects" / "demo_ppt169_20261106"
        (self.project / "svg_output").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _start(self, *extra: str, script_dir: Path = SCRIPTS) -> subprocess.CompletedProcess:
        return _run(script_dir, "start", str(self.project), *extra)

    def _lock(self) -> None:
        (self.project / "spec_lock.md").write_text("lock", encoding="utf-8")

    def test_export_without_record_is_refused(self) -> None:
        errors = plus_run.check(self.project, quick=False)
        self.assertTrue(any("plus_run.json" in e for e in errors))

    def test_start_rejects_missing_answers_in_full_skill(self) -> None:
        result = self._start("--route", "generate", "--answers", json.dumps({"start_point": "topic"}))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("audience_style", result.stderr)

    def test_full_generate_needs_lock_and_confirmed_copy(self) -> None:
        self.assertEqual(self._start("--route", "generate", "--answers", json.dumps(ANSWERS)).returncode, 0)
        errors = plus_run.check(self.project, quick=False)
        self.assertTrue(any("spec_lock.md" in e for e in errors))
        self.assertTrue(any("page_copy.md" in e for e in errors))

        self._lock()
        copy = self.project / "page_copy.md"
        copy.write_text("# P01\n标题", encoding="utf-8")
        self.assertTrue(any("确认" in e for e in plus_run.check(self.project, quick=False)))

        self.assertEqual(_run(SCRIPTS, "confirm-copy", str(self.project)).returncode, 0)
        self.assertEqual(plus_run.check(self.project, quick=False), [])

        copy.write_text("# P01\n改过的标题", encoding="utf-8")
        self.assertTrue(any("又改过" in e for e in plus_run.check(self.project, quick=False)))

    def test_designed_start_point_needs_no_page_copy(self) -> None:
        answers = dict(ANSWERS, start_point="designed")
        self._start("--route", "generate", "--answers", json.dumps(answers))
        self._lock()
        self.assertEqual(plus_run.check(self.project, quick=False), [])

    def test_full_skill_refuses_quick_export(self) -> None:
        answers = dict(ANSWERS, start_point="designed")
        self._start("--route", "generate", "--answers", json.dumps(answers))
        self._lock()
        errors = plus_run.check(self.project, quick=True)
        self.assertTrue(any("ppt-master-flash" in e for e in errors))

    def test_restart_keeps_copy_confirmation(self) -> None:
        self._start("--route", "generate", "--answers", json.dumps(ANSWERS))
        (self.project / "page_copy.md").write_text("文案", encoding="utf-8")
        _run(SCRIPTS, "confirm-copy", str(self.project))
        self._start("--route", "generate", "--answers", json.dumps(dict(ANSWERS, page_count="12")))
        self.assertIn("copy_confirmed", plus_run.load(self.project))

    def test_beautify_style_level(self) -> None:
        answers = {"level": "style", "audience_style": "沿用原风格",
                   "ai_images": "no", "advanced_animation": "no"}
        self.assertEqual(self._start("--route", "beautify", "--answers", json.dumps(answers)).returncode, 0)
        self._lock()
        self.assertEqual(plus_run.check(self.project, quick=False), [])

    def test_image_route_needs_frames_inside_project(self) -> None:
        self.assertNotEqual(self._start("--route", "image").returncode, 0)
        frame = self.project / "images" / "page_01.png"
        frame.parent.mkdir()
        frame.write_bytes(b"png")
        self.assertEqual(self._start("--route", "image", "--frames", str(frame)).returncode, 0)
        self.assertEqual(plus_run.check(self.project, quick=True), [])
        frame.unlink()
        self.assertTrue(plus_run.check(self.project, quick=True))

    def test_flash_entry_comes_from_the_called_path(self) -> None:
        flash = self.root / "skills" / "ppt-master-flash"
        flash.mkdir(parents=True)
        os.symlink(SCRIPTS, flash / "scripts")
        result = self._start("--route", "generate", script_dir=flash / "scripts")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(plus_run.load(self.project)["entry"], "flash")
        self.assertEqual(plus_run.check(self.project, quick=True), [])

    def test_export_gate_skips_roundtrip_and_blocks_generate(self) -> None:
        plus_run.export_gate([str(self.project), "--roundtrip"])
        with self.assertRaises(SystemExit):
            plus_run.export_gate([str(self.project), "--quick-generate"])

    def _pack_and_unpack(self) -> Path:
        (self.project / "svg_output" / "01_cover.svg").write_text("<svg/>", encoding="utf-8")
        (self.project / "exports").mkdir()
        (self.project / "exports" / "demo.pptx").write_bytes(b"pptx")
        quiet = contextlib.redirect_stdout(io.StringIO())
        with quiet:
            deliver.pack(argparse.Namespace(
                project=self.project, title="演示", pptx=None, dest=None,
                no_embed_fonts=True, font_dir=[], keep_workdir=False))
            deliver.unpack(argparse.Namespace(delivery=self.root / "演示", projects_dir=None))
        return self.project

    def test_unpack_of_an_older_delivery_records_a_revision(self) -> None:
        project = self._pack_and_unpack()
        self.assertEqual(plus_run.load(project)["route"], "revision")
        self.assertEqual(plus_run.check(project, quick=False), [])

    def test_run_record_and_page_copy_travel_with_the_delivery(self) -> None:
        self._start("--route", "generate", "--answers", json.dumps(ANSWERS))
        (self.project / "page_copy.md").write_text("文案", encoding="utf-8")
        _run(SCRIPTS, "confirm-copy", str(self.project))
        self._lock()
        project = self._pack_and_unpack()
        self.assertTrue((self.root / "演示" / "制作文件" / "设计规范" / "page_copy.md").is_file())
        self.assertEqual(plus_run.load(project)["route"], "generate")
        self.assertEqual(plus_run.check(project, quick=False), [])

    def test_svg_to_pptx_wrapper_runs_the_gate(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "svg_to_pptx.py"), str(self.project)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("[PLUS]", result.stderr)


if __name__ == "__main__":
    unittest.main()
