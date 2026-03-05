"""Claude AI client for text reasoning and prompt engineering."""

import os

import anthropic


def create_client(api_key: str | None = None) -> anthropic.Anthropic:
    """Create an Anthropic client."""
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "Anthropic API key is required. Set ANTHROPIC_API_KEY env var or pass api_key."
        )
    return anthropic.Anthropic(api_key=key)


def enhance_image_prompt(client: anthropic.Anthropic, user_request: str) -> str:
    """Use Claude to turn a casual request into an optimized image generation prompt.

    Args:
        client: Anthropic client instance.
        user_request: The user's plain-language image request.

    Returns:
        An enhanced, detailed prompt for image generation.
    """
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are an expert at writing prompts for AI image generation. "
                    "Turn the following request into a detailed, descriptive prompt "
                    "that will produce a high-quality image. Include details about "
                    "style, lighting, composition, and mood. Return ONLY the enhanced "
                    "prompt, nothing else.\n\n"
                    f"Request: {user_request}"
                ),
            }
        ],
    )
    return message.content[0].text


def analyze_image(
    client: anthropic.Anthropic,
    image_path: str,
    question: str = "Describe this image in detail.",
) -> str:
    """Use Claude's vision to analyze an image.

    Args:
        client: Anthropic client instance.
        image_path: Path to the image file.
        question: Question to ask about the image.

    Returns:
        Claude's analysis of the image.
    """
    import base64
    import mimetypes

    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": question},
                ],
            }
        ],
    )
    return message.content[0].text
