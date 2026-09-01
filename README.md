# Blender Extension Repository (Registry Hub)

A decentralized, self-hosted extension repository for **Blender 4.2+ / 5.x**.

* **Catalog URL**: `https://m-dr.github.io/blender-extensions/index.json`

---

## How to Connect to Blender

1. Open Blender $\rightarrow$ **Edit > Preferences > Get Extensions** (or **Add-ons**).
2. Click **Repositories** $\rightarrow$ **+ (Add Repository)**:
   * **Name**: `Personal Extensions`
   * **URL**: `https://m-dr.github.io/blender-extensions/index.json`
3. Click **Save Preferences**.

---

## Architecture

This registry operates as a pure metadata catalog:
* **Add-ons**: Downloaded directly from their individual GitHub Releases (zero storage bloat).
* **Themes & Presets**: Can be hosted directly in `packages/` if desired.
* **Large AI Packages**: Supported via Cloudflare R2 or direct CDN links.
