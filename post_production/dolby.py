import logging
import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple, Union
from urllib.parse import quote, unquote

import requests
from requests.models import InvalidURL

logger = logging.getLogger(__name__)


class JobType(Enum):
    ENHANCE = "enhance"
    ANALYZE = "analyze"
    DIAGNOSE = "diagnose"
    SPEECH_ANALYZE = "analyze/speech"
    UPLOAD = "input"
    DOWNLOAD = "output"


CONTENT_TYPES = {
    "conference",
    "interview",
    "lecture",
    "meeting",
    "mobile_phone",
    "music",
    "podcast",
    "studio",
    "voice_over",
    "voice_recording",
}


class DolbyIO:
    def __init__(self, api_key: str):
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._session = requests.Session()
        self._session.headers.update(headers)
        self._api_key = api_key

    @staticmethod
    def endpoint(job_type: JobType) -> str:
        return f"https://api.dolby.com/media/{job_type.value}"

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, key):
        self._api_key = key
        self._session.headers["x-api-key"] = key

    def upload(self, file_path: Path) -> str:
        """For a given file, upload it and return a Dolby-compatible url

        Args:
            in_file (Path): path to local file

        Returns:
            str: string to remote path
        """
        url = self.endpoint(JobType.UPLOAD)

        in_url = f"dlb://in/{quote(file_path.name)}"

        body = {
            "url": in_url,
        }

        r = self._session.post(url, json=body)
        r.raise_for_status()
        logger.info(f"Created endpoint for {in_url}")

        data = r.json()
        presigned_url = data["url"]
        # Upload your media to the pre-signed url response

        with open(file_path, "rb") as input_file:
            self._session.put(presigned_url, data=input_file)

        logger.info(f"Uploaded {file_path.name} to {in_url}")
        return in_url

    def enhance(
        self,
        in_url: str,
        out_url: Optional[str] = None,
        loudness: bool = True,
        loudness_target: float = -23.0,
        dialog_intelligence: bool = True,
        dynamic_range_control: bool = True,
        dynamic_range_control_amount: str = "medium",
        noise_reduction: bool = True,
        noise_reduction_amount: str = "auto",
        dynamic_eq: bool = True,
        high_pass_filter: bool = True,
        content_type: str = "interview",
    ) -> Tuple[str, str]:
        """Process an uploaded url and return a file once completed

        Args:
            in_url (str): path to Dolby-compatible file. Can be a Dolby Input file or other S3-compatible storage links
            out_url (Optional[str], optional): Optional path to destination url. If not provided, it will attempt to generate a dolby output url
            loudness (bool, optional): Enable loudness correction. Defaults to True.
            loudness_target (float, optional): Target loudness level. Defaults to -23.0.
            dialog_intelligence (bool, optional): Use voice gating for loudness. Defaults to True.
            dynamic_range_control (bool, optional): Enable Dynamic Range control. Defaults to True.
            dynamic_range_control_amount (str, optional): Amount of Dynamic Range control to apply. Defaults to "medium".
            noise_reduction (bool, optional): Enable Noise Reduction. Defaults to True.
            noise_reduction_amount (str, optional): Amount to apply. Defaults to "auto".
            dynamic_eq (bool, optional): Enable Dynamic EQ filtering. Defaults to True.
            high_pass_filter (bool, optional): Enable High Pass filtering. Defaults to True.
            content_type (str, optional): Set content type for processing. Defaults to "interview".

        Raises:
            InvalidURL: If a valid output url cannot be generated
            ValueError: Checks for valid content types

        Returns:
            Tuple[str, str]: A tuple of the job-id and output url
        """

        if in_url.startswith("dlb://"):
            out_url = in_url.replace("dlb://in/", "dlb://out/")
        elif not out_url:
            raise InvalidURL(
                "in_url is not a Dolby-provided URL and an out_url was not provided."
            )

        if content_type not in CONTENT_TYPES:
            raise ValueError(
                f'Content type must be a valid type for dolby.io. "{content_type}" is not valid.'
            )

        body = {
            "content": {"type": content_type},
            "audio": {
                "loudness": {
                    "enable": loudness,
                    "dialog_intelligence": dialog_intelligence,
                    "target_level": loudness_target,
                },
                "dynamics": {
                    "range_control": {
                        "enable": dynamic_range_control,
                        "amount": dynamic_range_control_amount,
                    }
                },
                "noise": {
                    "reduction": {
                        "enable": noise_reduction,
                        "amount": noise_reduction_amount,
                    }
                },
                "filter": {
                    "dynamic_eq": {"enable": dynamic_eq},
                    "high_pass": {"enable": high_pass_filter},
                },
            },
            "input": in_url,
            "output": out_url,
        }

        url = self.endpoint(JobType.ENHANCE)

        logger.info(f"Beginning enhancement for {in_url}")
        response = self._session.post(url, json=body)
        response.raise_for_status()

        job_id = response.json().get("job_id")
        logger.info(f"Created enhancement job {job_id} with expected output {out_url}")

        return job_id, out_url

    def analyze(
        self, in_url: str, out_url: Optional[str] = None, speech: bool = False
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
            url = self.endpoint(JobType.SPEECH_ANALYZE)
            logger.info(f"Beginning speech analysis for {in_url}")
        else:
            url = self.endpoint(JobType.ANALYZE)
            logger.info(f"Beginning analysis for {in_url}")

        response = self._session.post(url, json=body)
        response.raise_for_status()
        job_id = response.json().get("job_id")

        return job_id, out_url

    def get_status(
        self, job_id: str, job_type: JobType = JobType.ENHANCE
    ) -> Tuple[str, int]:
        """Get the current job status on Dolby.io for the given job id.

        Args:
            job_id (str): A valid job_id from the dolby.io website
            job_type (JobType, optional): The type of job to monitor. Defaults to JobType.ENHANCE.

        Returns:
            Tuple[str, int]: A tuple containing the job status and percent complete, e.g. ("Running", 19)
        """
        url = self.endpoint(job_type)

        params = {"job_id": job_id}

        r = self._session.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return data.get("status"), data.get("progress")

    def download(
        self,
        out_url: str,
        out_path: Optional[Path] = None,
        job_type: JobType = JobType.ENHANCE,
    ) -> Path:
        """Download files from the Dolby.io Media endpoints

        Args:
            out_url (str): The path to the dolby.io media
            out_path (Optional[Path], optional): The folder to save the file. Defaults to output/ under the current working directory.
            job_type (JobType, optional): The job type for naming conventions. Defaults to JobType.ENHANCE.

        Returns:
            [Path]: The pathlib link to the downloaded file
        """
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

        url = self.endpoint(JobType.DOWNLOAD)

        args = {
            "url": out_url,
        }
        logger.info(f"Downloading file from {out_url} to {out_file}")
        with self._session.get(url, params=args, stream=True) as response:
            response.raise_for_status()
            response.raw.decode_content = True
            logger.info(f"Downloading from {out_url} into {out_file}")
            with open(out_file, "wb") as output_file:
                shutil.copyfileobj(response.raw, output_file)

        return out_file
