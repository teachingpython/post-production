import logging
import os
import time
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from post_production.assembly_ai import AssemblyAI
from post_production.assembly_ai_cli import transcribe
from post_production.dolby_cli import enhance
from post_production.transcoding import transcode

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)


@click.group()
def cli():
    load_dotenv()
    logging.basicConfig(
        filename=log_dir / f"job_logs_{datetime.now().isoformat()}.log",
        level=logging.INFO,
    )


cli.add_command(enhance)
cli.add_command(transcribe)
cli.add_command(transcode)
