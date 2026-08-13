#!/usr/bin/env python3
"""Download the official Typst static binary (github.com/typst/typst releases,
Apache-2.0, scouted/verified as a reputable source -- already independently
confirmed as "Official typst" in a sibling project's own resource manifest,
D:/elix/praxis_csc/resources/manifest.yaml) into the shared repo-local
location `<repo_root>/.tools/typst/` -- NOT a system-wide install, no
package manager involved. This is the entire point of using Typst here:
a single ~50MB static binary, no TeX distribution (~5GB) needed on the
target machine.

Only run this after check_typst.py confirms typst is actually missing.
Requires internet access (downloads from GitHub) -- stdlib only
(urllib.request, zipfile, tarfile, platform), no third-party dependency.

Exit codes: 0 = installed (or already present), 1 = download/extract failed,
2 = unsupported platform/architecture.

Usage:
    python install_typst.py [--version latest]
"""
from __future__ import annotations

import argparse
import platform
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[4]
SHARED_TYPST_DIR = REPO_ROOT / ".tools" / "typst"
GITHUB_RELEASE_BASE = "https://github.com/typst/typst/releases/latest/download"

# Asset naming per https://github.com/typst/typst/releases -- verified against
# the "latest" release as of 2026-07-27. Only windows-x86_64 has been tested
# for real on this machine; macOS/Linux entries are written by direct analogy
# to the same release's published asset names, not independently verified.
PLATFORM_ASSETS = {
    ("Windows", "AMD64"): ("typst-x86_64-pc-windows-msvc.zip", "zip"),
    ("Darwin", "x86_64"): ("typst-x86_64-apple-darwin.tar.xz", "tar"),
    ("Darwin", "arm64"): ("typst-aarch64-apple-darwin.tar.xz", "tar"),
    ("Linux", "x86_64"): ("typst-x86_64-unknown-linux-musl.tar.xz", "tar"),
    ("Linux", "aarch64"): ("typst-aarch64-unknown-linux-musl.tar.xz", "tar"),
}


def _binary_name() -> str:
    return "typst.exe" if platform.system() == "Windows" else "typst"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()

    key = (platform.system(), platform.machine())
    asset = PLATFORM_ASSETS.get(key)
    if asset is None:
        print(f"UNSUPPORTED: no known Typst release asset for platform {key}. See {GITHUB_RELEASE_BASE.rsplit('/', 2)[0]} to find one manually.", file=sys.stderr)
        return 2
    asset_name, archive_kind = asset

    dest_binary = SHARED_TYPST_DIR / _binary_name()
    if dest_binary.is_file():
        print(f"OK: {dest_binary} already present, nothing to do.")
        return 0

    url = f"{GITHUB_RELEASE_BASE}/{asset_name}"
    print(f"Downloading {url} ...")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / asset_name
            urllib.request.urlretrieve(url, tmp_path)  # noqa: S310 -- fixed, hardcoded official GitHub release URL

            extract_dir = Path(tmp) / "extracted"
            extract_dir.mkdir()
            if archive_kind == "zip":
                with zipfile.ZipFile(tmp_path) as zf:
                    zf.extractall(extract_dir)
            else:
                with tarfile.open(tmp_path, "r:xz") as tf:
                    tf.extractall(extract_dir)

            found = list(extract_dir.rglob(_binary_name()))
            if not found:
                print(f"EXTRACT FAILED: no {_binary_name()!r} found inside {asset_name}.", file=sys.stderr)
                return 1

            SHARED_TYPST_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy(found[0], dest_binary)
            if platform.system() != "Windows":
                dest_binary.chmod(0o755)
    except OSError as exc:
        print(f"INSTALL FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"OK: installed {dest_binary}")
    print("Run check_typst.py to confirm.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
