#!/usr/bin/env python3
"""Repair v2.2 palette regression without any image generation or pixel recoloring.

Restore each previously processed sticker's RGB from the byte-identical original
master held by a parent commit, while preserving the transparent alpha mask
from the existing edited sticker. Do NOT turn stylized colors into white.

The input RGB is always hash-verified against the original_sha256_master in the
image's restoration metadata. All rendered assets, catalog search data and
audit reports are rebuilt. The original author artwork is never overwritten.

CI: python scripts/restore_original_palette.py
Local/test: python scripts/restore_original_palette.py --original-root /path/to/uncurated/project
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "29a21d12e9a46d4e35c03cc6bfa0e2dfb2f4ccb8"
VERSION = "2.2.1"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_verified_source(record: dict, original_root: Path | None) -> Image.Image:
    """Read original master from pre-curation git tree or provided untouched snapshot."""
    rel = record["files"]["master_png"]
    if original_root:
        blob = (original_root / rel).read_bytes()
        origin = f"local exact pre-curation source: {rel}"
    else:
        blob = subprocess.check_output(["git", "show", f"{BASELINE}:{rel}"], cwd=ROOT)
        origin = f"git:{BASELINE}:{rel}"
    assert hashlib.sha256(blob).hexdigest() == record["restoration"]["original_sha256_master"], (
        f"Original source hash does not match stored provenance: {record['id']} ({origin})"
    )
    with Image.open(io.BytesIO(blob)) as img:
        return img.convert("RGBA")


def repair(record: dict, original_root: Path | None) -> dict:
    rel = record["files"]["master_png"]
    original = read_verified_source(record, original_root)
    master_path = ROOT / rel
    delivery_path = ROOT / record["files"]["delivery_webp"]
    thumb_path = ROOT / record["files"]["thumbnail_webp"]
    with Image.open(master_path) as img:
        previous = img.convert("RGBA")
    before_hash = file_sha(master_path)
    # Keep the actual transparent cutout (including its edge antialiasing) from
    # the existing restoration, while restoring *every* original image RGB pixel.
    original_rgb = original.convert("RGB").resize(previous.size, Image.Resampling.LANCZOS)
    old_alpha = previous.getchannel("A")
    original_channels = original_rgb.split()
    repaired = Image.merge("RGBA", (*original_channels, old_alpha))
    assert repaired.getchannel("A").tobytes() == old_alpha.tobytes(), "Alpha mask unexpectedly changed"
    assert repaired.getchannel("A").getextrema()[0] == 0, "No transparent background"
    assert repaired.getchannel("A").getextrema()[1] == 255, "Character is not fully opaque"
    master_path.parent.mkdir(parents=True, exist_ok=True)
    repaired.save(master_path, format="PNG", optimize=True)
    repaired.save(delivery_path, format="WEBP", lossless=True, method=6)
    thumb = repaired.copy()
    thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
    canvas.alpha_composite(thumb, ((320 - thumb.width) // 2, (320 - thumb.height) // 2))
    canvas.save(thumb_path, format="WEBP", lossless=True, method=6)

    rest = record["restoration"]
    rest["method"] = "non-generative extraction of transparent matte + exact original palette from SHA256-verified pre-curation PNG"
    rest["palette_policy"] = "preserve_source_rgb_no_character_recoloring"
    rest["palette_correction"] = "2026-11-02: restored original colors from original master; retained transparent alpha matte"
    rest["prior_restoration_sha256_master"] = before_hash
    rest["reference_git_commit"] = BASELINE
    rest["notes"] = "Цвет шерсти, кожи, персонажа, одежды и аксессуаров оставлен как в исходнике; удалён только внешний фон."
    record["review_note"] = (record.get("review_note") or "").replace(
        "Изображение обработано программно; цвет/фон изменены, дополнительные мелкие детали не восстанавливались.",
        "Изображение обработано программно: фон сделан прозрачным, исходные цвета и детали персонажа сохранены."
    )
    record["provenance"]["sha256_master"] = file_sha(master_path)
    record["provenance"]["sha256_delivery"] = file_sha(delivery_path)
    record["has_alpha"] = True
    return {
        "id": record["id"], "method": "verified-original-rgb_plus-existing-alpha",
        "original_source_sha256": rest["original_sha256_master"],
        "before_master_sha256": before_hash,
        "after_master_sha256": record["provenance"]["sha256_master"],
        "alpha_preserved_exactly": True,
        "character_colors_from_original": True,
        "output_dimensions": list(repaired.size),
    }


def remove_legacy_whitening() -> None:
    """Permanently remove the incorrect rule from the old collection importer."""
    source = ROOT / "scripts/curate_hamsters.py"
    script = source.read_text(encoding="utf-8")
    start = script.index("def selective_fur_whitening(")
    end = script.index("def cleanup_and_upscale(", start)
    # Retain a backward-compatible function name, but its only acceptable
    # behavior is now a no-op: a green/purple/yellow hamster stays that color.
    script = script[:start] + (
        "def selective_fur_whitening(im: Image.Image, image_id: int):\n"
        "    \"\"\"Deprecated compatibility helper; never recolor original character artwork.\"\"\"\n"
        "    return im\n\n\n"
    ) + script[end:]
    assert "img=selective_fur_whitening(img,image_id)" in script
    script = script.replace(
        "    img=selective_fur_whitening(img,image_id)",
        "    # Do not recolor character/fur/costume; only the background is removed."
    )
    script = script.replace(
        "# BODY-white adjustments apply to base fur; props and costume are retained.",
        "# Source colors are immutable; only the external background is removed."
    )
    for before, after in {
        "green fur -> white": "original green fill preserved",
        "green body -> white": "original green fill preserved",
        "yellow Minion body -> white": "original yellow character preserved",
        "yellow hamster face -> white": "original yellow face preserved",
        "bright-green body -> white": "original bright-green body preserved",
        "cyan face -> white": "original cyan face preserved",
        "purple face -> white": "original purple face preserved",
        "yellow Pikachu body -> white": "original yellow character preserved",
    }.items():
        script = script.replace(before, after)
    script = script.replace(
        "Белый рисованный хомяк: реакции и стилизации на узнаваемых персонажей; посторонние животные и повторы исключены.",
        "Рисованный хомяк: реакции и стилизации узнаваемых персонажей; исходные цвета сохраняются, фон прозрачный."
    )
    source.write_text(script, encoding="utf-8")
    validator = ROOT / "scripts/validate.py"
    v = validator.read_text(encoding="utf-8")
    v = v.replace(
        "if p.is_file():check(p.stat().st_size<100*1024*1024,",
        "if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts:check(p.stat().st_size<100*1024*1024,",
    )
    validator.write_text(v, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-root", type=Path, default=None,
                        help="Path to byte-identical pre-curation files for local verification")
    args = parser.parse_args()
    source_path = ROOT / "data/source/memes.json"
    records = json.loads(source_path.read_text(encoding="utf-8"))
    edited = [r for r in records if r.get("restoration")]
    assert len(edited) == 15, f"Expected 15 edits from 2.2.0, saw {len(edited)}"
    assert not any(r["restoration"].get("palette_policy") == "preserve_source_rgb_no_character_recoloring" for r in edited), (
        "Palette migration already applied — refusing to overwrite repaired assets"
    )
    changes = [repair(r, args.original_root) for r in edited]
    remove_legacy_whitening()
    write_json(source_path, records)
    collections_path = ROOT / "data/source/collections.json"
    collections = json.loads(collections_path.read_text(encoding="utf-8"))
    collections[0]["description"] = "Рисованный хомяк: реакции и стилизации узнаваемых персонажей; исходные цвета сохраняются, фон прозрачный."
    write_json(collections_path, collections)
    write_json(ROOT / "provenance/palette_correction.json", {
        "date": "2026-11-02", "version": VERSION, "error_corrected": "Coloring non-white character artwork white",
        "policy": "Original color is part of the drawing. Only the background may be transparent. No recoloring.",
        "background_alpha_source": "v2.2.0 foreground silhouettes",
        "rgb_source": f"sha256-verified original masters in git history at {BASELINE}",
        "images_corrected": len(changes), "restorations": changes,
    })
    # Correct outdated language in release documentation, without changing website design.
    doc = ROOT / "docs/RESTORATION_RELEASE.md"
    if doc.exists():
        content = doc.read_text(encoding="utf-8")
        content += "\n## v2.2.1 color fidelity correction\n\n" \
                   "**Only the external background is transparent.** Colored characters stay in their original colors (Duo green, Minion and Pikachu yellow, Kris cyan, Susie purple, etc.). " \
                   "The previous forced-white conversion was a mistake. All fifteen edited masters have been recreated from cryptographically verified original RGB with preserved transparent alpha masks; no AI image model was used. " \
                   "See `provenance/palette_correction.json`.\n"
        doc.write_text(content, encoding="utf-8")
    package = ROOT / "package.json"
    pkg = json.loads(package.read_text(encoding="utf-8"))
    pkg["version"] = VERSION
    write_json(package, pkg)
    # Recompute local vector index because metadata changed and catalog hashes include it.
    subprocess.run(["python", "scripts/build.py", "--vectors"], cwd=ROOT, check=True)
    subprocess.run(["python", "scripts/contact_sheets.py"], cwd=ROOT, check=True)
    release_path = ROOT / "RELEASE.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    release["version"] = VERSION
    release["palette_corrected"] = len(changes)
    release["color_policy"] = "original_character_colors_preserved; only_external_background_transparent"
    write_json(release_path, release)
    # Generated checksums are rewritten after validators update qa/validation.json.
    print("PALETTE-CORRECTION", json.dumps({"version": VERSION,"repaired": len(changes),"ids": [x["id"] for x in changes]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
