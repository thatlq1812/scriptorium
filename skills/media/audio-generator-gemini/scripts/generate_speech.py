#!/usr/bin/env python3
"""Generate speech audio (TTS) from text using Gemini, via the user's own API
key (bring-your-own-key — NOT a Scriptorium-managed AI backend). Requires
GEMINI_API_KEY in the environment (or --api-key).

Gemini's TTS output is raw PCM (verified 2026-08-05: mime_type
"audio/l16; rate=24000; channels=1", NOT a WAV file) — this script always
wraps it into a proper .wav file via the stdlib `wave` module before writing.

Single speaker:
    python generate_speech.py "Say cheerfully: The quick brown fox jumps over the lazy dog." out.wav

Single speaker with a specific prebuilt voice:
    python generate_speech.py "Welcome to the show." out.wav --voice Charon

Multi-speaker dialogue (exactly 2 speakers -- a Gemini API requirement, not
a limitation of this script; the text must label each line with the same
speaker names passed via --speaker):
    python generate_speech.py "TTS the following conversation between Joe and Jane:
Joe: How's it going today, Jane?
Jane: Pretty good, how about you?" out.wav --speaker Joe:Charon --speaker Jane:Kore

Voice cloning (BOTH a voice sample AND recorded consent are REQUIRED --
this script refuses to clone a voice without proof of consent, no exception):
    python generate_speech.py "Hello, this is a cloned voice." out.wav \\
        --clone-voice-sample my_voice.wav --clone-consent my_consent.wav
"""
from __future__ import annotations

import argparse
import os
import sys
import wave
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("google-genai not installed. Run: pip install -r requirements.txt")

DEFAULT_MODEL = "gemini-3.1-flash-tts-preview"
DEFAULT_VOICE = "Kore"
PCM_SAMPLE_RATE = 24000  # verified 2026-08-05 against a real API response
PCM_SAMPLE_WIDTH = 2  # 16-bit
PCM_CHANNELS = 1


def _build_speech_config(
    voice: str | None,
    speakers: list[tuple[str, str]] | None,
    language_code: str | None,
    clone_sample: bytes | None,
    clone_consent: bytes | None,
) -> "types.SpeechConfig":
    if speakers:
        if len(speakers) != 2:
            raise ValueError(
                f"Gemini's multi-speaker TTS requires EXACTLY 2 speakers, got {len(speakers)}."
            )
        speaker_configs = [
            types.SpeakerVoiceConfig(
                speaker=name,
                voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)),
            )
            for name, voice_name in speakers
        ]
        return types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(speaker_voice_configs=speaker_configs),
            language_code=language_code,
        )

    if clone_sample is not None:
        # Voice cloning REQUIRES consent_audio -- this is the API's own
        # ownership-verification mechanism (types.ReplicatedVoiceConfig,
        # verified against the installed SDK, 2026-08-05). This script does
        # not offer a way to skip it, matching chatterbox/Resemble AI's own
        # built-in watermarking-for-consent precedent noted in
        # data/references/audio-voice-gen/NOTES.md #1.
        if clone_consent is None:
            raise ValueError(
                "Voice cloning requires --clone-consent (recorded proof of consent to clone this "
                "voice) -- refusing to clone a voice without it, no override available."
            )
        voice_config = types.VoiceConfig(
            replicated_voice_config=types.ReplicatedVoiceConfig(
                mime_type="audio/wav",
                voice_sample_audio=clone_sample,
                consent_audio=clone_consent,
            )
        )
        return types.SpeechConfig(voice_config=voice_config, language_code=language_code)

    return types.SpeechConfig(
        voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice or DEFAULT_VOICE)),
        language_code=language_code,
    )


def generate(
    client: "genai.Client",
    text: str,
    model: str,
    *,
    voice: str | None = None,
    speakers: list[tuple[str, str]] | None = None,
    language_code: str | None = None,
    clone_sample: bytes | None = None,
    clone_consent: bytes | None = None,
) -> bytes:
    """Returns raw PCM bytes (16-bit LE, 24kHz, mono) -- caller wraps into a
    WAV via write_wav(), or feeds directly into anything that accepts raw PCM
    at that spec (e.g. an ffmpeg pipe with -f s16le -ar 24000 -ac 1)."""
    speech_config = _build_speech_config(voice, speakers, language_code, clone_sample, clone_consent)
    response = client.models.generate_content(
        model=model,
        contents=text,
        config=types.GenerateContentConfig(response_modalities=["AUDIO"], speech_config=speech_config),
    )

    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data is not None:
                return part.inline_data.data

    text_out = " ".join(
        p.text for c in response.candidates for p in c.content.parts if getattr(p, "text", None)
    )
    raise RuntimeError(f"Response contained 0 audio parts.{f' Model said: {text_out[:200]}' if text_out else ''}")


def write_wav(pcm_bytes: bytes, output_path: Path) -> None:
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(PCM_CHANNELS)
        wf.setsampwidth(PCM_SAMPLE_WIDTH)
        wf.setframerate(PCM_SAMPLE_RATE)
        wf.writeframes(pcm_bytes)


def _parse_speaker(raw: str) -> tuple[str, str]:
    if ":" not in raw:
        raise argparse.ArgumentTypeError(f"--speaker must be NAME:VOICE, got {raw!r}")
    name, voice_name = raw.split(":", 1)
    return name.strip(), voice_name.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("text", help="Text to speak (or a dialogue script for --speaker mode)")
    parser.add_argument("output_path", type=Path, help="Output .wav file")
    parser.add_argument("--voice", default=None, help=f"Prebuilt voice name (default: {DEFAULT_VOICE}). See Gemini's TTS voice list for valid names.")
    parser.add_argument(
        "--speaker", action="append", type=_parse_speaker, default=None, dest="speakers",
        help="NAME:VOICE, repeat exactly twice for multi-speaker dialogue mode.",
    )
    parser.add_argument("--language-code", default=None, help="ISO 639-1 language code")
    parser.add_argument("--clone-voice-sample", type=Path, default=None, help="WAV sample of the voice to clone (16-bit LE, 24kHz)")
    parser.add_argument("--clone-consent", type=Path, default=None, help="WAV recording of consent to clone the voice above -- REQUIRED if --clone-voice-sample is set")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing GEMINI_API_KEY. This is the user's OWN key (bring-your-own-key), "
            "not a backend managed by Scriptorium — set the environment variable or use --api-key."
        )
    client = genai.Client(api_key=api_key)

    for path_arg in (args.clone_voice_sample, args.clone_consent):
        if path_arg and not path_arg.is_file():
            sys.exit(f"Not found: {path_arg}")

    clone_sample = args.clone_voice_sample.read_bytes() if args.clone_voice_sample else None
    clone_consent = args.clone_consent.read_bytes() if args.clone_consent else None

    try:
        pcm = generate(
            client,
            args.text,
            args.model,
            voice=args.voice,
            speakers=args.speakers,
            language_code=args.language_code,
            clone_sample=clone_sample,
            clone_consent=clone_consent,
        )
    except ValueError as exc:
        sys.exit(str(exc))

    write_wav(pcm, args.output_path)
    print(f"OK: wrote {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
