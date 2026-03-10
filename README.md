# Teams Meeting Note Taker

A **non-intrusive** meeting note taker that runs quietly alongside your Microsoft Teams meetings. No bots, no screen sharing disruption — just start it and forget it until the meeting ends.

## How It Works

1. **Captures audio** from your system's audio output (loopback) or microphone
2. **Transcribes** the audio locally using OpenAI Whisper (no data sent externally)
3. **Generates structured notes** with action items, decisions, questions, and a timeline

## Features

- **Non-intrusive**: Runs in the background, no meeting bot required
- **100% offline transcription**: Uses Whisper locally, your meeting audio never leaves your machine
- **Auto-extracts**: Action items, decisions, and questions from the conversation
- **Timeline view**: 5-minute bucketed timeline of the meeting
- **Multiple output formats**: Markdown or JSON
- **Flexible audio input**: System audio loopback or microphone
- **Chunked transcription**: Handles long meetings without running out of memory

## Quick Start

### Prerequisites

- Python 3.9+
- `ffmpeg` installed on your system
- For system audio capture (Linux): PulseAudio with monitor device
- For system audio capture (macOS): [BlackHole](https://existential.audio/blackhole/) virtual audio device
- For system audio capture (Windows): Stereo Mix enabled or [VB-Cable](https://vb-audio.com/Cable/)

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd Tad

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# Start recording (auto-detects system audio)
python -m teams_note_taker

# Use microphone instead
python -m teams_note_taker --mic

# List available audio devices
python -m teams_note_taker --list-devices

# Use a specific device
python -m teams_note_taker --device 5

# Better accuracy with a larger model
python -m teams_note_taker --model medium

# Set a meeting title
python -m teams_note_taker --title "Sprint Planning"

# Output as JSON instead of Markdown
python -m teams_note_taker --format json

# Transcribe a previously recorded audio file
python -m teams_note_taker --file path/to/meeting.wav
```

### During a Meeting

1. Start the note taker **before** or **during** your Teams meeting
2. The tool shows a live status with recording duration
3. When the meeting ends, press **Ctrl+C**
4. Wait for transcription and note generation
5. Find your notes in the `output/` directory

## Output Example

The generated Markdown notes include:

```
# Sprint Planning - 2026-03-10

**Duration:** 45m 12s
**Language:** en

## Summary
Brief extractive summary of the meeting...

## Action Items
- [ ] Set up the staging environment by Friday
- [ ] Review the API design document
- [ ] Schedule follow-up with the design team

## Decisions
- Use PostgreSQL instead of MongoDB for the new service
- Release v2.0 by end of Q1

## Questions Raised
- Should we migrate the legacy endpoints first?
- What's the budget for the new infrastructure?

## Timeline
### [00:00]
Opening discussion and agenda review...

### [05:00]
Technical discussion about architecture...
```

## Whisper Model Sizes

| Model  | Speed    | Accuracy | VRAM   |
|--------|----------|----------|--------|
| tiny   | Fastest  | Basic    | ~1 GB  |
| base   | Fast     | Good     | ~1 GB  |
| small  | Moderate | Better   | ~2 GB  |
| medium | Slow     | High     | ~5 GB  |
| large  | Slowest  | Best     | ~10 GB |

Start with `base` (default) and move up if you need better accuracy.

## Platform-Specific Audio Setup

### Linux (PulseAudio)
System audio capture works out of the box via PulseAudio monitor devices.

### macOS
Install [BlackHole](https://existential.audio/blackhole/) and create a Multi-Output Device in Audio MIDI Setup that includes both your speakers and BlackHole.

### Windows
Enable "Stereo Mix" in Sound settings, or install [VB-Cable](https://vb-audio.com/Cable/).

## Project Structure

```
teams_note_taker/
├── __init__.py          # Package init
├── __main__.py          # Entry point for python -m
├── app.py               # Main CLI application
├── audio_capture.py     # System/mic audio recording
├── transcriber.py       # Whisper-based transcription
├── notes_processor.py   # Structured note generation
└── config.py            # Configuration management
```
