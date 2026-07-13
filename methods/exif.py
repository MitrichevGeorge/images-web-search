from __future__ import annotations

from pathlib import Path
from typing import Any

import exifread

from .base import BaseImageMethod, MethodMeta
from .utils import ensure_test_image


class ExifReader(BaseImageMethod):
    meta = MethodMeta(
        name="EXIF Metadata Reading",
        category="Image Analysis",
        description="Чтение метаданных EXIF через exifread",
    )

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self.output_dir = Path(output_dir or "search_results") / "exif_reader"

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        path = ensure_test_image(self.output_dir / "test.jpg", image_format="JPEG")
        return [self.analyze(path)]

    def analyze(self, image_path: Path | str) -> dict[str, Any]:
        with open(image_path, "rb") as file:
            tags = exifread.process_file(file)
        return {str(tag): str(value) for tag, value in tags.items()}
