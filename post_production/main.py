import logging
import os
import time
from datetime import datetime
from pathlib import Path

import typer
from dotenv import load_dotenv

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)


app = typer.Typer()
from post_production import assembly_ai_cli, dolby_cli, transcoding


@app.callback()
def cli():
    load_dotenv()
    logging.basicConfig(
        filename=log_dir / f"job_logs_{datetime.now().isoformat()}.log",
        level=logging.INFO,
    )
