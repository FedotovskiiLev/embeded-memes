# Hamster-only curation and pixel-based restoration — v2.2.0

The site's **classic interface and color scheme are unchanged**. Only catalog content, search data, media assets and provenance were curated.

## Outcome

- Started from **452** canonical records on GitHub; retained **374** in the searchable hamster collection.
- Excluded **78** unrelated images, redundant copies, non-hamster characters, and unsuitable source entries. Exclusion reasons and identifiers are recorded in `provenance/curation_review.json`.
- **13** canonical images were promoted from better-quality duplicate sources, where visual content matched. Superseded aliases remain traceable.
- **15** low-quality or nontransparent originals received a **code-only** restoration: background masks, transparency, selective whitening of hamster fur, preservation of colored objects and costume details, and resampling with Pillow/OpenCV.
- Recognizable hamster cosplays remain tagged with character and franchise references, including Ralsei, Susie, Pikachu, Link, Spider-Man, and others. Uncertain identifications are qualified in the source metadata.
- Regenerated JSON and JSONL catalog, browser data, full-text SQLite catalog, 96-dimensional local LSA search vectors and contact sheets.

## Authenticity and limitations

Restorations are **not AI-generated images**. Source drawings were segmented, recolored and resized programmatically. Upscaling does not create genuinely missing fine details. In some cases, the low resolution of the source imposes a hard quality limit. A restoration is never presented as a high-resolution original.

Edited items have a `restoration` record in `data/source/memes.json`; the browser labels restored images. Original sources are retained under `originals/` for provenance and rollback.

## Reproducibility and checks

The script is `scripts/curate_hamsters.py`. It is idempotent on already curated datasets and is run in `.github/workflows/curate-hamsters.yml`. Search regression tests and catalog validation passed on the curated collection.

For full details, see `provenance/curation_review.json`. This commit also triggers publication of the latest main-branch collection on GitHub Pages.

## v2.2.1 color fidelity correction

**Only the external background is transparent.** Colored characters stay in their original colors (Duo green, Minion and Pikachu yellow, Kris cyan, Susie purple, etc.). The previous forced-white conversion was a mistake. All fifteen edited masters have been recreated from cryptographically verified original RGB with preserved transparent alpha masks; no AI image model was used. See `provenance/palette_correction.json`.
