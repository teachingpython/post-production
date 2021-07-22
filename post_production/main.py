import logging
import time
from pathlib import Path

import click

from post_production import dolby

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)


@click.command()
@click.argument("infile", type=click.Path())
@click.option("output", "--output", "-o", default=None, type=click.Path())
@click.option("analyze", "--analyze", "-a", is_flag=True, default=False)
@click.option("analyze_speech", "--analyze-speech", is_flag=True, default=False)
def process(infile, output, analyze, analyze_speech):
    infile = Path(infile)
    logging.basicConfig(
        filename=log_dir / f"job_logs_{infile.name}.log", level=logging.INFO
    )
    click.echo(f"Uploading {infile}...")
    in_url = dolby.upload(infile)

    if analyze:
        click.echo(f"Analyzing {in_url}...")
        job_id, out_url = dolby.analyze(in_url)
        job_type = dolby.JobType.ANALYZE
    elif analyze_speech:
        click.echo(f"Analyzing speech in {in_url}...")
        job_id, out_url = dolby.analyze(in_url, speech=True)
        job_type = dolby.JobType.SPEECH_ANALYZE
    else:
        click.echo(f"Processing {in_url}...")
        job_id, out_url = dolby.enhance(in_url)
        job_type = dolby.JobType.ENHANCE

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

    if output:
        out_path = Path(output)
    else:
        out_path = infile.parent / "output"
    click.echo(f"Downloading file from {out_url} to {out_path}")
    file_path = dolby.download(out_url=out_url, out_path=out_path, job_type=job_type)
    click.echo(f"File {infile} processed and saved to {file_path}")
