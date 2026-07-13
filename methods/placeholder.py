from __future__ import annotations

from typing import Any

import requests

from .base import BaseImageMethod, MethodMeta
from .utils import HTTPClient


class PlaceholderImages(BaseImageMethod):
    meta = MethodMeta(
        name="Placeholder APIs",
        category="Free API",
        description="Тестовые placeholder-сервисы: via.placeholder, placehold.co, placekitten",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        text = query.replace(" ", "+")
        services = [
            f"https://via.placeholder.com/800x600?text={text}",
            f"https://placehold.co/800x600?text={text}",
            "https://placekitten.com/800/600",
        ]

        images: list[dict[str, Any]] = []
        for url in services[:limit]:
            try:
                response = requests.head(
                    url,
                    timeout=10,
                    headers={"User-Agent": HTTPClient._USER_AGENT},
                    allow_redirects=True,
                )
                images.append(
                    {
                        "url": url,
                        "status": response.status_code,
                        "available": response.status_code == 200,
                    }
                )
            except Exception as exc:
                images.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})

        return images
