from __future__ import annotations

from pathlib import Path
from typing import Any

from icrawler.builtin import BingImageCrawler

from .base import BaseImageMethod, MethodMeta


class ICrawlerBing(BaseImageMethod):
    meta = MethodMeta(
        name="iCrawler Bing Images",
        category="Crawler",
        description="Bing Images crawler — стабильный способ массового скачивания",
    )

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self.output_dir = Path(output_dir or "search_results") / "icrawler_bing"

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        safe_query = query.replace(" ", "_")
        target_dir = self.output_dir / safe_query
        target_dir.mkdir(parents=True, exist_ok=True)
        crawler = BingImageCrawler(storage={"root_dir": str(target_dir)})
        crawler.crawl(keyword=query, max_num=limit, min_size=(100, 100))

        files: list[Path] = []
        for pattern in ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp"):
            files.extend(target_dir.glob(pattern))

        return [{"path": str(f), "filename": f.name} for f in files]
