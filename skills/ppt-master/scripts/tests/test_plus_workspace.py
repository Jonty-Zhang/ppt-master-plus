"""Plus workspace tidiness: research pairs move into the project, pack sweeps projects/."""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import deliver  # noqa: E402
from project_management import cli as project_cli  # noqa: E402


class ImportFromWorkingFolderTests(unittest.TestCase):
    def test_research_pair_under_working_projects_is_moved(self) -> None:
        # An installed Skill keeps PROJECTS_ROOT inside its own install tree,
        # while init puts projects under the caller's working folder.
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "projects"
            projects.mkdir()
            self.assertNotEqual(projects.resolve(), project_cli.PROJECTS_ROOT.resolve())
            manager = project_cli.ProjectManager(base_dir=projects)
            with contextlib.redirect_stdout(io.StringIO()):
                project = Path(manager.init_project("demo"))
            research = projects / "demo_research.md"
            facts = projects / "demo_research.facts.json"
            research.write_text("# Research\n\nfact\n", encoding="utf-8")
            facts.write_text("{}\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                manager.import_sources(str(project), [str(research), str(facts)])
            self.assertFalse(research.exists())
            self.assertFalse(facts.exists())
            self.assertTrue((project / "sources" / "demo_research.md").is_file())

    def test_user_file_outside_projects_is_copied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "projects"
            projects.mkdir()
            manager = project_cli.ProjectManager(base_dir=projects)
            with contextlib.redirect_stdout(io.StringIO()):
                project = Path(manager.init_project("demo"))
            draft = Path(tmp) / "draft.md"
            draft.write_text("# Draft\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                manager.import_sources(str(project), [str(draft)])
            self.assertTrue(draft.is_file())


class PackSweepTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        project = root / "projects" / "demo_ppt169_20261106"
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_output" / "01_cover.svg").write_text("<svg/>", encoding="utf-8")
        (project / "exports").mkdir()
        (project / "exports" / "demo.pptx").write_bytes(b"pptx")
        return project

    def _pack(self, project: Path) -> str:
        args = argparse.Namespace(project=project, title="演示", pptx=None, dest=None,
                                  no_embed_fonts=True, font_dir=[], keep_workdir=False)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            deliver.pack(args)
        return out.getvalue()

    def test_empty_leftovers_and_projects_folder_are_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._project(root)
            (root / "projects" / "demo_intake" / "draft_files").mkdir(parents=True)
            out = self._pack(project)
            self.assertFalse((root / "projects").exists())
            self.assertIn("empty projects/ folder", out)
            self.assertTrue((root / "演示" / "演示.pptx").is_file())

    def test_remaining_files_are_reported_not_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self._project(root)
            other = root / "projects" / "notes.md"
            other.write_text("keep", encoding="utf-8")
            out = self._pack(project)
            self.assertTrue(other.is_file())
            self.assertIn("projects/ still holds: notes.md", out)


if __name__ == "__main__":
    unittest.main()
