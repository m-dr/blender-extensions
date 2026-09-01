# Agent Operating Guide: Blender Extension Repository

This repository acts as the central **Extension Registry Index** for Blender 4.2+ and 5.x. It generates `index.json` and hosts light in-repo assets (such as themes) while pointing directly to external releases for larger add-ons.

---

## 1. Supported Extension Sources

The catalog builder (`build_repo.py`) supports 4 distinct distribution patterns in `registry.json`:

### Pattern A: Dedicated GitHub Release (Recommended for Add-ons)
Points directly to a release asset on the add-on's own public repository.
```json
{
  "id": "synchronize_workspaces",
  "name": "Synchronize Workspaces",
  "version": "1.15.0",
  "type": "add-on",
  "blender_version_min": "4.2.0",
  "maintainer": "MultLabs / m-dr",
  "archive_url": "https://github.com/m-dr/blender-sync-workspaces/releases/download/v1.15.0/synchronize_workspaces-1.15.0.zip",
  "website": "https://github.com/m-dr/blender-sync-workspaces"
}
```

### Pattern B: 3rd-Party Creator Release (Brady Johnston, Robert Rioux, etc.)
Points directly to an external author's public GitHub release:
```json
{
  "id": "molecular_nodes",
  "name": "Molecular Nodes",
  "version": "4.2.0",
  "type": "add-on",
  "blender_version_min": "4.2.0",
  "maintainer": "Brady Johnston",
  "archive_url": "https://github.com/bradyajohnston/MolecularNodes/releases/download/v4.2.0/MolecularNodes-4.2.0.zip",
  "website": "https://github.com/bradyajohnston/MolecularNodes"
}
```

### Pattern C: In-Repo Hosted Asset (Themes, UI Presets, Mini-Scripts)
Stored directly in `packages/` or `themes/` within this repository:
```json
{
  "id": "nordic_dark_theme",
  "name": "Nordic Dark Theme",
  "version": "1.0.0",
  "type": "theme",
  "blender_version_min": "4.2.0",
  "maintainer": "m-dr",
  "local_file": "packages/nordic_dark_theme-1.0.0.zip"
}
```

### Pattern D: Cloudflare R2 / S3 Object Storage (Large AI Packages / Gumroad)
For heavy packages (100 MB+ PyTorch/ONNX models or purchased Gumroad archives):
```json
{
  "id": "ai_enhancer",
  "name": "AI Viewport Enhancer",
  "version": "1.0.0",
  "type": "add-on",
  "blender_version_min": "4.2.0",
  "maintainer": "m-dr",
  "archive_url": "https://extensions.yourdomain.com/packages/ai_enhancer-1.0.0.zip"
}
```

---

## 2. SOP for AI Agents Adding / Updating Extensions

1. **Edit `registry.json`**: Add or update the extension entry with the appropriate pattern above.
2. **Rebuild Catalog**:
   ```bash
   python build_repo.py
   ```
   *(The script automatically downloads remote metadata or calculates local hashes).*
3. **Commit & Push**:
   ```bash
   git add .
   git commit -m "feat(registry): add/update <extension_id> v<version>"
   git push origin main
   ```
4. GitHub Actions automatically deploys the updated `index.json` to GitHub Pages within ~20 seconds.
