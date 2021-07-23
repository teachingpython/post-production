import logging
import os
import time
from pathlib import Path

import typer

from post_production.dolby import DolbyIO, JobType
from post_production.main import app


@app.command()
def enhance(
    infile: Path = typer.Argument(..., help="Input file"),
    output: Path = typer.Option(None, help="Output file."),
    analyze: bool = typer.Option(False, help="Analyze audio"),
    analyze_speech: bool = typer.Option(False, help="Use Dolby speech analysis."),
):
    banner()

    # Make sure we have a valid Dolby API key
    API_KEY = get_dolby_key()
    dolby = DolbyIO(API_KEY)

    if not typer.confirm(
        f"Are you ready to upload {infile.name}? You may incur costs.", default=True
    ):
        typer.echo("Aborting. Goodbye")
        return

    typer.echo(f"Uploading {infile}...")
    in_url = dolby.upload(infile)

    if analyze:
        typer.echo(f"Analyzing {in_url}...")
        job_id, out_url = dolby.analyze(in_url)
        job_type = JobType.ANALYZE
    elif analyze_speech:
        typer.echo(f"Analyzing speech in {in_url}...")
        job_id, out_url = dolby.analyze(in_url, speech=True)
        job_type = JobType.SPEECH_ANALYZE
    else:
        typer.echo(f"Processing {in_url}...")
        job_id, out_url = dolby.enhance(in_url)
        job_type = JobType.ENHANCE

    display_status(dolby, job_id, job_type)

    if output:
        out_path = Path(output)
    else:
        out_path = infile.parent / "output"
    typer.echo(f"Downloading file from {out_url} to {out_path}")
    file_path = dolby.download(out_url=out_url, out_path=out_path, job_type=job_type)
    typer.echo(f"File {infile} processed and saved to {file_path}")


def banner():
    typer.echo(
        """┌──────────────────────────────┐
│                              │
│    Dolby Audio Processing    │
│  by Teaching Python Podcast  │
│                              │
├──────────────────────────────┤
│      teachingpython.fm       │
│           @smtibor           │
└──────────────────────────────┘"""
    )


def get_dolby_key() -> str:
    if "DOLBY_API_KEY" in os.environ:
        # Key already set. Do nothing.
        return os.environ["DOLBY_API_KEY"]

    typer.echo("This tool requires a valid API key for Dolby.io.")
    return typer.prompt("Enter your Dolby.io API key")


def display_status(dolby, job_id, job_type):
    status, pct = dolby.get_status(job_id, job_type=job_type)
    last_pct = 0
    with typer.progressbar(
        length=100, label="Processing file", show_percent=True
    ) as bar:
        while pct < 100:
            status, pct = dolby.get_status(job_id, job_type=job_type)
            if pct > last_pct:
                bar.update(pct - last_pct)
                last_pct = pct
            if status not in ("Pending", "Running"):
                break
            time.sleep(1)
