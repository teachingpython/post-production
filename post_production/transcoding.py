import logging
from pathlib import Path

import click
import ffmpeg

logger = logging.getLogger(__name__)


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("output_file", "--output", "-o", type=click.Path())
@click.option("intro_music", "--intro", type=click.Path(exists=True))
@click.option("outro_music", "--outro", type=click.Path(exists=True))
def transcode(
    input_file: str, output_file: str, intro_music: str = None, outro_music: str = None
):
    main_episode = ffmpeg.input(input_file)
    if intro_music:
        logger.info(f"Adding intro music from {intro_music}")
        intro = ffmpeg.input(intro_music)
        main_episode = ffmpeg.filter(
            [intro, main_episode], "acrossfade", d=4, c1="tri", c2="nofade"
        )
    if outro_music:
        logger.info(f"Adding outro music from {outro_music}")
        outro = ffmpeg.input(outro_music)
        main_episode = ffmpeg.filter(
            [main_episode, outro], "acrossfade", d=1, c1="nofade", c2="tri"
        )
    if output_file:
        output_path = Path(output_file)
    else:
        output_path = Path(input_file).name + ".mp3"

    logger.info(f"Processing file and writing to {output_path}")
    main_episode.output(str(output_path), ac=1, ab="160k", f="mp3").run()
