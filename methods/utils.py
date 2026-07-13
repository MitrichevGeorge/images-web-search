from __future__ import annotations

from pathlib import Path
from typing import Any

import requests


class HTTPClient:
    _USER_AGENT: str = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )

    @classmethod
    def get(
        cls,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        merged_headers = {"User-Agent": cls._USER_AGENT}
        if headers:
            merged_headers.update(headers)
        return requests.get(url, params=params, headers=merged_headers, timeout=timeout)


def ensure_test_image(
    path: Path,
    *,
    size: tuple[int, int] = (200, 150),
    image_format: str = "PNG",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path

    from PIL import Image

    width, height = size
    image = Image.new("RGB", (width, height))
    pixels = [
        ((x * 255) // max(width - 1, 1), (y * 255) // max(height - 1, 1), 128)
        for y in range(height)
        for x in range(width)
    ]
    image.putdata(pixels)
    image.save(path, image_format)
    return path
