from __future__ import annotations

from typing import Any

from .base import BaseImageMethod, MethodMeta
from .utils import HTTPClient


class MetMuseumSearch(BaseImageMethod):
    meta = MethodMeta(
        name="Met Museum API",
        category="Free API",
        description="Произведения искусства из Met Museum (Public Domain/CC0)",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
        response = HTTPClient.get(search_url, params={"q": query}, timeout=self.timeout)
        response.raise_for_status()

        object_ids = response.json().get("objectIDs", [])[:limit]
        images: list[dict[str, Any]] = []

        for obj_id in object_ids:
            obj_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}"
            obj_response = HTTPClient.get(obj_url, timeout=self.timeout)
            if obj_response.status_code != 200:
                continue

            obj_data = obj_response.json()
            if obj_data.get("primaryImage"):
                images.append(
                    {
                        "title": obj_data.get("title", ""),
                        "url": obj_data.get("primaryImage", ""),
                        "artist": obj_data.get("artistDisplayName", ""),
                    }
                )

        return images
