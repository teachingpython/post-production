import json
import logging
import os
import time
from pathlib import Path
from typing import List

import click_spinner
import typer
from tabulate import tabulate

from post_production.assembly_ai import AssemblyAI, TranscriptResult
from post_production.main import app

logger = logging.getLogger(__name__)


@app.command()
def transcribe(input_file: Path = typer.Argument(..., exists=True)):
    assembly_banner()

    infile = Path(input_file)
    api_key = get_assemblyai_key()
    client = AssemblyAI(api_key)

    typer.echo(f"Uploading {infile.name} to AssemblyAI")
    audio_url = client.upload(infile)

    if typer.confirm("Do you want to add a list of priority words? ", default=True):
        word_list = get_word_list()
    else:
        word_list = []

    typer.echo(f"Beginning transcription job.")
    job_id = client.transcribe(
        audio_url=audio_url, speaker_labels=True, word_boost=word_list
    )
    result = client.result(job_id)
    typer.echo(f"Job {result.get('id')}: {result.get('status')}")
    with click_spinner.spinner():
        while result.get("status") not in ("completed", "error"):
            time.sleep(1)
            result = client.result(job_id)

    if result.get("status") == "completed":
        out_path = infile.parent / Path(infile.stem + ".json")
        save_json(out_path, result)

    typer.echo(f"Transcript JSON saved to output directory")
    if typer.prompt("Would you like to generate a plain-text transcript?"):
        transcript = TranscriptResult(**result)
        text_transcript = transcript.as_txt(prompt_speaker_labels=True)
        out_path = infile.parent / (infile.stem + " - transcript.txt")
        typer.echo(f"Writing transcript to {out_path}")
        with out_path.open("w") as outfile:
            outfile.write(text_transcript)


def save_json(file_path: Path, data):
    with file_path.open("w") as outfile:
        json.dump(data, outfile)


def get_assemblyai_key() -> str:
    if "ASSEMBLYAI_API_KEY" in os.environ:
        # Key already set. Do nothing.
        return os.environ["ASSEMBLYAI_API_KEY"]
    typer.echo("This tool requires a valid API key for AssemblyAI.")
    return typer.prompt("Enter your AssemblyAI API key")


def get_word_list() -> List[str]:
    words = []
    try:
        word = typer.prompt(
            "Enter a word to add it to the transcript priority wordlist.\n(Ctrl-C to quit)"
        )
        while word != "":
            words.append(word)
            word = typer.prompt("Enter another word. (Ctrl-C to quit)")
    except typer.Abort:
        typer.echo(tabulate({"Word List": words}, headers="keys"))
    return words


def assembly_banner():
    typer.echo(
        """┌──────────────────────────────┐
│                              │
│   AssemblyAI Transcription   │
│  by Teaching Python Podcast  │
│                              │
├──────────────────────────────┤
│      teachingpython.fm       │
│           @smtibor           │
└──────────────────────────────┘"""
    )
