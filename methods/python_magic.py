from __future__ import annotations

from pathlib import Path
from typing import Any

import magic

from .base import BaseImageMethod, MethodMeta
from .utils import ensure_test_image


class PythonMagic(BaseImageMethod):
    meta = MethodMeta(
        name="Python-magic File Type",
        category="Image Analysis",
        description="Определение MIME-типа файла по его содержимому",
    )

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self.output_dir = Path(output_dir or "search_results") / "python_magic"

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        path = ensure_test_image(self.output_dir / "test.png")
        return [self.analyze(path)]

    def analyze(self, image_path: Path | str) -> dict[str, Any]:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(str(image_path))
        return {
            "mime_type": file_type,
            "is_image": file_type.startswith("image/"),
        }
