#!/usr/bin/env python3
"""
Build index.json catalog for Blender Extension Repository.
"""
import hashlib
import json
import os

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(REPO_ROOT, "registry.json")
PACKAGES_DIR = os.path.join(REPO_ROOT, "packages")
INDEX_PATH = os.path.join(REPO_ROOT, "index.json")


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def main():
    if not os.path.exists(REGISTRY_PATH):
        raise FileNotFoundError(f"Missing registry config: {REGISTRY_PATH}")

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    base_url = registry.get("base_url", "").rstrip("/")
    extensions_data = []

    for ext in registry.get("extensions", []):
        pkg_file = ext.get("package_file")
        pkg_path = os.path.join(PACKAGES_DIR, pkg_file)

        if not os.path.exists(pkg_path):
            raise FileNotFoundError(f"Package zip file not found: {pkg_path}")

        archive_size = os.path.getsize(pkg_path)
        archive_hash = sha256_file(pkg_path)
        archive_url = f"{base_url}/packages/{pkg_file}" if base_url else f"packages/{pkg_file}"

        entry = {
            "id": ext["id"],
            "schema_version": ext.get("schema_version", "1.0.0"),
            "name": ext["name"],
            "tagline": ext.get("tagline", ""),
            "version": ext["version"],
            "type": ext.get("type", "add-on"),
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

        extensions_data.append(entry)
        print(f"Registered: {entry['id']} v{entry['version']} ({archive_size} bytes, {archive_hash[:16]}...)")

    catalog = {
        "version": "1.0.0",
        "data": extensions_data,
        "blocklist": []
    }

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"\nSuccessfully generated catalog: {INDEX_PATH}")


if __name__ == "__main__":
    main()
