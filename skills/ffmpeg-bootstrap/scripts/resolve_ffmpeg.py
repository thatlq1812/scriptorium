"""Importable helper for other skills: resolve_ffmpeg_path().

Resolution order (local-first, "portable" like every other bootstrap skill in
this project — the binary must live inside the project's own shared venv, not
depend on whatever happens to be on the machine's system PATH):
  1. `imageio_ffmpeg` package's bundled binary — this ships the actual ffmpeg
     executable INSIDE the pip wheel itself (verified: `uv pip install
     imageio-ffmpeg` already places `ffmpeg-win-x86_64-v7.1.exe` at
     `.venv/Lib/site-packages/imageio_ffmpeg/binaries/`, ~88MB, no separate
     download step, no network call at resolve time). This is the primary,
     recommended path.
  2. System PATH (`shutil.which("ffmpeg")`) — last-resort fallback only, for
     the rare case `imageio-ffmpeg` isn't installed in the current venv yet.
"""
import shutil
import subprocess


def resolve_ffmpeg_path() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    except Exception:
        pass  # bundled binary missing/corrupt for some reason - fall through

    path = shutil.which("ffmpeg")
    if path:
        return path

    raise RuntimeError(
        "No ffmpeg resolved: 'imageio-ffmpeg' is not installed in the shared venv, "
        "and no system ffmpeg was found on PATH either. Run:\n"
        "  uv pip install --python .venv -r skills/ffmpeg-bootstrap/requirements.txt"
    )


def _self_test() -> None:
    path = resolve_ffmpeg_path()
    result = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=10, check=False)
    first_line = result.stdout.splitlines()[0] if result.stdout else "(no version output)"
    print(f"Resolved: {path}")
    print(first_line)


if __name__ == "__main__":
    _self_test()
