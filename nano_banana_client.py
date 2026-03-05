"""Nano Banana AI client for image generation using Google Gemini."""

import base64
import os
from pathlib import Path

import google.generativeai as genai
from PIL import Image


def configure(api_key: str | None = None):
    """Configure the Gemini API with the given key."""
    key = api_key or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "Google API key is required. Set GOOGLE_API_KEY env var or pass api_key."
        )
    genai.configure(api_key=key)


def generate_image(
    prompt: str,
    model_name: str = "gemini-2.0-flash-exp",
    output_path: str | None = None,
) -> Image.Image | None:
    """Generate an image from a text prompt using Nano Banana (Gemini).

    Args:
        prompt: Text description of the image to generate.
        model_name: Gemini model to use for image generation.
        output_path: Optional file path to save the generated image.

    Returns:
        PIL Image object if successful, None otherwise.
    """
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)

    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_data = base64.b64decode(part.inline_data.data)
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_data)
            import io
            return Image.open(io.BytesIO(image_data))

    # If no inline image data, return the text response
    print(f"No image generated. Model response: {response.text}")
    return None


def edit_image(
    image_path: str,
    edit_prompt: str,
    model_name: str = "gemini-2.0-flash-exp",
    output_path: str | None = None,
) -> Image.Image | None:
    """Edit an existing image using Nano Banana (Gemini).

    Args:
        image_path: Path to the source image.
        edit_prompt: Description of the edits to apply.
        model_name: Gemini model to use.
        output_path: Optional file path to save the edited image.

    Returns:
        PIL Image object if successful, None otherwise.
    """
    source_image = Image.open(image_path)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content([edit_prompt, source_image])

    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_data = base64.b64decode(part.inline_data.data)
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_data)
            import io
            return Image.open(io.BytesIO(image_data))

    print(f"No image generated. Model response: {response.text}")
    return None
