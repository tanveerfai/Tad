"""Notes processor - converts raw transcription into structured meeting notes."""

import re
import datetime
import json
import os


class NotesProcessor:
    """Processes raw transcription into structured, readable meeting notes."""

    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def process(self, transcription, meeting_title=None):
        """Convert transcription data into structured meeting notes.

        Args:
            transcription: Dict from Transcriber with "text", "segments", "language".
            meeting_title: Optional title for the meeting.

        Returns:
            dict with structured meeting notes.
        """
        segments = transcription.get("segments", [])
        full_text = transcription.get("text", "")

        if not meeting_title:
            meeting_title = f"Meeting Notes - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Build timeline from segments
        timeline = self._build_timeline(segments)

        # Extract key phrases that look like action items or decisions
        action_items = self._extract_action_items(full_text)
        decisions = self._extract_decisions(full_text)
        questions = self._extract_questions(full_text)

        # Calculate meeting stats
        duration_sec = segments[-1]["end"] if segments else 0
        duration_min = int(duration_sec // 60)
        duration_remaining_sec = int(duration_sec % 60)

        notes = {
            "title": meeting_title,
            "date": datetime.datetime.now().isoformat(),
            "duration": f"{duration_min}m {duration_remaining_sec}s",
            "language": transcription.get("language", "unknown"),
            "summary": self._generate_summary(full_text),
            "timeline": timeline,
            "action_items": action_items,
            "decisions": decisions,
            "questions": questions,
            "full_transcript": full_text,
        }

        return notes

    def _build_timeline(self, segments):
        """Group segments into time-bucketed sections."""
        if not segments:
            return []

        timeline = []
        bucket_duration = 300  # 5-minute buckets
        current_bucket_start = 0
        current_texts = []

        for seg in segments:
            bucket_index = int(seg["start"] // bucket_duration)
            bucket_start = bucket_index * bucket_duration

            if bucket_start != current_bucket_start and current_texts:
                timeline.append({
                    "time": self._format_time(current_bucket_start),
                    "content": " ".join(current_texts),
                })
                current_texts = []
                current_bucket_start = bucket_start

            current_texts.append(seg["text"])

        # Add remaining
        if current_texts:
            timeline.append({
                "time": self._format_time(current_bucket_start),
                "content": " ".join(current_texts),
            })

        return timeline

    def _extract_action_items(self, text):
        """Extract potential action items from the transcript."""
        patterns = [
            r"(?:we need to|we should|let's|please|make sure to|don't forget to|action item[s]?[:\s]|todo[:\s]|task[:\s]|follow up on|will do|i'll|i will|going to)\s+([^.!?\n]{10,100})",
        ]
        items = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                cleaned = match.strip().rstrip(",;:")
                if cleaned and cleaned not in items:
                    items.append(cleaned)
        return items

    def _extract_decisions(self, text):
        """Extract potential decisions from the transcript."""
        patterns = [
            r"(?:we decided|decision is|agreed to|consensus is|we'll go with|let's go with|final answer is|we're going to)\s+([^.!?\n]{10,100})",
        ]
        items = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                cleaned = match.strip().rstrip(",;:")
                if cleaned and cleaned not in items:
                    items.append(cleaned)
        return items

    def _extract_questions(self, text):
        """Extract questions raised during the meeting."""
        sentences = re.split(r'[.!]\s+', text)
        questions = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence.endswith("?") and len(sentence) > 15:
                if sentence not in questions:
                    questions.append(sentence)
        return questions

    def _generate_summary(self, text):
        """Generate a brief summary from the transcript.

        This is a simple extractive summary. For better results,
        you can integrate an LLM API here.
        """
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if not sentences:
            return "No significant content captured."

        # Take key sentences from beginning, middle, and end
        summary_sentences = []
        if len(sentences) >= 3:
            summary_sentences.append(sentences[0])
            summary_sentences.append(sentences[len(sentences) // 2])
            summary_sentences.append(sentences[-1])
        else:
            summary_sentences = sentences[:3]

        return ". ".join(summary_sentences) + "."

    def _format_time(self, seconds):
        """Format seconds into HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def save_notes(self, notes, format="markdown"):
        """Save meeting notes to a file.

        Args:
            notes: Dict of structured meeting notes.
            format: "markdown" or "json".

        Returns:
            Path to the saved file.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            filepath = os.path.join(self.output_dir, f"notes_{timestamp}.json")
            with open(filepath, "w") as f:
                json.dump(notes, f, indent=2)
        else:
            filepath = os.path.join(self.output_dir, f"notes_{timestamp}.md")
            with open(filepath, "w") as f:
                f.write(self._to_markdown(notes))

        return filepath

    def _to_markdown(self, notes):
        """Convert notes dict to formatted markdown."""
        lines = []
        lines.append(f"# {notes['title']}")
        lines.append("")
        lines.append(f"**Date:** {notes['date']}")
        lines.append(f"**Duration:** {notes['duration']}")
        lines.append(f"**Language:** {notes['language']}")
        lines.append("")

        lines.append("## Summary")
        lines.append(notes.get("summary", "N/A"))
        lines.append("")

        if notes.get("action_items"):
            lines.append("## Action Items")
            for item in notes["action_items"]:
                lines.append(f"- [ ] {item}")
            lines.append("")

        if notes.get("decisions"):
            lines.append("## Decisions")
            for item in notes["decisions"]:
                lines.append(f"- {item}")
            lines.append("")

        if notes.get("questions"):
            lines.append("## Questions Raised")
            for q in notes["questions"]:
                lines.append(f"- {q}")
            lines.append("")

        if notes.get("timeline"):
            lines.append("## Timeline")
            for entry in notes["timeline"]:
                lines.append(f"### [{entry['time']}]")
                lines.append(entry["content"])
                lines.append("")

        lines.append("## Full Transcript")
        lines.append(notes.get("full_transcript", "N/A"))
        lines.append("")

        return "\n".join(lines)
