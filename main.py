#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Final, Iterable, NamedTuple, Sequence

from methods import METHODS
from methods.base import BenchmarkRecord, MethodMeta

DEFAULT_QUERIES: Final[tuple[str, ...]] = (
    "nature landscape",
    "cat portrait",
    "space galaxy",
    "architecture building",
)
DEFAULT_LIMIT: Final[int] = 10
REPORT_PATH: Final[Path] = Path("benchmark_report.json")

logger = logging.getLogger("BenchmarkSuite")


@dataclass(slots=True, frozen=True)
class MethodStats:
    meta: MethodMeta
    queries_tested: int
    success_rate: float
    total_results: int
    avg_time_ms: float
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.meta.name,
            "category": self.meta.category,
            "queries_tested": self.queries_tested,
            "success_rate": self.success_rate,
            "total_results": self.total_results,
            "avg_time_ms": self.avg_time_ms,
            "errors": self.errors,
        }


class ReportRenderer(NamedTuple):
    query_fmt: str = "{idx:<4} {name:<30} {category:<18} {success:<6} {count:<6} {time:>10.2f}"
    summary_fmt: str = "{idx:<4} {name:<30} {category:<18} {success:<8} {time:<12} {count:<12}"


def run_benchmarks(
    methods: Sequence[Any],
    queries: Sequence[str],
    *,
    limit: int = DEFAULT_LIMIT,
) -> list[BenchmarkRecord]:
    records: list[BenchmarkRecord] = []
    total_runs = len(queries) * len(methods)

    print(f"\n▶ Запуск {len(methods)} методов × {len(queries)} запросов = {total_runs} измерений (limit={limit})\n")

    for query_idx, query in enumerate(queries, start=1):
        print(f"[{query_idx}/{len(queries)}] Запрос: \"{query}\"")
        for method_idx, method in enumerate(methods, start=1):
            record = method.benchmark(query, limit=limit)
            records.append(record)
            
            status = "✓" if record.success else "✗"
            print(
                f"  {status} {method_idx:02d}. {record.meta.name:30s} "
                f"| count={record.results_count:3d} "
                f"| time={record.duration_sec * 1000:8.2f} ms"
            )
        print()

    return records


def calculate_rankings(records: Sequence[BenchmarkRecord]) -> list[MethodStats]:
    metas = {r.meta for r in records}
    rankings: list[MethodStats] = []

    for meta in metas:
        method_records = [r for r in records if r.meta == meta]
        if not method_records:
            continue

        successes = sum(1 for r in method_records if r.success)
        times = [r.duration_sec * 1000 for r in method_records if r.success]
        
        rankings.append(
            MethodStats(
                meta=meta,
                queries_tested=len(method_records),
                success_rate=successes / len(method_records),
                total_results=sum(r.results_count for r in method_records),
                avg_time_ms=mean(times) if times else float("inf"),
                errors=[f"{r.query}: {r.error}" for r in method_records if not r.success and r.error]
            )
        )

    rankings.sort(key=lambda item: (-item.success_rate, item.avg_time_ms, -item.total_results))
    return rankings


def print_query_table(records: Sequence[BenchmarkRecord], query: str) -> None:
    query_records = sorted(
        [r for r in records if r.query == query],
        key=lambda r: (not r.success, r.duration_sec)
    )

    header = f"{'#':<4} {'Метод':<30} {'Категория':<18} {'Успех':<6} {'Рез.':<6} {'Время, мс':<12}"
    print(f"\n=== Запрос: \"{query}\" ===\n{header}\n{'-' * len(header)}")

    renderer = ReportRenderer()
    for idx, r in enumerate(query_records, start=1):
        print(
            renderer.query_fmt.format(
                idx=idx,
                name=r.meta.name,
                category=r.meta.category,
                success="Да" if r.success else "Нет",
                count=r.results_count,
                time=r.duration_sec * 1000
            )
        )


def print_summary(ranking: Iterable[MethodStats]) -> None:
    header = f"{'#':<4} {'Метод':<30} {'Категория':<18} {'Успех %':<8} {'Среднее мс':<12} {'Всего рез.':<12}"
    border = "=" * len(header)
    
    print(f"\n{border}\nИТОГОВЫЙ РЕЙТИНГ МЕТОДОВ\n{border}\n{header}\n{'-' * len(header)}")

    renderer = ReportRenderer()
    for idx, item in enumerate(ranking, start=1):
        avg_ms = f"{item.avg_time_ms:.2f}" if item.avg_time_ms != float("inf") else "N/A"
        print(
            renderer.summary_fmt.format(
                idx=idx,
                name=item.meta.name,
                category=item.meta.category,
                success=f"{item.success_rate * 100:.0f}%",
                time=avg_ms,
                count=item.total_results
            )
        )


def save_report(records: Sequence[BenchmarkRecord], path: Path = REPORT_PATH) -> None:
    payload = {
        "summary": {
            "methods_tested": len({r.meta for r in records}),
            "queries_tested": len({r.query for r in records}),
            "total_runs": len(records),
        },
        "records": [asdict(record) for record in records],
    }
    
    try:
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), 
            encoding="utf-8"
        )
        print(f"\nОтчёт сохранён: {path.resolve()}")
    except IOError as e:
        logger.error("Failed writing tracking metadata matrix: %s", e)


def main() -> None:
    records = run_benchmarks(METHODS, DEFAULT_QUERIES, limit=DEFAULT_LIMIT)

    for query in DEFAULT_QUERIES:
        print_query_table(records, query)

    ranking = calculate_rankings(records)
    print_summary(ranking)
    save_report(records)


if __name__ == "__main__":
    main()