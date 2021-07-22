import time
from pathlib import Path

import click

from post_production import dolby


@click.command()
@click.argument("infile", type=Path)
@click.option("--output", "-o", default=None, type=Path)
def process(infile, output=None):
    click.echo(f"Uploading {infile}...")
    in_url = dolby.upload(infile)
    click.echo(f"Processing {in_url}...")
    job_id, out_url = dolby.process(in_url)
    status, pct = dolby.get_status(job_id)
    with click.progressbar(
        length=100, label="Processing file", show_percent=True
    ) as bar:
        while pct < 100:
            status, pct = dolby.get_status(job_id)
            bar.update(pct)
            if status != "Running":
                break
            time.sleep(1)
        bar.update(pct)
    out_path = infile.parent / "output"
    file_path = dolby.download(out_url=out_url, out_path=out_path)
    click.echo(f"File {infile} processed and saved to {file_path}")
