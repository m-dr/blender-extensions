#!/usr/bin/env python3
"""
Automated Catalog Sync Worker for Blender Extension Repository.
Discovers and inspects releases across tracked GitHub repositories,
extracts manifest metadata from release .zip packages in memory,
and automatically updates registry.json and index.json.
"""
import argparse
import fnmatch
import hashlib
import io
import json
import os
import subprocess
import sys
import tomllib
import urllib.request
import zipfile

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCES_CONFIG_PATH = os.path.join(REPO_ROOT, "sources.json")
REGISTRY_PATH = os.path.join(REPO_ROOT, "registry.json")
INDEX_PATH = os.path.join(REPO_ROOT, "index.json")


def get_github_headers():
    headers = {
        "User-Agent": "Blender-Extension-Sync-Worker/1.0",
        "Accept": "application/vnd.github+json"
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_json(url):
    req = urllib.request.Request(url, headers=get_github_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def fetch_bytes(url):
    req = urllib.request.Request(url, headers=get_github_headers())
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return "sha256:" + h.hexdigest()


def discover_repositories(sources_cfg):
    repos = set(sources_cfg.get("explicit_repos", []))
    pattern = sources_cfg.get("repo_pattern", "blender-*")
    exclude = set(sources_cfg.get("exclude_repos", []))

    for user in sources_cfg.get("github_users", []):
        url = f"https://api.github.com/users/{user}/repos?per_page=100"
        user_repos = fetch_json(url)
        if user_repos:
            for r in user_repos:
                full_name = r.get("full_name", "")
                name = r.get("name", "")
                if fnmatch.fnmatch(name, pattern) and full_name not in exclude:
                    repos.add(full_name)

    filtered_repos = sorted(r for r in repos if r not in exclude)
    return filtered_repos


def inspect_release_asset(asset):
    asset_name = asset["name"]
    download_url = asset["browser_download_url"]
    print(f"    * Inspecting asset: {asset_name}...")

    zip_data = fetch_bytes(download_url)
    archive_size = len(zip_data)
    archive_hash = sha256_bytes(zip_data)

    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        manifest_files = [f for f in z.namelist() if f == "blender_manifest.toml" or f.endswith("/blender_manifest.toml")]
        if not manifest_files:
            print(f"      [WARN] No blender_manifest.toml found in {asset_name}, skipping.")
            return None

        # Prefer root manifest
        manifest_name = "blender_manifest.toml" if "blender_manifest.toml" in manifest_files else manifest_files[0]
        with z.open(manifest_name) as mf:
            manifest = tomllib.load(mf)

    ext_entry = {
        "id": manifest["id"],
        "schema_version": manifest.get("schema_version", "1.0.0"),
        "name": manifest["name"],
        "tagline": manifest.get("tagline", ""),
        "version": manifest["version"],
        "type": manifest.get("type", "add-on"),
        "blender_version_min": manifest.get("blender_version_min", "5.2.0"),
        "maintainer": manifest.get("maintainer", ""),
        "license": manifest.get("license", ["SPDX:GPL-3.0-or-later"]),
        "tags": manifest.get("tags", []),
        "archive_url": download_url,
        "archive_size": archive_size,
        "archive_hash": archive_hash,
        "website": manifest.get("website", "")
    }

    if "blender_version_max" in manifest:
        ext_entry["blender_version_max"] = manifest["blender_version_max"]
    if "platforms" in manifest:
        ext_entry["platforms"] = manifest["platforms"]

    return ext_entry


def sync_sources():
    if not os.path.exists(SOURCES_CONFIG_PATH):
        raise FileNotFoundError(f"Missing sources config: {SOURCES_CONFIG_PATH}")

    with open(SOURCES_CONFIG_PATH, "r", encoding="utf-8") as f:
        sources_cfg = json.load(f)

    repos = discover_repositories(sources_cfg)
    print(f"Found {len(repos)} tracked repository source(s):")
    for r in repos:
        print(f"  - {r}")

    discovered_extensions = {}

    for repo in repos:
        print(f"\nChecking releases for {repo}...")
        rel_url = f"https://api.github.com/repos/{repo}/releases?per_page=5"
        releases = fetch_json(rel_url)
        if not releases:
            print(f"  No releases found for {repo}.")
            continue

        # Inspect latest release first
        latest_release = releases[0]
        tag_name = latest_release.get("tag_name", "")
        print(f"  Latest release: {tag_name}")

        for asset in latest_release.get("assets", []):
            if asset.get("name", "").endswith(".zip"):
                try:
                    entry = inspect_release_asset(asset)
                    if entry:
                        ext_id = entry["id"]
                        discovered_extensions[ext_id] = entry
                        print(f"      -> Registered [{entry['type']}] {entry['name']} v{entry['version']}")
                except Exception as e:
                    print(f"      [ERROR] Failed to inspect asset {asset.get('name')}: {e}")

    return list(discovered_extensions.values())


def update_catalog(extensions_list, dry_run=False):
    # Load existing registry to preserve custom settings/order if needed
    existing_registry = {}
    base_url = "https://m-dr.github.io/blender-extensions"

    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            existing_registry = json.load(f)
            base_url = existing_registry.get("base_url", base_url)

    # Sort extensions cleanly by type (add-on first, theme second) then by id
    sorted_exts = sorted(extensions_list, key=lambda x: (x.get("type", "add-on"), x["id"]))

    new_registry = {
        "base_url": base_url,
        "extensions": sorted_exts
    }

    # Generate index.json for Blender
    catalog_data = []
    for ext in sorted_exts:
        catalog_data.append(dict(ext))

    new_catalog = {
        "version": "1.0.0",
        "data": catalog_data,
        "blocklist": []
    }

    # Compare with existing
    changed = False
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            old_catalog = json.load(f)
            if old_catalog != new_catalog:
                changed = True
    else:
        changed = True

    if dry_run:
        print(f"\n[DRY RUN] Catalog contains {len(catalog_data)} item(s). Changed: {changed}")
        return changed

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(new_registry, f, indent=2)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(new_catalog, f, indent=2)

    print(f"\nSuccessfully wrote {REGISTRY_PATH} and {INDEX_PATH} with {len(catalog_data)} extension(s)!")
    return changed


def main():
    parser = argparse.ArgumentParser(description="Sync Blender Extension Repository from tracked GitHub sources.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect and report changes without writing files.")
    parser.add_argument("--commit", action="store_true", help="Automatically commit changes to git.")
    parser.add_argument("--push", action="store_true", help="Automatically push committed changes to git remote.")
    args = parser.parse_args()

    extensions_list = sync_sources()
    changed = update_catalog(extensions_list, dry_run=args.dry_run)

    if changed and args.commit and not args.dry_run:
        print("\nCommitting changes to git...")
        subprocess.run(["git", "add", "registry.json", "index.json", "sources.json"], cwd=REPO_ROOT, check=True)
        commit_msg = f"chore(sync): automated catalog update ({len(extensions_list)} items)"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, check=True)

        if args.push:
            print("Pushing changes to remote...")
            subprocess.run(["git", "push", "origin", "main"], cwd=REPO_ROOT, check=True)


if __name__ == "__main__":
    main()
