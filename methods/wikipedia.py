from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .base import BaseImageMethod, MethodMeta
from .utils import HTTPClient


class WikipediaScraper(BaseImageMethod):
    meta = MethodMeta(
        name="Wikipedia Scraping",
        category="Web Scraping",
        description="requests + BeautifulSoup для извлечения картинок из Wikipedia",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        term = query.split()[0] if query else "nature"
        url = f"https://en.wikipedia.org/wiki/{term}"
        response = HTTPClient.get(url, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        images: list[dict[str, Any]] = []

        for img in soup.find_all("img", src=True):
            src = img["src"]
            if src.startswith("//"):
                src = f"https:{src}"
            elif src.startswith("/") and not src.startswith("//"):
                src = f"https://en.wikipedia.org{src}"

            if src.startswith("http"):
                images.append(
                    {
                        "url": src,
                        "alt": img.get("alt", ""),
                        "title": img.get("title", ""),
                    }
                )
            if len(images) >= limit:
                break

        return images
