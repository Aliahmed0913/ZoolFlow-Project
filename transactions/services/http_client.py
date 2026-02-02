import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_session_with_retries():
    max_retry = Retry(
        total=3,
        # backoff_seconds = backoff_factor * (2 ** (retry_number - 1))
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504, 429],
        allowed_methods=["POST"],
    )

    adapter = HTTPAdapter(max_retries=max_retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
