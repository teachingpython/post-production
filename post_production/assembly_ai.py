import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class AssemblyAI:
    api_endpoint = "https://api.assemblyai.com/v2"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._session = requests.Session()
        headers = {"authorization": api_key}
        self._session.headers.update(headers)

    def upload(self, file_path: Path):
        url = self.api_endpoint + "/upload"
        r = self._session.post(url, data=read_file(file_path))
        r.raise_for_status()
        return r.json().get("upload_url")

    def transcribe(
        self,
        audio_url: str,
        speaker_labels: bool = False,
        word_boost: Optional[List[str]] = None,
        auto_chapters: bool = False,
        auto_highlights: bool = True,
        disfluencies: bool = False,
    ):
        if word_boost is None:
            word_boost = []

        url = self.api_endpoint + "/transcript"
        payload = {
            "audio_url": audio_url,
            "speaker_labels": speaker_labels,
            "word_boost": word_boost,
            "disfluencies": disfluencies,
            "auto_chapters": auto_chapters,
            "auto_highlights": auto_highlights,
        }

        r = self._session.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        logger.info("Created job with id %s: %s", data.get("id"), data)
        return data.get("id")

    def result(self, job_id: str) -> Dict[Any, Any]:
        url = f"{self.api_endpoint}/transcript/{job_id}"
        r = self._session.get(url)
        r.raise_for_status()
        return r.json()


class TranscriptResult:
    def __init__(self, **kwargs):
        for kwarg, value in kwargs.items():
            setattr(self, kwarg, value)

        self.speakers = {}

    def as_txt(self, prompt_speaker_labels: bool = True):
        sections = []
        for utterance in self.utterances:
            if prompt_speaker_labels:
                speaker_name = self.get_speaker(utterance)
            else:
                speaker_name = utterance.get("speaker")
            section = f"{speaker_name}:\n{utterance.get('text')}\n"
            sections.append(section)
        return "\n".join(sections)

    def get_speaker(self, utterance) -> str:
        speaker = utterance.get("speaker")
        speaker_name = self.speakers.get(speaker)
        if not speaker_name:
            print(f"Speaker {speaker} not found for {utterance.get('text')}")
            speaker_name = input("Enter speaker label for this section: ")
            self.speakers[speaker] = speaker_name
        return speaker_name


def read_file(filename, chunk_size=5242880):
    with open(filename, "rb") as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data
