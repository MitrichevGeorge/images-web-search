from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from .base import BaseImageMethod, MethodMeta
from .utils import ensure_test_image


class PILAnalysis(BaseImageMethod):
    meta = MethodMeta(
        name="PIL Image Analysis",
        category="Image Analysis",
        description="Анализ формата, размера и режима через Pillow",
    )

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self.output_dir = Path(output_dir or "search_results") / "pil_analysis"

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        path = ensure_test_image(self.output_dir / "test.png")
        return [self.analyze(path)]

    def analyze(self, image_path: Path | str) -> dict[str, Any]:
        with Image.open(image_path) as img:
            return {
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
            }
