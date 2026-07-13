from __future__ import annotations

from typing import Any

from .base import BaseImageMethod, MethodMeta
from .utils import HTTPClient


class ArtStationSearch(BaseImageMethod):
    meta = MethodMeta(
        name="ArtStation API",
        category="Free API",
        description="Художественные работы и концепт-арт с ArtStation",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        url = "https://www.artstation.com/projects.json"
        response = HTTPClient.get(url, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        images: list[dict[str, Any]] = []

        for item in data.get("data", [])[:limit]:
            cover = item.get("cover")
            if cover:
                images.append(
                    {
                        "title": item.get("title", ""),
                        "url": cover.get("small_square_url", ""),
                        "artist": item.get("user", {}).get("username", ""),
                    }
                )

        return images
