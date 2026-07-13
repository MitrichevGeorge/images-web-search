from __future__ import annotations

from pathlib import Path
from typing import Any

import imageio.v2 as imageio

from .base import BaseImageMethod, MethodMeta
from .utils import ensure_test_image


class ImageIOOperations(BaseImageMethod):
    meta = MethodMeta(
        name="ImageIO Operations",
        category="Image Analysis",
        description="Чтение и базовая информация об изображении через imageio",
    )

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self.output_dir = Path(output_dir or "search_results") / "imageio_ops"

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        path = ensure_test_image(self.output_dir / "test.png")
        return [self.analyze(path)]

    def analyze(self, image_path: Path | str) -> dict[str, Any]:
        img = imageio.imread(image_path)
        return {
            "shape": img.shape,
            "dtype": str(img.dtype),
        }
