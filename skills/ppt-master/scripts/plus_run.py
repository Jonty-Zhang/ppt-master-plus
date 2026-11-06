#!/usr/bin/env python3
"""
PPT Master Plus - Run Record and Export Gate

Records the answers to the Plus opening questions and the user's page-copy
confirmation in <project>/plus_run.json, and refuses a Generate export that
lacks them.

Usage:
    python3 ${SKILL_DIR}/scripts/plus_run.py start <project_path> --route generate --answers '<json>'
    python3 ${SKILL_DIR}/scripts/plus_run.py start <project_path> --route image --frames <page images...>
    python3 ${SKILL_DIR}/scripts/plus_run.py confirm-copy <project_path>
    python3 ${SKILL_DIR}/scripts/plus_run.py check <project_path> [--quick-generate]
    python3 ${SKILL_DIR}/scripts/plus_run.py show <project_path>

Notes:
    - The entry (full ppt-master or ppt-master-flash) comes from the path the
      script is called through: ppt-master-flash links its scripts/ to the
      full Skill, and the called path keeps the ppt-master-flash folder name.
    - svg_to_pptx.py calls export_gate() before every export; --roundtrip
      (Edit Native PPTX) is not a Generate export and is never gated.

Dependencies:
    None (only uses the standard library)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
RECORD_NAME = "plus_run.json"
COPY_NAME = "page_copy.md"
FLASH_DIRNAME = "ppt-master-flash"

ROUTES = ("generate", "beautify", "image", "revision")
CHOICES = {
    "start_point": ("designed", "draft", "topic", "pptx-reedit", "pptx-rebuild"),
    "level": ("style",),
    "ai_images": ("yes", "no"),
    "advanced_animation": ("yes", "no"),
}
REQUIRED = {
    "generate": ("start_point", "audience_style", "page_count", "ai_images", "advanced_animation"),
    "beautify": ("level", "audience_style", "ai_images", "advanced_animation"),
}
# start points whose on-slide copy the user has not written page by page
COPY_REQUIRED = ("draft", "topic", "pptx-reedit", "pptx-rebuild")


def _entry() -> str:
    called = Path(sys.argv[0]).absolute()
    return "flash" if FLASH_DIRNAME in called.parts else "full"


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(project: Path) -> dict | None:
    path = project / RECORD_NAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save(project: Path, record: dict) -> None:
    (project / RECORD_NAME).write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def answer_errors(route: str, answers: dict) -> list[str]:
    errors = []
    for key in REQUIRED.get(route, ()):
        value = answers.get(key)
        if value is None or str(value).strip() == "":
            errors.append(f"缺少必问答案 {key}")
        elif key in CHOICES and value not in CHOICES[key]:
            errors.append(f"{key} 只能是 {' / '.join(CHOICES[key])}，收到 {value!r}")
    return errors


def check(project: Path, quick: bool) -> list[str]:
    """Return the reasons this project may not be exported; empty means OK."""
    record = load(project)
    if record is None:
        return [f"项目里没有 {RECORD_NAME}：先问完开工问题并运行 plus_run.py start"]
    route = record.get("route")
    if record.get("entry") == "flash" or route == "revision":
        return []
    if route == "image":
        errors = [] if quick else ["图片转 PPT 用 --quick-generate 导出"]
        frames = record.get("frames") or []
        if not frames or not all((project / f).is_file() for f in frames):
            errors.append("图片转 PPT 的页面原图不在项目里，无法确认这是图片还原项目")
        return errors
    if route not in REQUIRED:
        return [f"{RECORD_NAME} 里的 route 无效：{route!r}"]
    errors = []
    if quick:
        errors.append(
            "完整版 ppt-master 不走 Quick：普通生成和美化按 Default 流程导出；"
            "要快速版请用户自己调用 /ppt-master-flash"
        )
    elif not (project / "spec_lock.md").is_file():
        errors.append("缺少 spec_lock.md：Default 流程的确认和锁定还没完成")
    errors += answer_errors(route, record.get("answers") or {})
    start_point = (record.get("answers") or {}).get("start_point")
    if route == "generate" and start_point in COPY_REQUIRED:
        copy = project / COPY_NAME
        confirmed = record.get("copy_confirmed") or {}
        if not copy.is_file():
            errors.append(f"缺少 {COPY_NAME}：起点是 {start_point}，要先写逐页文案给用户确认")
        elif not confirmed:
            errors.append(f"{COPY_NAME} 还没经用户确认（plus_run.py confirm-copy）")
        elif confirmed.get("sha256") != _sha256(copy):
            errors.append(f"{COPY_NAME} 在用户确认后又改过，要重新给用户确认")
    return errors


def export_gate(argv: list[str]) -> None:
    """Stop svg_to_pptx.py before a Generate export that lacks the Plus records."""
    if "--roundtrip" in argv:
        return
    project = next(
        (Path(a) for a in argv if not a.startswith("-") and (Path(a) / "svg_output").is_dir()),
        None,
    )
    if project is None or SKILL_DIR in project.resolve().parents:
        return  # the Skill's own examples are demos, not user runs
    errors = check(project, "--quick-generate" in argv)
    if errors:
        print("[PLUS] 导出被拒绝：", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        print("  按 workflows/stages/plus-intake.md 补上缺的步骤，不要绕过。", file=sys.stderr)
        raise SystemExit(2)


def cmd_start(args: argparse.Namespace) -> int:
    project = args.project
    if not project.is_dir():
        raise SystemExit(f"project not found: {project}")
    entry = _entry()
    try:
        answers = json.loads(args.answers) if args.answers else {}
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--answers is not valid JSON: {exc}")
    if not isinstance(answers, dict):
        raise SystemExit("--answers must be a JSON object")
    record = {"format": 1, "entry": entry, "route": args.route, "answers": answers,
              "started_at": _now()}
    if args.route == "image":
        frames = []
        for frame in args.frames or []:
            path = Path(frame).resolve()
            try:
                frames.append(str(path.relative_to(project.resolve())))
            except ValueError:
                raise SystemExit(f"frame must be inside the project: {frame}")
            if not path.is_file():
                raise SystemExit(f"frame not found: {frame}")
        if not frames:
            raise SystemExit("--route image needs --frames <page images inside the project>")
        record["frames"] = frames
    elif entry == "full":
        if args.route not in REQUIRED:
            raise SystemExit(f"--route {args.route} is not started by hand")
        errors = answer_errors(args.route, answers)
        if errors:
            raise SystemExit("; ".join(errors))
    previous = load(project)
    if previous and previous.get("copy_confirmed"):
        record["copy_confirmed"] = previous["copy_confirmed"]
    _save(project, record)
    print(f"[PLUS] {RECORD_NAME}: entry={entry} route={args.route}")
    return 0


def cmd_confirm_copy(args: argparse.Namespace) -> int:
    record = load(args.project)
    if record is None:
        raise SystemExit(f"run plus_run.py start first: no {RECORD_NAME}")
    copy = args.project / COPY_NAME
    if not copy.is_file():
        raise SystemExit(f"no {COPY_NAME} in {args.project}")
    record["copy_confirmed"] = {"sha256": _sha256(copy), "at": _now()}
    _save(args.project, record)
    print(f"[PLUS] {COPY_NAME} confirmed")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    errors = check(args.project, args.quick_generate)
    for line in errors:
        print(f"  - {line}")
    print("[PLUS] ok" if not errors else "[PLUS] export would be refused")
    return 1 if errors else 0


def cmd_show(args: argparse.Namespace) -> int:
    record = load(args.project)
    print(json.dumps(record, ensure_ascii=False, indent=2) if record else f"no {RECORD_NAME}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PPT Master Plus run record and export gate")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("start", help="record the opening answers")
    p.add_argument("project", type=Path)
    p.add_argument("--route", choices=ROUTES, required=True)
    p.add_argument("--answers", help="JSON object of the opening answers")
    p.add_argument("--frames", nargs="+", help="page images for --route image")
    p.set_defaults(func=cmd_start)
    p = sub.add_parser("confirm-copy", help="record the user's page-copy confirmation")
    p.add_argument("project", type=Path)
    p.set_defaults(func=cmd_confirm_copy)
    p = sub.add_parser("check", help="report whether an export would pass")
    p.add_argument("project", type=Path)
    p.add_argument("--quick-generate", action="store_true")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("show", help="print the run record")
    p.add_argument("project", type=Path)
    p.set_defaults(func=cmd_show)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
