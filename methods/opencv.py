from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2

from .base import BaseImageMethod, MethodMeta
from .utils import ensure_test_image


class OpenCVDetection(BaseImageMethod):
    meta = MethodMeta(
        name="OpenCV Detection",
        category="Image Analysis",
        description="Детекция краёв Canny и обработка через OpenCV",
    )

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self.output_dir = Path(output_dir or "search_results") / "opencv"

    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        path = ensure_test_image(self.output_dir / "test.png")
        return [self.analyze(path)]

    def analyze(self, image_path: Path | str) -> dict[str, Any]:
        img = cv2.imread(str(image_path))
        if img is None:
            return {"error": "Failed to load image"}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)

        return {
            "original_shape": img.shape,
            "gray_shape": gray.shape,
            "edges_detected": int(edges.sum() / 255),
        }
