from __future__ import annotations

from typing import Any

from ddgs import DDGS

from .base import BaseImageMethod, MethodMeta


class DuckDuckGoImages(BaseImageMethod):
    meta = MethodMeta(
        name="DuckDuckGo Image Search",
        category="Search Engine",
        description="Поиск изображений через официальный DDGS API",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=limit))

        return [
            {
                "title": r.get("title", ""),
                "image_url": r.get("image", ""),
                "source": r.get("source", ""),
                "thumbnail": r.get("thumbnail", ""),
            }
            for r in results
        ]


class DuckDuckGoText(BaseImageMethod):
    meta = MethodMeta(
        name="DuckDuckGo Text Search",
        category="Search Engine",
        description="Текстовый поиск DDGS, заточенный под картинки",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} image", max_results=limit))

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
