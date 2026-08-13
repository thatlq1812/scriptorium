#!/usr/bin/env python3
"""Safe, read-only detection. Checks the LOCAL portable resource first
(imageio-ffmpeg's bundled binary inside the shared venv — no network call,
the binary already shipped inside the pip wheel at install time), then
reports system PATH ffmpeg as secondary/informational only."""
import shutil
import subprocess
import sys


def main() -> int:
    try:
        import imageio_ffmpeg

        local_path = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        local_path = None
    except Exception as exc:
        print(f"WARNING: 'imageio-ffmpeg' is installed but failed to resolve its binary: {exc}")
        local_path = None

    system_path = shutil.which("ffmpeg")

    if local_path:
        result = subprocess.run([local_path, "-version"], capture_output=True, text=True, timeout=10, check=False)
        first_line = result.stdout.splitlines()[0] if result.stdout else "(no version output)"
        print(f"OK (local, portable): {local_path}")
        print(first_line)
        if system_path:
            print(f"(system ffmpeg also found at {system_path}, but the local copy above is what resolve_ffmpeg_path() will use)")
        return 0

    if system_path:
        print(f"PARTIAL: no local portable ffmpeg yet, but a system ffmpeg was found at {system_path}.")
        print("resolve_ffmpeg_path() will fall back to this for now, but the project won't be portable")
        print("across machines until the local copy is installed. Run:")
        print("  uv pip install --python .venv -r skills/media/ffmpeg-bootstrap/requirements.txt")
        return 0

    print("MISSING: no local portable ffmpeg (imageio-ffmpeg not installed) and no system ffmpeg on PATH.")
    print("Install the local, portable copy (recommended, lives inside this project's own .venv):")
    print("  uv pip install --python .venv -r skills/media/ffmpeg-bootstrap/requirements.txt")
    print("(Optional, system-wide install instead: install_ffmpeg_system.ps1 / .sh)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
