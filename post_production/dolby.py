import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import quote, unquote

import requests

logger = logging.getLogger(__name__)

API_KEY = os.environ["DOLBY_API_KEY"]


def upload(file_path: Path) -> str:
    """For a given file, upload it and return a Dolby-compatible url

    Args:
        in_file (Path): path to local file

    Returns:
        str: string to remote path
    """
    url = "https://api.dolby.com/media/input"
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
    data = r.json()
    presigned_url = data["url"]
    # Upload your media to the pre-signed url response

    with open(file_path, "rb") as input_file:
        requests.put(presigned_url, data=input_file)

    return in_url


def process(in_url: str) -> Tuple[str, str]:
    """Process an uploaded url and return a file once completed

    Args:
        in_url (str): path to Dolby-compatible file

    Returns:
        str: path to processed file
    """
    out_url = in_url.replace("dlb://in/", "dlb://out/")

    body = {
        "input": in_url,
        "output": out_url,
        "content": {"type": "podcast"},
        "audio": {
            "loudness": {"enable": True, "dialog_intelligence": True},
            "dynamics": {"range_control": {"enable": True, "amount": "medium"}},
            "noise": {"reduction": {"enable": True}},
        },
    }
    url = "https://api.dolby.com/media/enhance"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    job_id = response.json().get("job_id")

    return job_id, out_url


def get_status(job_id: str) -> Tuple[str, int]:
    url = "https://api.dolby.com/media/enhance"
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


def download(out_url: str, out_path: Optional[Path] = None):
    if not out_path:
        out_path = Path(__file__).parent / "output"

    filename = unquote(out_url.split("/")[-1])
    out_file = out_path / (Path(filename).stem + " - Enhanced" + Path(filename).suffix)
    out_path.mkdir(parents=True, exist_ok=True)

    url = "https://api.dolby.com/media/output"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    args = {
        "url": out_url,
    }

    with requests.get(url, params=args, headers=headers, stream=True) as response:
        response.raise_for_status()
        response.raw.decode_content = True
        print(f"Downloading from {out_url} into {out_file}")
        with open(out_file, "wb") as output_file:
            shutil.copyfileobj(response.raw, output_file)

    return out_file
