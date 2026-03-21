import importlib.metadata
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from post_production import assembly_ai_cli, dolby_cli, transcoding

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

app = typer.Typer()
app.command()(dolby_cli.enhance)
app.command()(assembly_ai_cli.transcribe)
app.command()(assembly_ai_cli.chapters)
app.command()(transcoding.transcode)
app.command()(assembly_ai_cli.retrieve)

__version__ = importlib.metadata.version("post-production")


def version_callback(value: bool):
    if value:
        typer.echo(f"{__version__}")
        raise typer.Exit()


@app.callback()
def cli(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    )
):
    load_dotenv()
    logging.basicConfig(
        filename=log_dir / f"job_logs_{datetime.now().isoformat()}.log",
        level=logging.INFO,
    )
