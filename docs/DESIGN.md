# Visual identity — ORANGE TAPE

The reference for this edition was an orange, black and grey cut-paper collage supplied by the project owner. Its artwork is **not** redistributed or reproduced in this repository. The site uses an independently built palette and shape language.

| Token | Colour | Use |
| --- | --- | --- |
| `--orange` | `#F19446` | Primary brand orange; hero, active nav, CTAs |
| `--ink` | `#1B1B1C` | Primary typography, dark sidebar, borders |
| `--paper` | `#F4F1ED` | Main surface and dialog background |
| `--concrete` | `#C5C3C3` | Supporting grey, non-semantic details |
| `--mist` | `#E0DEDF` | Preview backing and quiet surfaces |
| `--cream` | `#FFF3E5` | Warm surface accents |
| `--rust` | `#8C400C` | Accessible dark orange on light surfaces |

## Rules

- **Orange carries the brand; black carries the text.** Avoid white text on the primary orange because contrast is insufficient for small text.
- Keep the interface usable without any external images or fonts. The design is inspired by the mood and palette of the supplied art, not a copy of its imagery.
- Editorial, slightly industrial feel: square labels, strong borders, a rotated dark tape label, restrained corners; avoid visual noise around actual memes.
- Memes are data, not background decoration. Display full image in previews with `object-fit: contain`.
- Maintain visible keyboard focus, mobile layout and reduced-motion support.

The basic look is implemented in `src/style.css` under `GLIWY / ORANGE TAPE theme`.
