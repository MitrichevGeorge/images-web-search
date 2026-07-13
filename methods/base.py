from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, ClassVar, final


@dataclass(frozen=True, slots=True)
class MethodMeta:
    name: str
    category: str
    description: str


@dataclass(frozen=True, slots=True)
class BenchmarkRecord:
    meta: MethodMeta
    query: str
    success: bool
    duration_sec: float
    results_count: int
    data: list[dict[str, Any]] = field(default_factory=list, repr=False)
    error: str | None = None


class BaseImageMethod(ABC):
    meta: ClassVar[MethodMeta]
    timeout: ClassVar[float] = 30.0

    @abstractmethod
    def search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        ...

    @final
    def benchmark(self, query: str, *, limit: int = 10) -> BenchmarkRecord:
        start = perf_counter()
        try:
            data = self.search(query, limit=limit)
            success = True
            error = None
        except Exception as exc:
            data = []
            success = False
            error = f"{type(exc).__name__}: {exc}"

        duration = perf_counter() - start
        return BenchmarkRecord(
            meta=self.meta,
            query=query,
            success=success,
            duration_sec=duration,
            results_count=len(data),
            data=data,
            error=error,
        )
