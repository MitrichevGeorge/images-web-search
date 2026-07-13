from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .base import BaseImageMethod, MethodMeta
from .utils import HTTPClient


class WikimediaCommonsScraper(BaseImageMethod):
    meta = MethodMeta(
        name="Wikimedia Commons",
        category="Web Scraping",
        description="html5lib-робастный парсинг категорий Commons",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        url = f"https://commons.wikimedia.org/wiki/Category:{query.replace(' ', '_')}"
        response = HTTPClient.get(url, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html5lib")
        images: list[dict[str, Any]] = []

        for img in soup.find_all("img", src=True):
            src = img["src"]
            if src.startswith("//"):
                src = f"https:{src}"
            elif src.startswith("/"):
                src = f"https://commons.wikimedia.org{src}"

            if src.startswith("http"):
                images.append({"url": src})
            if len(images) >= limit:
                break

        return images
