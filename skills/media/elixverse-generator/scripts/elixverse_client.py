"""Shared HTTP client for Elixverse's OpenAI-compatible REST API (BYOK --
bring-your-own-key; Scriptorium never holds or manages this key, see
generate_image.py's module docstring for the full "doesn't contradict the
no-AI-backend principle" reasoning). Stdlib only -- no requests/SDK
dependency needed for a plain Bearer-token JSON REST API. Used by
generate_image.py and analyze_reference.py.

Base URL and auth verified against Elixverse's own real quickstart docs
(pasted into PROJECT.md, 2026-08-19) and cross-checked against the real
server-side request schema at D:/elix/platform/server/src/api/v1/images.py
(ImageGenerationRequest) -- that schema is the reason this skill's anchor
support works the way it does (see describe_images() below).
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request

BASE_URL = "https://api.elixverse.com/api/v1"

_ANALYSIS_PROMPT = {
    "style": (
        "Describe this image's visual STYLE (not its subject) in a short, dense "
        "paragraph usable as a prompt prefix to generate new images in the same "
        "style. Cover: color palette (name actual colors), lighting/mood, "
        "line-weight or rendering technique (flat/photorealistic/watercolor/etc.), "
        "composition tendencies, and any distinctive motifs. Do not describe what "
        "the subject IS, only HOW it is rendered."
    ),
    "identity": (
        "Describe this image's SUBJECT identity in a short, dense paragraph precise "
        "enough that another image generator could recreate the same subject from "
        "the text alone: face shape/proportions, hair color and style, distinctive "
        "markings or features, and any consistent clothing/character-design "
        "elements. Do not describe pose, camera angle, background, lighting, or art "
        "style -- only what makes this specific subject identifiable."
    ),
}


def resolve_api_key(explicit: str | None) -> str:
    key = explicit or os.environ.get("ELIXVERSE_API_KEY")
    if not key:
        sys.exit(
            "Missing ELIXVERSE_API_KEY. This is the user's OWN key (bring-your-own-key), "
            "not a backend managed by Scriptorium -- set the environment variable or use --api-key."
        )
    return key


def post_json(path: str, api_key: str, payload: dict, timeout: float = 180.0) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Elixverse API error {exc.code} on {path}: {body}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Elixverse API unreachable ({path}): {exc.reason}") from None


def _image_bytes_to_data_uri(image_bytes: bytes, filename_hint: str = "ref.png") -> str:
    mime = mimetypes.guess_type(filename_hint)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def describe_images(image_bytes_list: list[bytes], kind: str, api_key: str, model: str | None = None) -> str:
    """Vision-based text description of 1+ reference images via
    /chat/completions -- Elixverse's /images/generations has NO
    reference-image input (verified against the real request schema,
    D:/elix/platform/server/src/api/v1/images.py: ImageGenerationRequest only
    accepts prompt/model/size/quality/n/style/response_format, no image
    field, and generate_image() on the adapter side takes the same flat
    kwargs). So identity/style anchoring in this skill goes through this
    text-description bridge instead of native image conditioning -- the
    reference image is described in words, then that description is folded
    into the /images/generations prompt as a strength-graded instruction
    (see generate_image.py's _identity_instruction/_style_instruction)."""
    if kind not in _ANALYSIS_PROMPT:
        raise ValueError(f"kind must be 'style' or 'identity', got {kind!r}")
    instruction = _ANALYSIS_PROMPT[kind]
    if len(image_bytes_list) > 1:
        instruction += (
            f" The {len(image_bytes_list)} attached images together define ONE "
            f"{kind} -- synthesize their common features into a single consistent "
            "description, don't just describe the first image."
        )
    content: list[dict] = [{"type": "text", "text": instruction}]
    for i, img in enumerate(image_bytes_list):
        content.append({"type": "image_url", "image_url": {"url": _image_bytes_to_data_uri(img, f"ref{i}.png")}})
    payload: dict = {"messages": [{"role": "user", "content": content}]}
    if model:
        payload["model"] = model
    result = post_json("/chat/completions", api_key, payload)
    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected /chat/completions response shape: {result}") from exc


def generate_images(
    prompt: str,
    api_key: str,
    *,
    model: str | None = None,
    size: str = "1024x1024",
    quality: str = "standard",
    n: int = 1,
    style: str = "vivid",
    response_format: str = "b64_json",
) -> dict:
    """Mirrors the real ImageGenerationRequest shape exactly (see module
    docstring) -- no field this skill invents that the server doesn't
    accept."""
    payload: dict = {
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": n,
        "style": style,
        "response_format": response_format,
    }
    if model:
        payload["model"] = model
    return post_json("/images/generations", api_key, payload)
