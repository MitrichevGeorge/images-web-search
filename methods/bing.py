from __future__ import annotations

from pathlib import Path
from typing import Any

from bing_image_downloader import downloader as bing_downloader

from .base import BaseImageMethod, MethodMeta


class BingImageDownloader(BaseImageMethod):
    meta = MethodMeta(
        name="Bing Image Downloader",
        category="Search Engine",
        description="Локальное скачивание изображений из Bing",
    )

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self.output_dir = Path(output_dir or "search_results") / "bing_downloader"

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        safe_query = query.replace(" ", "_")
        target_dir = self.output_dir / safe_query
        target_dir.mkdir(parents=True, exist_ok=True)
        bing_downloader.download(
            query,
            limit=limit,
            output_dir=str(target_dir),
            timeout=int(self.timeout),
            verbose=False,
        )

        files: list[Path] = []
        for pattern in ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp"):
            files.extend(target_dir.rglob(pattern))

        return [{"path": str(f), "filename": f.name} for f in files]
