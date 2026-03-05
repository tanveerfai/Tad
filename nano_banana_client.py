"""Nano Banana AI client for image generation using Google Gemini REST API."""

import base64
import io
import os
from pathlib import Path

import httpx
from PIL import Image

_api_key: str | None = None

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def configure(api_key: str | None = None):
    """Configure the Gemini API with the given key."""
    global _api_key
    _api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not _api_key:
        raise ValueError(
            "Google API key is required. Set GOOGLE_API_KEY env var or pass api_key."
        )


def _get_key() -> str:
    if not _api_key:
        raise ValueError("Call configure() first.")
    return _api_key


def generate_image(
    prompt: str,
    model_name: str = "gemini-2.0-flash-exp",
    output_path: str | None = None,
) -> Image.Image | None:
    """Generate an image from a text prompt using Nano Banana (Gemini REST API).

    Args:
        prompt: Text description of the image to generate.
        model_name: Gemini model to use for image generation.
        output_path: Optional file path to save the generated image.

    Returns:
        PIL Image object if successful, None otherwise.
    """
    url = f"{API_BASE}/{model_name}:generateContent?key={_get_key()}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }

    resp = httpx.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            image_bytes = base64.b64decode(part["inlineData"]["data"])
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
            return Image.open(io.BytesIO(image_bytes))

    # No image in response — print text parts
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "text" in part:
            print(f"No image generated. Model response: {part['text']}")
    return None


def edit_image(
    image_path: str,
    edit_prompt: str,
    model_name: str = "gemini-2.0-flash-exp",
    output_path: str | None = None,
) -> Image.Image | None:
    """Edit an existing image using Nano Banana (Gemini REST API).

    Args:
        image_path: Path to the source image.
        edit_prompt: Description of the edits to apply.
        model_name: Gemini model to use.
        output_path: Optional file path to save the edited image.

    Returns:
        PIL Image object if successful, None otherwise.
    """
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    import mimetypes
    mime = mimetypes.guess_type(image_path)[0] or "image/png"

    url = f"{API_BASE}/{model_name}:generateContent?key={_get_key()}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": edit_prompt},
                    {"inlineData": {"mimeType": mime, "data": image_data}},
                ]
            }
        ],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }

    resp = httpx.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            image_bytes = base64.b64decode(part["inlineData"]["data"])
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
            return Image.open(io.BytesIO(image_bytes))

    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "text" in part:
            print(f"No image generated. Model response: {part['text']}")
    return None
