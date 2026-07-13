#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any

from methods import METHODS
from methods.base import BenchmarkRecord, MethodMeta


DEFAULT_QUERIES: tuple[str, ...] = (
    "nature landscape",
    "cat portrait",
    "space galaxy",
    "architecture building",
)
DEFAULT_LIMIT: int = 5
REPORT_PATH: Path = Path("benchmark_report.json")


def run_benchmarks(
    methods: tuple[Any, ...],
    queries: tuple[str, ...],
    *,
    limit: int = DEFAULT_LIMIT,
) -> list[BenchmarkRecord]:
    records: list[BenchmarkRecord] = []
    total_runs = len(queries) * len(methods)

    print(f"\n▶ Запуск {len(methods)} методов × {len(queries)} запросов "
          f"= {total_runs} измерений (limit={limit})\n")

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


def _method_aggregate(
    records: list[BenchmarkRecord],
    meta: MethodMeta,
) -> dict[str, Any]:
    method_records = [r for r in records if r.meta == meta]
    successes = sum(1 for r in method_records if r.success)
    total_count = sum(r.results_count for r in method_records)
    times = [r.duration_sec * 1000 for r in method_records if r.success]

    return {
        "name": meta.name,
        "category": meta.category,
        "queries_tested": len(method_records),
        "success_rate": successes / len(method_records) if method_records else 0.0,
        "total_results": total_count,
        "avg_time_ms": mean(times) if times else float("inf"),
        "errors": [
            f"{r.query}: {r.error}"
            for r in method_records
            if not r.success and r.error
        ],
    }


def build_ranking(records: list[BenchmarkRecord]) -> list[dict[str, Any]]:
    metas = {r.meta for r in records}
    aggregates = [_method_aggregate(records, meta) for meta in metas]

    aggregates.sort(
        key=lambda item: (
            -item["success_rate"],
            item["avg_time_ms"],
            -item["total_results"],
        )
    )
    return aggregates


def print_query_table(records: list[BenchmarkRecord], query: str) -> None:
    query_records = [r for r in records if r.query == query]
    query_records.sort(key=lambda r: (not r.success, r.duration_sec))

    header = (
        f"{'#':<4} {'Метод':<30} {'Категория':<18} "
        f"{'Успех':<6} {'Рез.':<6} {'Время, мс':<12}"
    )
    separator = "-" * len(header)

    print(f"\n=== Запрос: \"{query}\" ===")
    print(header)
    print(separator)

    for idx, record in enumerate(query_records, start=1):
        success_mark = "Да" if record.success else "Нет"
        print(
            f"{idx:<4} {record.meta.name:<30} {record.meta.category:<18} "
            f"{success_mark:<6} {record.results_count:<6} "
            f"{record.duration_sec * 1000:>10.2f}"
        )


def print_summary(ranking: list[dict[str, Any]]) -> None:
    header = (
        f"{'#':<4} {'Метод':<30} {'Категория':<18} "
        f"{'Успех %':<8} {'Среднее мс':<12} {'Всего рез.':<12}"
    )
    separator = "-" * len(header)

    print("\n" + "=" * len(header))
    print("ИТОГОВЫЙ РЕЙТИНГ МЕТОДОВ")
    print("=" * len(header))
    print(header)
    print(separator)

    for idx, item in enumerate(ranking, start=1):
        success_pct = f"{item['success_rate'] * 100:.0f}%"
        avg_ms = f"{item['avg_time_ms']:.2f}" if item["avg_time_ms"] != float("inf") else "N/A"
        print(
            f"{idx:<4} {item['name']:<30} {item['category']:<18} "
            f"{success_pct:<8} {avg_ms:<12} {item['total_results']:<12}"
        )


def save_report(records: list[BenchmarkRecord], path: Path = REPORT_PATH) -> None:
    payload = {
        "summary": {
            "methods_tested": len({r.meta for r in records}),
            "queries_tested": len({r.query for r in records}),
            "total_runs": len(records),
        },
        "records": [asdict(record) for record in records],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n📄 Отчёт сохранён: {path.resolve()}")


def main() -> None:
    records = run_benchmarks(METHODS, DEFAULT_QUERIES, limit=DEFAULT_LIMIT)

    for query in DEFAULT_QUERIES:
        print_query_table(records, query)

    ranking = build_ranking(records)
    print_summary(ranking)
    save_report(records)


if __name__ == "__main__":
    main()
