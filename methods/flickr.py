from __future__ import annotations

from typing import Any

import lxml.html

from .base import BaseImageMethod, MethodMeta
from .utils import HTTPClient


class FlickrScraper(BaseImageMethod):
    meta = MethodMeta(
        name="Flickr Search",
        category="Web Scraping",
        description="lxml-парсинг результатов поиска Flickr",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        url = f"https://www.flickr.com/search/?text={query.replace(' ', '+')}"
        response = HTTPClient.get(url, timeout=self.timeout)
        response.raise_for_status()

        tree = lxml.html.fromstring(response.content)
        images: list[dict[str, Any]] = []

        for img in tree.xpath("//img[@src]"):
            src = img.get("src", "")
            if src.startswith("http"):
                images.append(
                    {
                        "url": src,
                        "alt": img.get("alt", ""),
                    }
                )
            if len(images) >= limit:
                break

        return images
