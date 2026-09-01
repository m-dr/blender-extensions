# Agent Guide: Blender Extension Repository

This repository is the central **Blender 4.2+ Extension Registry Hub**. It serves `index.json` and hosts `.zip` packages for direct installation inside Blender.

---

## Repository Structure
- `registry.json`: Source list of all managed extensions and metadata.
- `packages/`: Directory containing distribution `.zip` archives.
- `index.json`: Generated catalog consumed by Blender.
- `build_repo.py`: Script to generate `index.json` from `registry.json` and compute file hashes.
- `.github/workflows/deploy.yml`: Automated GitHub Pages deployment on push to `main`.

---

## SOP: Adding or Updating an Extension

When an agent needs to register a new add-on or update an existing one:

### Step 1: Copy Package Archive
Place the new `.zip` archive into the `packages/` directory:
```text
packages/my_extension-1.0.0.zip
```

### Step 2: Update `registry.json`
Add or update the extension entry in `registry.json`:
```json
{
  "id": "my_extension",
  "name": "My Extension",
  "tagline": "Short description",
  "version": "1.0.0",
  "type": "add-on",
  "blender_version_min": "4.2.0",
  "maintainer": "Maintainer Name",
  "license": ["SPDX:GPL-3.0-or-later"],
  "tags": ["3D View"],
  "package_file": "my_extension-1.0.0.zip",
  "website": "https://github.com/m-dr/my-extension"
}
```

### Step 3: Rebuild Catalog
```bash
python build_repo.py
```

### Step 4: Commit & Push
```bash
git add .
git commit -m "feat(repo): add/update <extension_id> v<version>"
git push origin main
```
