import logging
import os
import time
from pathlib import Path

import click

from post_production.dolby import DolbyIO, JobType


@click.command()
@click.argument("infile", type=click.Path())
@click.option("output", "--output", "-o", default=None, type=click.Path())
@click.option("analyze", "--analyze", "-a", is_flag=True, default=False)
@click.option("analyze_speech", "--analyze-speech", is_flag=True, default=False)
def enhance(infile, output, analyze, analyze_speech):
    banner()
    infile = Path(infile)

    # Make sure we have a valid Dolby API key
    API_KEY = get_dolby_key()
    dolby = DolbyIO(API_KEY)

    if not click.confirm(
        f"Are you ready to upload {infile.name}? You may incur costs.", default=True
    ):
        click.echo("Aborting. Goodbye")
        return

    click.echo(f"Uploading {infile}...")
    in_url = dolby.upload(infile)

    if analyze:
        click.echo(f"Analyzing {in_url}...")
        job_id, out_url = dolby.analyze(in_url)
        job_type = JobType.ANALYZE
    elif analyze_speech:
        click.echo(f"Analyzing speech in {in_url}...")
        job_id, out_url = dolby.analyze(in_url, speech=True)
        job_type = JobType.SPEECH_ANALYZE
    else:
        click.echo(f"Processing {in_url}...")
        job_id, out_url = dolby.enhance(in_url)
        job_type = JobType.ENHANCE

    display_status(dolby, job_id, job_type)

    if output:
        out_path = Path(output)
    else:
        out_path = infile.parent / "output"
    click.echo(f"Downloading file from {out_url} to {out_path}")
    file_path = dolby.download(out_url=out_url, out_path=out_path, job_type=job_type)
    click.echo(f"File {infile} processed and saved to {file_path}")


def banner():
    click.echo(
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

    click.echo("This tool requires a valid API key for Dolby.io.")
    return click.prompt("Enter your Dolby.io API key")


def display_status(dolby, job_id, job_type):
    status, pct = dolby.get_status(job_id, job_type=job_type)
    last_pct = 0
    with click.progressbar(
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
