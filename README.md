# Tad

Claude + Nano Banana AI integration — uses Claude for intelligent prompt engineering and image analysis, and Nano Banana (Google Gemini) for image generation and editing.

## How It Works

1. **Generate**: You describe an image in plain language. Claude enhances your prompt for better results, then Nano Banana generates the image. Claude analyzes the result.
2. **Analyze**: Claude's vision analyzes any image and answers questions about it.
3. **Edit**: You describe edits to an existing image. Claude refines the instructions, then Nano Banana applies the changes.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your API keys:
   ```bash
   cp .env.example .env
   ```
   - **ANTHROPIC_API_KEY** — get one at https://console.anthropic.com/
   - **GOOGLE_API_KEY** — get one at https://aistudio.google.com/apikey

## Usage

```bash
# Generate an image from a text description
python main.py generate "a cat sitting on a rainbow"

# Generate with custom output path
python main.py generate "sunset over mountains" -o output/sunset.png

# Analyze an image with Claude
python main.py analyze path/to/image.png

# Analyze with a specific question
python main.py analyze path/to/image.png -q "What colors are in this image?"

# Edit an existing image
python main.py edit path/to/image.png "make the sky more dramatic"
```

## Project Structure

```
├── main.py                 # CLI entry point and pipeline orchestration
├── claude_client.py        # Claude API client (prompt enhancement + vision)
├── nano_banana_client.py   # Nano Banana / Gemini image generation client
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
└── .gitignore
```
