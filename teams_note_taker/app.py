"""Main application - CLI interface for the Teams Meeting Note Taker."""

import sys
import signal
import threading
import time

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text

from .audio_capture import AudioCapture
from .transcriber import Transcriber
from .notes_processor import NotesProcessor


console = Console()


class MeetingNoteTaker:
    """Main application that orchestrates audio capture, transcription, and note generation."""

    def __init__(self, config=None):
        config = config or {}
        self.output_dir = config.get("output_dir", "output")
        self.model_size = config.get("whisper_model", "base")
        self.language = config.get("language", None)
        self.use_loopback = config.get("use_loopback", True)
        self.device_id = config.get("device_id", None)
        self.meeting_title = config.get("meeting_title", None)
        self.output_format = config.get("output_format", "markdown")

        self.audio = AudioCapture(output_dir=self.output_dir)
        self.transcriber = Transcriber(model_size=self.model_size)
        self.processor = NotesProcessor(output_dir=self.output_dir)

        self._running = False
        self._stop_event = threading.Event()

    def list_audio_devices(self):
        """Print all available audio input devices."""
        devices = self.audio.list_devices()
        table = Table(title="Available Audio Input Devices")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Channels", style="yellow")

        for dev in devices:
            table.add_row(str(dev["id"]), dev["name"], str(dev["channels"]))

        console.print(table)
        return devices

    def start(self):
        """Start recording a meeting."""
        self._running = True
        self._stop_event.clear()

        console.print(Panel(
            "[bold green]Teams Meeting Note Taker[/bold green]\n\n"
            "Recording has started. The tool is running quietly in the background.\n"
            "Press [bold]Ctrl+C[/bold] to stop recording and generate notes.",
            title="Recording",
            border_style="green",
        ))

        # Start audio capture
        try:
            self.audio.start_recording(
                device=self.device_id,
                use_loopback=self.use_loopback,
            )
        except Exception as e:
            console.print(f"[red]Failed to start recording: {e}[/red]")
            console.print("\n[yellow]Tip: Try listing devices with --list-devices and "
                          "pick one with --device ID[/yellow]")
            return

        # Show live status
        try:
            with Live(self._make_status_display(), refresh_per_second=1, console=console) as live:
                while not self._stop_event.is_set():
                    live.update(self._make_status_display())
                    self._stop_event.wait(1)
        except KeyboardInterrupt:
            pass

        self._finish()

    def stop(self):
        """Signal the recording to stop."""
        self._stop_event.set()

    def _make_status_display(self):
        """Create a live status display."""
        duration = self.audio.get_recording_duration()
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        status = Table.grid(padding=1)
        status.add_row(
            Text("Status:", style="bold"),
            Text("Recording", style="bold red blink"),
        )
        status.add_row(
            Text("Duration:", style="bold"),
            Text(f"{minutes:02d}:{seconds:02d}", style="cyan"),
        )
        status.add_row(
            Text("Mode:", style="bold"),
            Text("System Audio (loopback)" if self.use_loopback else "Microphone", style="yellow"),
        )
        status.add_row(
            Text("", style=""),
            Text("Press Ctrl+C to stop", style="dim"),
        )

        return Panel(status, title="Meeting Note Taker", border_style="blue")

    def _finish(self):
        """Stop recording, transcribe, and generate notes."""
        console.print("\n[yellow]Stopping recording...[/yellow]")
        audio_path = self.audio.stop_recording()

        if not audio_path:
            console.print("[red]No audio was captured.[/red]")
            return

        console.print(f"[green]Audio saved to: {audio_path}[/green]")

        # Transcribe
        console.print("\n[yellow]Transcribing audio (this may take a moment)...[/yellow]")
        try:
            transcription = self.transcriber.transcribe_in_chunks(
                audio_path, language=self.language
            )
        except Exception as e:
            console.print(f"[red]Transcription failed: {e}[/red]")
            console.print("[yellow]The audio file has been saved. You can transcribe it later.[/yellow]")
            return

        console.print(f"[green]Transcription complete. Language: {transcription['language']}[/green]")

        # Generate notes
        console.print("[yellow]Generating meeting notes...[/yellow]")
        notes = self.processor.process(transcription, meeting_title=self.meeting_title)
        filepath = self.processor.save_notes(notes, format=self.output_format)

        console.print(Panel(
            f"[bold green]Meeting notes saved![/bold green]\n\n"
            f"File: [cyan]{filepath}[/cyan]\n"
            f"Duration: {notes['duration']}\n"
            f"Action Items: {len(notes.get('action_items', []))}\n"
            f"Decisions: {len(notes.get('decisions', []))}\n"
            f"Questions: {len(notes.get('questions', []))}",
            title="Complete",
            border_style="green",
        ))

    def transcribe_existing(self, audio_path):
        """Transcribe an existing audio file and generate notes."""
        console.print(f"[yellow]Transcribing: {audio_path}[/yellow]")

        transcription = self.transcriber.transcribe_in_chunks(
            audio_path, language=self.language
        )

        console.print(f"[green]Transcription complete. Language: {transcription['language']}[/green]")

        notes = self.processor.process(transcription, meeting_title=self.meeting_title)
        filepath = self.processor.save_notes(notes, format=self.output_format)

        console.print(f"[green]Notes saved to: {filepath}[/green]")
        return filepath


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Teams Meeting Note Taker - Non-intrusive meeting transcription",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start recording (auto-detect system audio)
  python -m teams_note_taker

  # Record from microphone instead of system audio
  python -m teams_note_taker --mic

  # List audio devices
  python -m teams_note_taker --list-devices

  # Use a specific audio device
  python -m teams_note_taker --device 5

  # Transcribe a previously recorded file
  python -m teams_note_taker --file meeting.wav

  # Use a larger model for better accuracy
  python -m teams_note_taker --model medium

  # Set meeting title and output as JSON
  python -m teams_note_taker --title "Sprint Planning" --format json
        """,
    )

    parser.add_argument("--list-devices", action="store_true",
                        help="List available audio input devices and exit")
    parser.add_argument("--device", type=int, default=None,
                        help="Audio device ID to use (see --list-devices)")
    parser.add_argument("--mic", action="store_true",
                        help="Use microphone instead of system audio loopback")
    parser.add_argument("--model", default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--language", default=None,
                        help="Language code (e.g., 'en'). Auto-detects if not set")
    parser.add_argument("--title", default=None,
                        help="Meeting title for the notes")
    parser.add_argument("--output-dir", default="output",
                        help="Directory to save output files (default: output)")
    parser.add_argument("--format", default="markdown", choices=["markdown", "json"],
                        help="Output format (default: markdown)")
    parser.add_argument("--file", default=None,
                        help="Transcribe an existing audio file instead of recording")

    args = parser.parse_args()

    config = {
        "output_dir": args.output_dir,
        "whisper_model": args.model,
        "language": args.language,
        "use_loopback": not args.mic,
        "device_id": args.device,
        "meeting_title": args.title,
        "output_format": args.format,
    }

    app = MeetingNoteTaker(config)

    if args.list_devices:
        app.list_audio_devices()
        return

    if args.file:
        app.transcribe_existing(args.file)
        return

    # Set up graceful shutdown
    def signal_handler(sig, frame):
        app.stop()

    signal.signal(signal.SIGINT, signal_handler)

    app.start()


if __name__ == "__main__":
    main()
