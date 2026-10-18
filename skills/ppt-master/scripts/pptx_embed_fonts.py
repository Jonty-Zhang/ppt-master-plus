#!/usr/bin/env python3
"""
PPT Master - Local Font Embedding Tool

Embeds every locally installed font a finished PPTX uses into the package, so
the deck renders with its designed faces on a computer that lacks them.

Usage:
    python3 scripts/pptx_embed_fonts.py <deck.pptx>
    python3 scripts/pptx_embed_fonts.py <deck.pptx> -o <out.pptx>
    python3 scripts/pptx_embed_fonts.py <deck.pptx> --dry-run

Dependencies:
    fonttools, lxml (installed with python-pptx)

Notes:
    - The exporter targets Windows: a CJK design face whose name is not in its
      East Asian list lands in the latin slot while ea falls back to a Windows
      face. A run (or theme slot) whose latin face is installed here and covers
      the run's Han characters gets ea/cs retargeted to that face first, so the
      embedded face is the one actually used for Chinese text.
    - Fonts are subset to the characters the deck uses (slides, layouts,
      masters, notes) and CFF outlines are converted to TrueType, the outline
      format PowerPoint loads from embedded font parts.
    - OS/2 fsType is honoured: Restricted and bitmap-only fonts are skipped,
      no-subsetting fonts are embedded whole.
    - Faces present on every Windows and macOS Office install are skipped
      unless --all is given.
    - Embedded fonts are honoured by PowerPoint (Windows / macOS 16.17+);
      Keynote and Google Slides ignore them; WPS support varies by version.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree
import logging

try:
    from fontTools.ttLib import TTCollection, TTFont, newTable
    from fontTools.subset import Options, Subsetter
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
except ImportError:  # pragma: no cover - dependency guard
    print("fonttools is required: pip install fonttools", file=sys.stderr)
    sys.exit(2)


logging.getLogger("fontTools.subset").setLevel(logging.ERROR)

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
FONT_REL_TYPE = R_NS + "/font"
FONT_CONTENT_TYPE = "application/x-fontdata"

# presentation.xml children that must follow p:embeddedFontLst (CT_Presentation order)
_AFTER_EMBEDDED_FONTS = (
    "custShowLst", "photoAlbum", "custDataLst", "kinsoku",
    "defaultTextStyle", "modifyVerifier", "extLst",
)

# Faces shipped with Office on both Windows and macOS: embedding them only adds weight.
UBIQUITOUS_FONTS = frozenset({
    "arial", "arial black", "calibri", "calibri light", "cambria", "cambria math",
    "candara", "consolas", "constantia", "corbel", "courier new", "georgia",
    "impact", "segoe ui", "tahoma", "times new roman", "trebuchet ms", "verdana",
    "microsoft yahei", "simsun", "simhei", "kaiti", "fangsong", "dengxian",
    "symbol", "wingdings", "webdings",
})

_STYLE_TAGS = ("regular", "bold", "italic", "boldItalic")

_SLIDE_PART = re.compile(
    r"^ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters)/[^/]+\.xml$"
)


def _font_dirs(extra: list[str]) -> list[Path]:
    home = Path.home()
    dirs = [Path(d).expanduser() for d in extra]
    if sys.platform == "darwin":
        dirs += [home / "Library/Fonts", Path("/Library/Fonts"),
                 Path("/System/Library/Fonts")]
        dirs += sorted(Path("/System/Library/AssetsV2").glob(
            "com_apple_MobileAsset_Font*/*/AssetData"))
    elif os.name == "nt":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        dirs += [windir / "Fonts"]
        local = os.environ.get("LOCALAPPDATA")
        if local:
            dirs.append(Path(local) / "Microsoft/Windows/Fonts")
    else:
        dirs += [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"),
                 home / ".local/share/fonts", home / ".fonts"]
    return [d for d in dirs if d.is_dir()]


@dataclass
class FontFace:
    path: Path
    index: int  # TTC member index, -1 for a single font file
    style: str  # one of _STYLE_TAGS


def _style_of(font: TTFont) -> str:
    os2 = font["OS/2"] if "OS/2" in font else None
    sel = os2.fsSelection if os2 is not None else 0
    sub = (font["name"].getDebugName(2) or "").lower()
    bold = bool(sel & 0x20) or "bold" in sub
    italic = bool(sel & 0x01) or "italic" in sub or "oblique" in sub
    if bold and italic:
        return "boldItalic"
    return "bold" if bold else ("italic" if italic else "regular")


def index_local_fonts(wanted: set[str], extra_dirs: list[str]) -> dict[str, dict[str, FontFace]]:
    """Map lower-cased family names in ``wanted`` to their installed style files."""
    found: dict[str, dict[str, FontFace]] = {}
    for root in _font_dirs(extra_dirs):
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".ttf", ".otf", ".ttc", ".otc"}:
                continue
            try:
                if path.suffix.lower() in {".ttc", ".otc"}:
                    members = list(enumerate(TTCollection(str(path), lazy=True).fonts))
                else:
                    members = [(-1, TTFont(str(path), lazy=True))]
            except Exception:
                continue
            for index, font in members:
                try:
                    family = font["name"].getDebugName(1) or ""
                    style = _style_of(font)
                except Exception:
                    continue
                key = family.strip().lower()
                if key in wanted:
                    found.setdefault(key, {}).setdefault(style, FontFace(path, index, style))
    return found


def _open_face(face: FontFace) -> TTFont:
    if face.index >= 0:
        return TTFont(str(face.path), fontNumber=face.index)
    return TTFont(str(face.path))


def _covers(face: FontFace, chars: set[str], cache: dict) -> bool:
    key = (face.path, face.index)
    if key not in cache:
        cache[key] = set(_open_face(face).getBestCmap() or {})
    cmap = cache[key]
    return all(ord(ch) in cmap for ch in chars)


def _is_han(ch: str) -> bool:
    cp = ord(ch)
    return 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF or 0x20000 <= cp <= 0x323AF


def _otf_to_ttf(font: TTFont) -> None:
    """Convert CFF outlines to quadratic TrueType glyf in place."""
    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    glyf = newTable("glyf")
    glyf.glyphOrder = glyph_order
    glyf.glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
        glyf.glyphs[name] = pen.glyph()
    font["loca"] = newTable("loca")
    font["glyf"] = glyf
    for tag in ("CFF ", "CFF2", "VORG"):
        if tag in font:
            del font[tag]
    glyf.compile(font)
    hmtx = font["hmtx"]
    for name, glyph in glyf.glyphs.items():
        advance, _ = hmtx[name]
        hmtx[name] = (advance, getattr(glyph, "xMin", 0) if glyph.numberOfContours else 0)
    maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    for attr in ("maxTwilightPoints", "maxStorage", "maxFunctionDefs",
                 "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions",
                 "maxComponentElements"):
        setattr(maxp, attr, 0)
    font["maxp"] = maxp
    maxp.compile(font)
    post = font["post"]
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = glyph_order
    font.sfntVersion = "\x00\x01\x00\x00"


def build_font_payload(face: FontFace, chars: set[str], subset: bool) -> tuple[bytes | None, str]:
    """Return (TrueType bytes, note) or (None, reason) when the face may not be embedded."""
    font = _open_face(face)
    fs_type = font["OS/2"].fsType if "OS/2" in font else 0
    if fs_type & 0x0200:
        return None, "bitmap-only embedding"
    if fs_type & 0x000F == 0x0002:
        return None, "licence forbids embedding (fsType Restricted)"
    note = "read-only (Preview & Print)" if fs_type & 0x0004 else ""
    if subset and fs_type & 0x0100:
        subset = False
        note = (note + "; " if note else "") + "licence forbids subsetting, embedded whole"
    if subset:
        options = Options()
        options.name_IDs = ["*"]
        options.name_languages = ["*"]
        options.name_legacy = True
        options.notdef_outline = True
        options.layout_features = ["*"]
        options.hinting = True
        subsetter = Subsetter(options)
        subsetter.populate(text="".join(sorted(chars | set(" 0123456789"))))
        subsetter.subset(font)
    if "CFF " in font or "CFF2" in font:
        _otf_to_ttf(font)
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue(), note


@dataclass
class Usage:
    chars: set[str] = field(default_factory=set)
    styles: set[str] = field(default_factory=set)


def _theme_fonts(theme_root) -> dict[str, str]:
    fonts = {}
    for kind, prefix in (("majorFont", "+mj"), ("minorFont", "+mn")):
        node = theme_root.find(f".//{{{A_NS}}}{kind}")
        if node is None:
            continue
        for slot, suffix in (("latin", "lt"), ("ea", "ea"), ("cs", "cs")):
            el = node.find(f"{{{A_NS}}}{slot}")
            if el is not None and el.get("typeface"):
                fonts[f"{prefix}-{suffix}"] = el.get("typeface")
    return fonts


def _run_style(rpr) -> str:
    bold = rpr is not None and rpr.get("b") in {"1", "true"}
    italic = rpr is not None and rpr.get("i") in {"1", "true"}
    if bold and italic:
        return "boldItalic"
    return "bold" if bold else ("italic" if italic else "regular")


def embed_fonts(src: Path, dst: Path, *, extra_dirs: list[str], subset: bool,
                include_all: bool, dry_run: bool) -> int:
    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        parts = {n: zin.read(n) for n in names}

    theme_name = next((n for n in sorted(names) if re.match(r"^ppt/theme/theme\d+\.xml$", n)), None)
    theme_root = etree.fromstring(parts[theme_name]) if theme_name else None
    theme = _theme_fonts(theme_root) if theme_root is not None else {}

    trees = {n: etree.fromstring(parts[n]) for n in names if _SLIDE_PART.match(n)}

    # Pass 1: every run's characters per (resolved typeface).
    runs = []  # (rPr element or None, text)
    for root in trees.values():
        for run in root.iter(f"{{{A_NS}}}r", f"{{{A_NS}}}fld"):
            text = "".join(t.text or "" for t in run.iter(f"{{{A_NS}}}t"))
            if text:
                runs.append((run.find(f"{{{A_NS}}}rPr"), text))

    def slot_face(rpr, slot: str) -> str | None:
        el = rpr.find(f"{{{A_NS}}}{slot}") if rpr is not None else None
        face = el.get("typeface") if el is not None else None
        if face is None:
            face = f"+mn-{'lt' if slot == 'latin' else slot}"
        return theme.get(face, face) if face.startswith("+") else face

    wanted = {f.lower() for f in theme.values()}
    for rpr, _ in runs:
        for slot in ("latin", "ea", "cs"):
            face = slot_face(rpr, slot)
            if face:
                wanted.add(face.lower())
    local = index_local_fonts(wanted, extra_dirs)
    cover_cache: dict = {}

    # Pass 2: a CJK design face parked in latin also takes ea/cs.
    retargeted = 0
    for rpr, text in runs:
        han = {ch for ch in text if _is_han(ch)}
        latin_el = rpr.find(f"{{{A_NS}}}latin") if rpr is not None else None
        if not han or latin_el is None:
            continue  # theme-inherited latin is aligned on the theme below
        latin = slot_face(rpr, "latin")
        faces = local.get((latin or "").lower())
        if not faces or not _covers(next(iter(faces.values())), han, cover_cache):
            continue
        previous = latin_el
        for slot in ("ea", "cs"):  # CT_TextCharacterProperties order: latin, ea, cs
            el = rpr.find(f"{{{A_NS}}}{slot}")
            if el is None:
                el = etree.Element(f"{{{A_NS}}}{slot}")
                previous.addnext(el)
            previous = el
            if slot_face(rpr, slot) != latin:
                el.set("typeface", latin)
                retargeted += 1

    theme_changed = False
    if theme_root is not None:
        deck_han = {ch for _, text in runs for ch in text if _is_han(ch)}
        for kind in ("majorFont", "minorFont"):
            node = theme_root.find(f".//{{{A_NS}}}{kind}")
            latin_el = node.find(f"{{{A_NS}}}latin") if node is not None else None
            latin = latin_el.get("typeface") if latin_el is not None else None
            faces = local.get((latin or "").lower())
            if not faces or not deck_han or not _covers(next(iter(faces.values())), deck_han, cover_cache):
                continue
            targets = [node.find(f"{{{A_NS}}}ea")] + [
                f for f in node.findall(f"{{{A_NS}}}font") if f.get("script") in {"Hans", "Hant"}]
            for el in targets:
                if el is not None and el.get("typeface") != latin:
                    el.set("typeface", latin)
                    theme_changed = True
        theme = _theme_fonts(theme_root)

    # Pass 3: final usage per family and style.
    usage: dict[str, Usage] = {}
    display: dict[str, str] = {}
    for rpr, text in runs:
        style = _run_style(rpr)
        for slot in ("latin", "ea", "cs"):
            face = slot_face(rpr, slot)
            if not face:
                continue
            key = face.lower()
            display.setdefault(key, face)
            entry = usage.setdefault(key, Usage())
            entry.chars.update(text)
            entry.styles.add(style)

    pres_name = "ppt/presentation.xml"
    pres = etree.fromstring(parts[pres_name])
    already = set()
    existing = pres.find(f"{{{P_NS}}}embeddedFontLst")
    if existing is not None:
        for el in existing.iter(f"{{{P_NS}}}font"):
            already.add((el.get("typeface") or "").lower())

    embedded, skipped = [], []
    payloads = []  # (family display name, style, bytes, panose, charset)
    for key in sorted(usage):
        name = display[key]
        if key in already:
            skipped.append((name, "already embedded"))
            continue
        if not include_all and key in UBIQUITOUS_FONTS:
            skipped.append((name, "ships with Office on Windows and macOS"))
            continue
        faces = local.get(key)
        if not faces:
            skipped.append((name, "not installed on this computer"))
            continue
        # Regular is always the base face; PowerPoint synthesises styles that have no file.
        for style in _STYLE_TAGS:
            if style != "regular" and style not in usage[key].styles:
                continue
            face = faces.get(style)
            if face is None and style == "regular":
                face = next(iter(faces.values()))
            if face is None:
                continue
            data, note = build_font_payload(face, usage[key].chars, subset)
            if data is None:
                skipped.append((name, note))
                break
            font = TTFont(io.BytesIO(data))
            panose = font["OS/2"].panose
            panose_hex = "".join(f"{getattr(panose, a):02X}" for a in (
                "bFamilyType", "bSerifStyle", "bWeight", "bProportion", "bContrast",
                "bStrokeVariation", "bArmStyle", "bLetterForm", "bMidline", "bXHeight"))
            cjk = any(_is_han(chr(cp)) for cp in (font.getBestCmap() or {}))
            payloads.append((name, style, data, panose_hex, "-122" if cjk else "0", panose))
            embedded.append((name, style, len(data), note))

    by_family: dict[str, dict[str, tuple]] = {}
    for name, style, data, panose_hex, charset, panose in payloads:
        by_family.setdefault(name, {})[style] = (data, panose_hex, charset, panose)

    print(f"[EMBED] {src.name}: retargeted {retargeted} run slot(s) to their CJK design face"
          + ("; theme East Asian font aligned" if theme_changed else ""))
    for name, style, size, note in embedded:
        print(f"  + {name} [{style}] {size / 1024:.0f} KB" + (f" — {note}" if note else ""))
    for name, reason in skipped:
        print(f"  - {name}: {reason}")
    if dry_run:
        return 0

    # Write package parts.
    rels_name = "ppt/_rels/presentation.xml.rels"
    rels = etree.fromstring(parts[rels_name])
    used_ids = {r.get("Id") for r in rels}
    next_id = 1
    font_lst = existing
    if font_lst is None and by_family:
        font_lst = etree.Element(f"{{{P_NS}}}embeddedFontLst")
        anchor = None
        for tag in _AFTER_EMBEDDED_FONTS:
            anchor = pres.find(f"{{{P_NS}}}{tag}")
            if anchor is not None:
                break
        if anchor is not None:
            anchor.addprevious(font_lst)
        else:
            pres.append(font_lst)
    file_no = 1
    new_parts: dict[str, bytes] = {}
    for name, styles in by_family.items():
        first = next(iter(styles.values()))
        holder = etree.SubElement(font_lst, f"{{{P_NS}}}embeddedFont")
        font_el = etree.SubElement(holder, f"{{{P_NS}}}font", typeface=name, panose=first[1])
        family_bits = {3: 0x40, 4: 0x50, 5: 0x50}.get(first[3].bFamilyType,
                                                       0x20 if 11 <= first[3].bSerifStyle <= 13 else 0x10)
        font_el.set("pitchFamily", str(family_bits | 0x02))
        font_el.set("charset", first[2])
        for style in _STYLE_TAGS:
            if style not in styles:
                continue
            while f"rId{next_id}" in used_ids:
                next_id += 1
            rid = f"rId{next_id}"
            used_ids.add(rid)
            while f"ppt/fonts/font{file_no}.fntdata" in parts:
                file_no += 1
            target = f"fonts/font{file_no}.fntdata"
            new_parts[f"ppt/{target}"] = styles[style][0]
            file_no += 1
            etree.SubElement(rels, f"{{{PKG_REL_NS}}}Relationship",
                             Id=rid, Type=FONT_REL_TYPE, Target=target)
            etree.SubElement(holder, f"{{{P_NS}}}{style}").set(f"{{{R_NS}}}id", rid)
    if by_family:
        pres.set("embedTrueTypeFonts", "1")
        pres.set("saveSubsetFonts", "1" if subset else "0")

    ct = etree.fromstring(parts["[Content_Types].xml"])
    if by_family and not any(d.get("Extension", "").lower() == "fntdata"
                             for d in ct.findall(f"{{{CT_NS}}}Default")):
        ct.insert(0, etree.Element(f"{{{CT_NS}}}Default", Extension="fntdata",
                                   ContentType=FONT_CONTENT_TYPE))

    def xml(root) -> bytes:
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    replaced = {n: xml(r) for n, r in trees.items()}
    replaced[pres_name] = xml(pres)
    replaced[rels_name] = xml(rels)
    replaced["[Content_Types].xml"] = xml(ct)
    if theme_name and theme_changed:
        replaced[theme_name] = xml(theme_root)

    fd, tmp = tempfile.mkstemp(suffix=".pptx", dir=str(dst.parent))
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for n in names:
                zout.writestr(n, replaced.get(n, parts[n]))
            for n, data in new_parts.items():
                zout.writestr(n, data)
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print(f"[EMBED] wrote {dst} ({dst.stat().st_size / 1024 / 1024:.1f} MB)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed locally installed fonts into a PPTX.")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="output path (default: in place)")
    parser.add_argument("--font-dir", action="append", default=[], help="extra font directory")
    parser.add_argument("--no-subset", action="store_true", help="embed whole fonts")
    parser.add_argument("--all", action="store_true", help="also embed faces bundled with Office")
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = parser.parse_args()
    if not args.pptx.is_file():
        parser.error(f"not a file: {args.pptx}")
    dst = args.output or args.pptx
    dst.parent.mkdir(parents=True, exist_ok=True)
    return embed_fonts(args.pptx, dst, extra_dirs=args.font_dir, subset=not args.no_subset,
                       include_all=args.all, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
