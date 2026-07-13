from __future__ import annotations

from typing import Any

from .base import BaseImageMethod, MethodMeta
from .utils import HTTPClient


class LoremPicsum(BaseImageMethod):
    meta = MethodMeta(
        name="Lorem Picsum",
        category="Free API",
        description="Случайные изображения для прототипов и тестов",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        url = f"https://picsum.photos/v2/list?page=1&limit={limit}"
        response = HTTPClient.get(url, timeout=self.timeout)
        response.raise_for_status()

        photos = response.json()
        return [
            {
                "id": photo.get("id", ""),
                "url": f"https://picsum.photos/id/{photo.get('id')}/800/600",
                "author": photo.get("author", ""),
                "download_url": photo.get("download_url", ""),
            }
            for photo in photos
        ]
