#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Kodi-installable zip of this addon.

Reads the addon id and version from addon.xml and produces
    <addon_id>-<version>.zip
containing a single top-level folder named <addon_id>, which is what
Kodi requires when installing from a zip ("Install from zip file").

The zip is built from the current working tree, so uncommitted changes
are included. Development files (.git, .idea, .DS_Store, this script,
existing zips, ...) are left out.

Usage:
    python3 release.py
"""
import os
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = os.path.basename(__file__)

# Directory names skipped entirely (with everything under them).
# "tools" holds maintainer-only scripts (data regeneration) that Kodi never runs.
EXCLUDE_DIRS = {".git", ".idea", ".claude", ".github", "__pycache__", "tools"}
# Exact file names to skip.
EXCLUDE_FILES = {".gitignore", ".gitattributes", SCRIPT_NAME}
# File suffixes to skip.
EXCLUDE_SUFFIXES = (".pyc", ".pyo", ".zip")


def read_addon_meta():
    """Return (addon_id, version) from addon.xml."""
    root = ET.parse(os.path.join(ROOT, "addon.xml")).getroot()
    return root.get("id"), root.get("version")


def skip_file(name):
    # Hidden files (.DS_Store, ...), explicit names and suffixes.
    return (name.startswith(".")
            or name in EXCLUDE_FILES
            or name.endswith(EXCLUDE_SUFFIXES))


def build(addon_id, version):
    zip_path = os.path.join(ROOT, "{}-{}.zip".format(addon_id, version))
    if os.path.exists(zip_path):
        os.remove(zip_path)

    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(ROOT):
            # Prune excluded / hidden directories in place (and sort for
            # a deterministic, reproducible archive order).
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in EXCLUDE_DIRS and not d.startswith("."))
            for filename in sorted(filenames):
                if skip_file(filename):
                    continue
                abspath = os.path.join(dirpath, filename)
                relpath = os.path.relpath(abspath, ROOT)
                # Kodi requires everything nested under a folder named after
                # the addon id. Use forward slashes for a valid zip path.
                arcname = addon_id + "/" + relpath.replace(os.sep, "/")
                zf.write(abspath, arcname)
                count += 1
    return zip_path, count


def main():
    addon_id, version = read_addon_meta()
    if not addon_id or not version:
        sys.exit("error: could not read id/version from addon.xml")
    zip_path, count = build(addon_id, version)
    print("Created {} ({} files)".format(os.path.basename(zip_path), count))
    print("Install in Kodi via: Add-ons > Install from zip file")


if __name__ == "__main__":
    main()
