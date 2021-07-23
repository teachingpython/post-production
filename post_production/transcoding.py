import logging
from pathlib import Path
from typing import Optional

import ffmpeg
import typer

logger = logging.getLogger(__name__)


def transcode(
    input_file: Path = typer.Argument(..., exists=True),
    output_file: Optional[Path] = typer.Option(
        None, help="Path to output file location"
    ),
    intro_music: Optional[Path] = typer.Option(
        None, exists=True, help="Intro music to add before file."
    ),
    outro_music: Optional[Path] = typer.Option(
        None, exists=True, help="Outro music to add after file."
    ),
):
    main_episode = ffmpeg.input(input_file)
    if intro_music:
        logger.info(f"Adding intro music from {intro_music}")
        intro = ffmpeg.input(intro_music).filter("loudnorm", i=-23, dual_mono="true")
        main_episode = ffmpeg.filter(
            [intro, main_episode], "acrossfade", d=4, c1="tri", c2="nofade"
        )
    if outro_music:
        logger.info(f"Adding outro music from {outro_music}")
        outro = ffmpeg.input(outro_music).filter("loudnorm", i=-23, dual_mono="true")
        main_episode = ffmpeg.filter(
            [main_episode, outro], "acrossfade", d=1, c1="nofade", c2="tri"
        )
    if output_file:
        output_path = Path(output_file)
    else:
        output_path = Path(input_file).stem + ".mp3"

    logger.info(f"Processing file and writing to {output_path}")
    main_episode.output(str(output_path), ac=1, ab="160k", f="mp3").run()
