from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from doorman.engine import Doorman, Verdict

DATASET_RELATIVE_PATH = Path("benchmark") / "dataset.jsonl"


@dataclass(frozen=True)
class DatasetRow:
    text: str
    label: str  # "injection" | "benign"
    technique: str
    source: str = "curated"


def default_dataset_path() -> Path:
    repo_root_guess = Path(__file__).resolve().parents[2] / DATASET_RELATIVE_PATH
    if repo_root_guess.exists():
        return repo_root_guess
    return Path.cwd() / DATASET_RELATIVE_PATH


def load_dataset(path: Path) -> list[DatasetRow]:
    if not path.exists():
        raise FileNotFoundError(
            f"Benchmark dataset not found at {path}. Pass --dataset to point at it explicitly."
        )
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        rows.append(
            DatasetRow(
                text=obj["text"],
                label=obj["label"],
                technique=obj.get("technique", "n/a"),
                source=obj.get("source", "curated"),
            )
        )
    return rows


@dataclass(frozen=True)
class BenchmarkReport:
    total: int
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    f1: float
    accuracy: float
    per_technique: dict[str, tuple[int, int]]  # technique -> (caught, total)


def evaluate(rows: list[DatasetRow], engine: Doorman) -> BenchmarkReport:
    tp = fp = tn = fn = 0
    per_technique: dict[str, list[int]] = {}

    for row in rows:
        result = engine.scan(row.text)
        predicted_positive = result.verdict is not Verdict.ALLOW
        actual_positive = row.label == "injection"

        if actual_positive:
            counts = per_technique.setdefault(row.technique, [0, 0])
            counts[1] += 1
            if predicted_positive:
                counts[0] += 1

        if actual_positive and predicted_positive:
            tp += 1
        elif actual_positive and not predicted_positive:
            fn += 1
        elif not actual_positive and predicted_positive:
            fp += 1
        else:
            tn += 1

    total = len(rows)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / total if total else 0.0

    return BenchmarkReport(
        total=total,
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        precision=precision,
        recall=recall,
        f1=f1,
        accuracy=accuracy,
        per_technique={k: (v[0], v[1]) for k, v in sorted(per_technique.items())},
    )


def format_report(report: BenchmarkReport, *, title: str = "Doorman benchmark results") -> str:
    lines = [
        f"# {title}",
        "",
        f"- Examples: {report.total} ({report.tp + report.fn} injection, {report.tn + report.fp} benign)",
        f"- Precision: {report.precision:.1%}",
        f"- Recall: {report.recall:.1%}",
        f"- F1: {report.f1:.1%}",
        f"- Accuracy: {report.accuracy:.1%}",
        f"- Confusion: TP={report.tp} FP={report.fp} TN={report.tn} FN={report.fn}",
        "",
        "| Technique | Caught | Total | Detection rate |",
        "|---|---|---|---|",
    ]
    for technique, (caught, total) in report.per_technique.items():
        rate = caught / total if total else 0.0
        lines.append(f"| {technique} | {caught} | {total} | {rate:.1%} |")
    return "\n".join(lines)
