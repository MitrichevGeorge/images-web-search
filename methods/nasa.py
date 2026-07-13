from __future__ import annotations

from typing import Any

from .base import BaseImageMethod, MethodMeta
from .utils import HTTPClient


class NASASearch(BaseImageMethod):
    meta = MethodMeta(
        name="NASA Image API",
        category="Free API",
        description="Публичные космические снимки и фотографии NASA",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        url = "https://images-api.nasa.gov/search"
        params = {"q": query, "media_type": "image"}
        response = HTTPClient.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        images: list[dict[str, Any]] = []

        for item in data.get("collection", {}).get("items", [])[:limit]:
            links = item.get("links", [])
            metadata = item.get("data", [{}])[0]

            if links:
                images.append(
                    {
                        "title": metadata.get("title", ""),
                        "url": links[0].get("href", ""),
                        "description": metadata.get("description", ""),
                    }
                )

        return images
