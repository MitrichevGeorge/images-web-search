from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .base import BaseImageMethod, MethodMeta


class AIOHTTPUrlValidator(BaseImageMethod):
    meta = MethodMeta(
        name="AIOHTTP URL Validator",
        category="Network",
        description="Асинхронная пакетная проверка HTTP-статуса URL",
    )

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        urls = self._build_urls(query, limit)
        return asyncio.run(self._validate(urls))

    def _build_urls(self, query: str, limit: int) -> list[str]:
        seed = query.replace(" ", "-")
        return [
            f"https://picsum.photos/seed/{seed}-{i}/800/600"
            for i in range(limit)
        ]

    async def _validate(self, urls: list[str]) -> list[dict[str, Any]]:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [self._check(session, url) for url in urls]
            return await asyncio.gather(*tasks)

    async def _check(self, session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
        try:
            async with session.head(url, allow_redirects=True) as resp:
                return {
                    "url": url,
                    "status": resp.status,
                    "content_type": resp.headers.get("Content-Type", ""),
                }
        except Exception as exc:
            return {"url": url, "error": f"{type(exc).__name__}: {exc}"}
