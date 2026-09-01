#!/usr/bin/env python3
"""
Multi-source catalog builder for Blender Extension Repository.
Supports:
  1. Direct external URLs (GitHub Releases, Cloudflare R2, CDN)
  2. In-repo packages / themes (stored in packages/)
"""
import hashlib
import json
import os
import urllib.request

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(REPO_ROOT, "registry.json")
PACKAGES_DIR = os.path.join(REPO_ROOT, "packages")
INDEX_PATH = os.path.join(REPO_ROOT, "index.json")


def sha256_bytes(data):
    h = hashlib.sha256()
    h.update(data)
    return "sha256:" + h.hexdigest()


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def fetch_url_data(url):
    print(f"Fetching metadata for remote package: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Blender/5.2"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
    return len(content), sha256_bytes(content)


def main():
    if not os.path.exists(REGISTRY_PATH):
        raise FileNotFoundError(f"Missing registry config: {REGISTRY_PATH}")

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    base_url = registry.get("base_url", "").rstrip("/")
    extensions_data = []

    for ext in registry.get("extensions", []):
        ext_id = ext["id"]
        version = ext["version"]
        ext_type = ext.get("type", "add-on")

        # Source Resolution: In-repo local package vs. External URL
        if "local_file" in ext:
            pkg_path = os.path.join(REPO_ROOT, ext["local_file"])
            if not os.path.exists(pkg_path):
                raise FileNotFoundError(f"Local package file not found: {pkg_path}")
            archive_size = os.path.getsize(pkg_path)
            archive_hash = sha256_file(pkg_path)
            rel_path = os.path.relpath(pkg_path, REPO_ROOT).replace("\\", "/")
            archive_url = f"{base_url}/{rel_path}" if base_url else rel_path
        elif "archive_url" in ext:
            archive_url = ext["archive_url"]
            if "archive_size" in ext and "archive_hash" in ext:
                archive_size = ext["archive_size"]
                archive_hash = ext["archive_hash"]
            else:
                archive_size, archive_hash = fetch_url_data(archive_url)
        else:
            raise ValueError(f"Extension '{ext_id}' must specify either 'archive_url' or 'local_file'.")

        entry = {
            "id": ext_id,
            "schema_version": ext.get("schema_version", "1.0.0"),
            "name": ext["name"],
            "tagline": ext.get("tagline", ""),
            "version": version,
            "type": ext_type,
            "blender_version_min": ext.get("blender_version_min", "4.2.0"),
            "archive_url": archive_url,
            "archive_hash": archive_hash,
            "archive_size": archive_size,
            "maintainer": ext.get("maintainer", ""),
            "license": ext.get("license", ["SPDX:GPL-3.0-or-later"]),
            "tags": ext.get("tags", []),
            "website": ext.get("website", ""),
        }

        if "blender_version_max" in ext:
            entry["blender_version_max"] = ext["blender_version_max"]
        if "platforms" in ext:
            entry["platforms"] = ext["platforms"]

        extensions_data.append(entry)
        print(f"Registered: [{ext_type}] {ext_id} v{version} -> {archive_url} ({archive_size} bytes)")

    catalog = {
        "version": "1.0.0",
        "data": extensions_data,
        "blocklist": []
    }

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"\nSuccessfully generated catalog with {len(extensions_data)} extension(s): {INDEX_PATH}")


if __name__ == "__main__":
    main()
