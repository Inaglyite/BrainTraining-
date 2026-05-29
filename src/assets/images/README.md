Project image assets

Place project images in this folder: src/assets/images

Recommended formats:
- PNG: lossless, good for UI icons with opaque backgrounds.
- SVG: preferred for icons and logos (scalable, small file size).
- WEBP / JPG: photos or large bitmaps (use WEBP when supported for smaller size).

Naming conventions:
- lowercase, use kebab-case: `game-suan-shi.png`, `avatar-user-1.webp`, `tile-icon-rps.svg`
- include semantic prefixes where useful: `tile-`, `hero-`, `avatar-`, `icon-`

Suggested sizes:
- App icons / tile icons: 56x56 (PNG) or SVG
- Hero / banner images: 1200x400 (WEBP/JPG)
- Camera overlay icons: 28x28 (SVG preferred)

Usage examples (import in code):
- Import an SVG: `import TileIcon from '../assets/images/tile-icon.svg'`
- Import a PNG/WEBP: `import Hero from '../assets/images/hero.webp'`

Notes:
- Prefer SVG for UI icons so they scale crisply at different resolutions.
- Keep file sizes small for a snappy demo; compress photos when possible.

