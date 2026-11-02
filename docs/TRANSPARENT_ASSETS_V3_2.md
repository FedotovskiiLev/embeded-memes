# Transparent production assets · v3.2.0

**Embeded Memes by Gliwy.dev** provides transparent background cutouts for all 374 curated hamster images.

## What changed

- 359 new images received a transparent cutout mask using deterministic Pillow, NumPy, SciPy and OpenCV processing.
- The previous 15 approved, color-faithful restorations were kept byte-for-byte untouched.
- Each canonical record now exposes an alpha-enabled PNG master and a lossless WebP delivery image.
- All 374 nuanced individual descriptions, cultural context, stable IDs, search index, original artwork colors, and site theme are preserved.
- The detailed processing history is stored in `provenance/mass_transparent_restoration.json`, including before/after SHA-256 hashes.
- Intricate cases have guided masks: `HAMPTER_0071`, `HAMPTER_0094`, `HAMPTER_0104` and `HAMPTER_0431`.

## Using these in video editing

Use `media/masters/*.png` for compositing in Premiere, DaVinci Resolve, Final Cut, Kdenlive, or any editor that supports transparent PNG. The `media/webp/` files are lossless and alpha-enabled, but check your editor's WebP support. The `originals/` directory is intentionally unchanged.

**Important:** PNG transparency is an alpha channel; pixels of the hamster and its accessories retain their original colors. Resizing low-resolution originals does not create missing detail. Masks were checked through contact sheets and automated validation, but not every fine edge has received individual human approval. Do not treat this as a license to redistribute the original artwork commercially; see `SOURCES_AND_RIGHTS.md`.

## Rebuilding and validation

```bash
python -m pip install -r requirements.txt opencv-python-headless
python scripts/restore_all_transparent.py
python scripts/build.py --vectors
python scripts/contact_sheets.py
python scripts/validate.py
node --test tests/*.test.cjs
```

The restoration script is idempotent when all 374 assets are already restored. The GitHub Actions workflow `.github/workflows/restore-all-transparent.yml` checks complete alpha ranges, catalog links, and search regressions.
