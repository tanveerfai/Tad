"""
Tad — Integrated Claude + Nano Banana AI Pipeline

Uses Claude for intelligent prompt engineering and image analysis,
and Nano Banana (Gemini) for image generation and editing.
"""

import argparse
import os

from dotenv import load_dotenv

import claude_client
import nano_banana_client


def generate(user_request: str, output_path: str = "output/generated.png"):
    """Generate an image: Claude enhances the prompt, Nano Banana creates the image.

    Args:
        user_request: Plain-language description of the desired image.
        output_path: Where to save the generated image.
    """
    # Step 1: Claude enhances the prompt
    print(f"[Claude] Enhancing prompt: {user_request!r}")
    client = claude_client.create_client()
    enhanced_prompt = claude_client.enhance_image_prompt(client, user_request)
    print(f"[Claude] Enhanced prompt: {enhanced_prompt!r}")

    # Step 2: Nano Banana generates the image
    print("[Nano Banana] Generating image...")
    image = nano_banana_client.generate_image(enhanced_prompt, output_path=output_path)

    if image:
        print(f"[Done] Image saved to {output_path}")

        # Step 3: Claude analyzes the result
        print("[Claude] Analyzing generated image...")
        analysis = claude_client.analyze_image(client, output_path)
        print(f"[Claude] Analysis: {analysis}")
    else:
        print("[Error] Image generation failed.")


def analyze(image_path: str, question: str = "Describe this image in detail."):
    """Analyze an existing image using Claude's vision.

    Args:
        image_path: Path to the image to analyze.
        question: Question to ask about the image.
    """
    client = claude_client.create_client()
    print(f"[Claude] Analyzing {image_path}...")
    result = claude_client.analyze_image(client, image_path, question)
    print(f"[Claude] {result}")


def edit(image_path: str, edit_request: str, output_path: str = "output/edited.png"):
    """Edit an image: Claude refines the edit instructions, Nano Banana applies them.

    Args:
        image_path: Path to the source image.
        edit_request: Plain-language description of the edits.
        output_path: Where to save the edited image.
    """
    client = claude_client.create_client()

    # Step 1: Claude refines the edit instructions
    print(f"[Claude] Refining edit instructions: {edit_request!r}")
    enhanced = claude_client.enhance_image_prompt(
        client,
        f"Edit this image: {edit_request}",
    )
    print(f"[Claude] Enhanced edit prompt: {enhanced!r}")

    # Step 2: Nano Banana applies the edit
    print("[Nano Banana] Editing image...")
    image = nano_banana_client.edit_image(image_path, enhanced, output_path=output_path)

    if image:
        print(f"[Done] Edited image saved to {output_path}")
    else:
        print("[Error] Image editing failed.")


def main():
    load_dotenv()
    nano_banana_client.configure()

    parser = argparse.ArgumentParser(
        description="Tad — Claude + Nano Banana AI integration"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate an image from text")
    gen_parser.add_argument("prompt", help="Image description")
    gen_parser.add_argument("-o", "--output", default="output/generated.png")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze an image with Claude")
    analyze_parser.add_argument("image", help="Path to image file")
    analyze_parser.add_argument("-q", "--question", default="Describe this image in detail.")

    # edit command
    edit_parser = subparsers.add_parser("edit", help="Edit an existing image")
    edit_parser.add_argument("image", help="Path to source image")
    edit_parser.add_argument("instruction", help="Edit instructions")
    edit_parser.add_argument("-o", "--output", default="output/edited.png")

    args = parser.parse_args()

    if args.command == "generate":
        generate(args.prompt, args.output)
    elif args.command == "analyze":
        analyze(args.image, args.question)
    elif args.command == "edit":
        edit(args.image, args.instruction, args.output)


if __name__ == "__main__":
    main()
