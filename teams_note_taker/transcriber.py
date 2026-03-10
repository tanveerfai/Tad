"""Transcription engine - converts audio to text using OpenAI Whisper (runs locally)."""

import os


class Transcriber:
    """Transcribes audio files to text using Whisper (offline, no data sent externally)."""

    def __init__(self, model_size="base"):
        """Initialize the transcriber.

        Args:
            model_size: Whisper model size. Options:
                - "tiny"  : fastest, least accurate (~1GB VRAM)
                - "base"  : good balance for meetings (~1GB VRAM)
                - "small" : better accuracy (~2GB VRAM)
                - "medium": high accuracy (~5GB VRAM)
                - "large" : best accuracy (~10GB VRAM)
        """
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            import whisper
            self._model = whisper.load_model(self.model_size)
        return self._model

    def transcribe(self, audio_path, language=None):
        """Transcribe an audio file to text with timestamps.

        Args:
            audio_path: Path to the WAV audio file.
            language: Language code (e.g., "en"). None for auto-detect.

        Returns:
            dict with keys:
                - "text": Full transcription text.
                - "segments": List of segments with timestamps and text.
                - "language": Detected language.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self._load_model()

        options = {"verbose": False}
        if language:
            options["language"] = language

        result = model.transcribe(audio_path, **options)

        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
            })

        return {
            "text": result["text"].strip(),
            "segments": segments,
            "language": result.get("language", "unknown"),
        }

    def transcribe_in_chunks(self, audio_path, chunk_duration_sec=300, language=None):
        """Transcribe a long audio file in chunks for memory efficiency.

        Args:
            audio_path: Path to the WAV audio file.
            chunk_duration_sec: Duration of each chunk in seconds (default 5 min).
            language: Language code or None for auto-detect.

        Returns:
            Same format as transcribe().
        """
        import wave
        import numpy as np
        import tempfile

        with wave.open(audio_path, "rb") as wf:
            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            total_duration = n_frames / sample_rate

        # If short enough, transcribe directly
        if total_duration <= chunk_duration_sec:
            return self.transcribe(audio_path, language)

        all_segments = []
        all_text_parts = []
        chunk_frames = chunk_duration_sec * sample_rate

        with wave.open(audio_path, "rb") as wf:
            offset = 0
            while offset < n_frames:
                frames_to_read = min(chunk_frames, n_frames - offset)
                wf.setpos(offset)
                raw_data = wf.readframes(frames_to_read)

                # Write chunk to temp file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                    with wave.open(tmp_path, "wb") as chunk_wf:
                        chunk_wf.setnchannels(n_channels)
                        chunk_wf.setsampwidth(sampwidth)
                        chunk_wf.setframerate(sample_rate)
                        chunk_wf.writeframes(raw_data)

                try:
                    result = self.transcribe(tmp_path, language)
                    time_offset = offset / sample_rate
                    for seg in result["segments"]:
                        seg["start"] += time_offset
                        seg["end"] += time_offset
                        all_segments.append(seg)
                    all_text_parts.append(result["text"])
                    if not language:
                        language = result.get("language")
                finally:
                    os.unlink(tmp_path)

                offset += frames_to_read

        return {
            "text": " ".join(all_text_parts),
            "segments": all_segments,
            "language": language or "unknown",
        }
