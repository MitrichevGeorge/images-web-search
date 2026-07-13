from __future__ import annotations

from typing import Any

from .base import BaseImageMethod, MethodMeta
from .utils import HTTPClient


class WikimediaAPI(BaseImageMethod):
    meta = MethodMeta(
        name="Wikimedia API (httpx)",
        category="Network",
        description="Запрос к Wikimedia Commons API через MediaWiki search",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        url = (
            "https://commons.wikimedia.org/w/api.php"
            f"?action=query&format=json&generator=search"
            f"&gsrnamespace=6&gsrlimit={limit}&gsrsearch={query}"
            f"&prop=imageinfo&iiprop=url"
        )
        response = HTTPClient.get(url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        images: list[dict[str, Any]] = []
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            for info in page.get("imageinfo", []):
                images.append(
                    {
                        "url": info.get("url", ""),
                        "title": page.get("title", ""),
                        "pageid": page_id,
                    }
                )

        return images
