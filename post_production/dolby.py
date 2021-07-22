import logging
import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import quote, unquote

import requests

logger = logging.getLogger(__name__)

API_KEY = os.environ["DOLBY_API_KEY"]


class JobType(Enum):
    ENHANCE = "enhance"
    ANALYZE = "analyze"
    DIAGNOSE = "diagnose"
    SPEECH_ANALYZE = "analyze/speech"
    UPLOAD = "input"
    DOWNLOAD = "output"


def endpoint(job_type: JobType) -> str:
    return f"https://api.dolby.com/media/{job_type.value}"


def upload(file_path: Path) -> str:
    """For a given file, upload it and return a Dolby-compatible url

    Args:
        in_file (Path): path to local file

    Returns:
        str: string to remote path
    """
    url = endpoint(JobType.UPLOAD)
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    in_url = f"dlb://in/{quote(file_path.name)}"

    body = {
        "url": in_url,
    }

    r = requests.post(url, json=body, headers=headers)
    r.raise_for_status()
    logger.info(f"Created endpoint for {in_url}")
    data = r.json()
    presigned_url = data["url"]
    # Upload your media to the pre-signed url response

    with open(file_path, "rb") as input_file:
        requests.put(presigned_url, data=input_file)

    logger.info(f"Uploaded {file_path.name} to {in_url}")
    return in_url


def enhance(in_url: str, out_url: Optional[str] = None) -> Tuple[str, str]:
    """Process an uploaded url and return a file once completed

    Args:
        in_url (str): path to Dolby-compatible file

    Returns:
        str: path to processed file
    """
    out_url = in_url.replace("dlb://in/", "dlb://out/")

    body = {
        "content": {"type": "interview"},
        "audio": {
            "loudness": {"enable": True, "dialog_intelligence": True},
            "dynamics": {"range_control": {"enable": True}},
            "noise": {"reduction": {"enable": True}},
            "filter": {
                "dynamic_eq": {"enable": True},
                "high_pass": {"enable": True},
            },
        },
        "input": in_url,
        "output": out_url,
    }

    url = endpoint(JobType.ENHANCE)
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    logger.info(f"Beginning enhancement for {in_url}")
    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()

    job_id = response.json().get("job_id")
    logger.info(f"Created enhancement job {job_id} with expected output {out_url}")

    return job_id, out_url


def analyze(
    in_url: str, out_url: Optional[str] = None, speech: bool = False
) -> Tuple[str, str]:
    """Analyzes an uploaded url and returns a json file once completed

    Args:
        in_url (str): path to Dolby-compatible file
        out_url (str): path to JSON analysis report

    Returns:
        str: path to json analysis
    """
    out_frags = in_url.split(".")[:-1]
    out_frags.append("json")
    out_url = ".".join(out_frags).replace("dlb://in/", "dlb://out/")

    body = {
        "input": in_url,
        "output": out_url,
    }
    if speech:
        url = endpoint(JobType.SPEECH_ANALYZE)
        logger.info(f"Beginning speech analysis for {in_url}")
    else:
        url = endpoint(JobType.ANALYZE)
        logger.info(f"Beginning analysis for {in_url}")
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    job_id = response.json().get("job_id")

    return job_id, out_url


def get_status(job_id: str, job_type: JobType = JobType.ENHANCE) -> Tuple[str, int]:
    url = endpoint(job_type)
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    params = {"job_id": job_id}

    r = requests.get(url, params=params, headers=headers)
    r.raise_for_status()
    data = r.json()
    return data.get("status"), data.get("progress")


def download(
    out_url: str, out_path: Optional[Path] = None, job_type: JobType = JobType.ENHANCE
):
    if not out_path:
        out_path = Path(__file__).parent / "output"

    if job_type == JobType.ANALYZE:
        file_tag = " - Analyzed"
    elif job_type == JobType.SPEECH_ANALYZE:
        file_tag = " - Speech Analyzed"
    else:
        file_tag = " - Enhanced"

    filename = unquote(out_url.split("/")[-1])
    out_file = out_path / (Path(filename).stem + file_tag + Path(filename).suffix)
    out_path.mkdir(parents=True, exist_ok=True)

    url = endpoint(JobType.DOWNLOAD)
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    args = {
        "url": out_url,
    }
    logger.info(f"Downloading file from {out_url} to {out_file}")
    with requests.get(url, params=args, headers=headers, stream=True) as response:
        response.raise_for_status()
        response.raw.decode_content = True
        logger.info(f"Downloading from {out_url} into {out_file}")
        with open(out_file, "wb") as output_file:
            shutil.copyfileobj(response.raw, output_file)

    return out_file
