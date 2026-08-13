#!/usr/bin/env python3
"""Concatenates per-scene voice WAV files (from audio-generator-gemini) back
to back into ONE combined voice track, via ffmpeg's concat demuxer (stream
copy, no re-encode -- safe here since every input is the same format:
16-bit PCM, 24kHz, mono, all produced by the same TTS skill)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

_toolchain_bootstrap = next(Path(__file__).resolve().parents[3].glob("*/toolchain-bootstrap"), None)
if _toolchain_bootstrap is None:
    sys.exit("concat_audio.py requires the 'toolchain-bootstrap' skill installed as a sibling skill folder.")
sys.path.insert(0, str(_toolchain_bootstrap / "scripts"))
from resolve_ffmpeg import resolve_ffmpeg_path  # noqa: E402


def concat_wavs(wav_paths: list[Path], output_path: Path) -> None:
    if not wav_paths:
        raise ValueError("concat_wavs() needs at least 1 input file")
    if len(wav_paths) == 1:
        output_path.write_bytes(Path(wav_paths[0]).read_bytes())
        return

    ffmpeg = resolve_ffmpeg_path()
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in wav_paths:
            escaped = str(Path(p).resolve()).replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")
        list_path = f.name

    try:
        cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed:\n{result.stderr[-2000:]}")
    finally:
        Path(list_path).unlink(missing_ok=True)
