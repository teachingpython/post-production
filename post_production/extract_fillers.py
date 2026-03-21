import json
import logging
import string
from pathlib import Path

from alive_progress import alive_it
from pydub import AudioSegment

logger = logging.getLogger(__name__)

FILLER_WORDS = ["um", "uh", "hmm", "mhm", "uh huh", "ah"]
CROSSFADE = 100


def strip_punctuation(word):
    trans = str.maketrans("", "", string.punctuation)
    return word.translate(trans).casefold()


def is_filler(word):
    return strip_punctuation(word) in FILLER_WORDS


def load_transcript(transcript_path: Path) -> list:
    """Load transcript JSON and return the words list."""
    with transcript_path.open() as f:
        transcript = json.load(f)
    return transcript.get("words", [])


def find_fillers(words: list) -> list:
    """Filter the word list down to filler words only."""
    return [word for word in words if is_filler(word.get("text"))]


def remove_fillers(
    audio_path: Path,
    transcript_path: Path,
    output_path: Path,
    crossfade_ms: int = CROSSFADE,
) -> Path:
    """Remove filler words from audio based on transcript data.

    Args:
        audio_path: Path to the source audio file (WAV).
        transcript_path: Path to the AssemblyAI transcript JSON.
        output_path: Path for the output audio file.
        crossfade_ms: Crossfade duration in milliseconds between segments.

    Returns:
        Path to the exported output file.
    """
    words = load_transcript(transcript_path)
    fillers = find_fillers(words)

    logger.info("Found %d filler words in transcript", len(fillers))

    podcast = AudioSegment.from_wav(audio_path)

    start = 0
    segments = []
    logger.info("Segmenting audio")
    for filler in alive_it(fillers):
        end = filler.get("start")
        segments.append(podcast[start:end])
        start = filler.get("end")
    segments.append(podcast[start:])

    logger.info("Crossfading %d segments", len(segments))
    output_segment = AudioSegment.empty()
    for segment in alive_it(segments):
        crossfade = min(len(output_segment), len(segment), crossfade_ms)
        output_segment = output_segment.append(segment, crossfade=crossfade)

    output_segment.export(str(output_path))
    logger.info("Exported cleaned audio to %s", output_path)
    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print(
            "Usage: python -m post_production.extract_fillers <audio.wav> <transcript.json> <output.wav>"
        )
        sys.exit(1)

    audio = Path(sys.argv[1])
    transcript = Path(sys.argv[2])
    output = Path(sys.argv[3])

    remove_fillers(audio, transcript, output)
