import logging
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple
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

    @staticmethod
    def endpoint(job_type: JobType) -> str:
        return f"https://api.dolby.com/media/{job_type.value}"

    def upload(self, file_path: Path) -> str:
        """For a given file, upload it and return a Dolby-compatible url.

        Args:
            file_path (Path): path to local file

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
        logger.info("Created endpoint for %s", in_url)

        data = r.json()
        presigned_url = data["url"]

        with open(file_path, "rb") as input_file:
            self._session.put(presigned_url, data=input_file)

        logger.info("Uploaded %s to %s", file_path.name, in_url)
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
        """Process an uploaded url and return a file once completed.

        Args:
            in_url: path to Dolby-compatible file.
            out_url: Optional path to destination url.
            content_type: Set content type for processing. Defaults to "interview".

        Raises:
            InvalidURL: If a valid output url cannot be generated
            ValueError: Checks for valid content types

        Returns:
            A tuple of the job-id and output url
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

        logger.info("Beginning enhancement for %s", in_url)
        response = self._session.post(url, json=body)
        response.raise_for_status()

        job_id = response.json().get("job_id")
        logger.info(
            "Created enhancement job %s with expected output %s", job_id, out_url
        )

        return job_id, out_url

    def analyze(
        self, in_url: str, out_url: Optional[str] = None, speech: bool = False
    ) -> Tuple[str, str]:
        """Analyzes an uploaded url and returns a json file once completed.

        Args:
            in_url: path to Dolby-compatible file
            out_url: path to JSON analysis report

        Returns:
            Tuple of job_id and out_url
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
            logger.info("Beginning speech analysis for %s", in_url)
        else:
            url = self.endpoint(JobType.ANALYZE)
            logger.info("Beginning analysis for %s", in_url)

        response = self._session.post(url, json=body)
        response.raise_for_status()
        job_id = response.json().get("job_id")

        return job_id, out_url

    def get_status(
        self, job_id: str, job_type: JobType = JobType.ENHANCE
    ) -> Tuple[str, int]:
        """Get the current job status on Dolby.io for the given job id.

        Args:
            job_id: A valid job_id from the dolby.io website
            job_type: The type of job to monitor. Defaults to JobType.ENHANCE.

        Returns:
            A tuple containing the job status and percent complete.
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
        """Download files from the Dolby.io Media endpoints.

        Args:
            out_url: The path to the dolby.io media
            out_path: The folder to save the file. Defaults to output/ under cwd.
            job_type: The job type for naming conventions.

        Returns:
            The pathlib path to the downloaded file
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
        logger.info("Downloading file from %s to %s", out_url, out_file)
        with self._session.get(url, params=args, stream=True) as response:
            response.raise_for_status()
            response.raw.decode_content = True
            with open(out_file, "wb") as output_file:
                shutil.copyfileobj(response.raw, output_file)

        return out_file
