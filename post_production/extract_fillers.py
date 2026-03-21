import json
import logging
import string
from collections import Counter
from pathlib import Path

from alive_progress import alive_it
from pydub import AudioSegment
from pydub.playback import play

filler_words = ["um", "uh", "hmm", "mhm", "uh huh", "ah"]
transcript_path = Path(
    "/Users/sean/Dropbox (Personal)/Teaching Python/Podcast/Episode 82/Episode 82 raw - Enhanced.json"
)

logger = logging.getLogger(__name__)

CROSSFADE = 100


def strip_punctuation(word):
    trans = str.maketrans("", "", string.punctuation)
    return word.translate(trans).casefold()


def is_filler(word):
    return strip_punctuation(word) in filler_words


with transcript_path.open() as f:
    transcript = json.load(f)

words = transcript.get("words", [])

fillers = [word for word in words if is_filler(word.get("text"))]


podcast_file = Path(
    "/Users/sean/Dropbox (Personal)/Teaching Python/Podcast/Episode 82/output/Episode 82 raw - Enhanced.wav"
)
podcast = AudioSegment.from_wav(podcast_file)

start = 0

segments = []
print("segmenting audio")
for filler in alive_it(fillers):
    end = filler.get("start")
    segments.append(podcast[start:end])
    start = filler.get("end")
else:
    segments.append(podcast[start:])


print("crossfading")
output_segment = AudioSegment.empty()
for segment in alive_it(segments):
    crossfade = min(len(output_segment), len(segment), CROSSFADE)
    output_segment = output_segment.append(segment, crossfade=crossfade)

output_segment.export("test_audio.wav")
